"""
Fair-XAI Fairness Metrics Computation
Calculates Statistical Parity Difference (SPD) and Disparate Impact (DI)
for gender and experience groups

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"

Key Metrics:
  SPD (Statistical Parity Difference) = P(Ŷ=1|unprivileged) - P(Ŷ=1|privileged)
    Fair if: |SPD| < 0.1 (10% threshold)
  
  DI (Disparate Impact) = P(Ŷ=1|unprivileged) / P(Ŷ=1|privileged)
    Fair if: 0.8 ≤ DI ≤ 1.0 (80% rule)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import logging
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FairnessMetricsCalculator:
    """
    Compute fairness metrics for AI hiring systems
    Supports analysis by gender, experience, and other protected attributes
    """
    
    # Fairness thresholds
    SPD_THRESHOLD = 0.10  # 10% difference is fair
    DI_LOWER_THRESHOLD = 0.80  # 80% rule
    DI_UPPER_THRESHOLD = 1.25  # Upper bound for DI
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with predictions dataframe
        
        Args:
            df: DataFrame with columns:
                - 'prediction' or 'label': Binary predictions (0/1) or continuous scores
                - 'gender': Protected attribute (Male/Female)
                - 'years_experience' or 'experience_level': Experience attribute
                - (optional) other sensitive attributes
        """
        self.df = df.copy()
        self.results = {}
        
        logger.info(f"✅ Fairness metrics calculator initialized")
        logger.info(f"   Dataset size: {len(df)} records")
    
    # ============================================================================
    # STATISTICAL PARITY DIFFERENCE (SPD)
    # ============================================================================
    
    def compute_spd(self, attribute: str, privileged_value: str, 
                    unprivileged_value: str, prediction_col: str = 'prediction') -> Dict:
        """
        Compute Statistical Parity Difference
        
        SPD = P(Ŷ=1|unprivileged) - P(Ŷ=1|privileged)
        Fair if: |SPD| < 0.10
        
        Args:
            attribute: Column name for protected attribute (e.g., 'gender')
            privileged_value: Value of privileged group (e.g., 'Male')
            unprivileged_value: Value of unprivileged group (e.g., 'Female')
            prediction_col: Column with predictions/scores
        
        Returns:
            Dictionary with SPD, fairness verdict, and statistical significance
        """
        
        # Get groups
        priv_group = self.df[self.df[attribute] == privileged_value]
        unpriv_group = self.df[self.df[attribute] == unprivileged_value]
        
        # Handle both binary and continuous predictions
        if self.df[prediction_col].dtype in ['int64', 'int32']:
            # Binary: compute selection rate
            p_priv = (priv_group[prediction_col] == 1).mean()
            p_unpriv = (unpriv_group[prediction_col] == 1).mean()
        else:
            # Continuous: compute mean score
            p_priv = priv_group[prediction_col].mean()
            p_unpriv = unpriv_group[prediction_col].mean()
        
        spd = p_unpriv - p_priv
        
        # Fairness verdict
        is_fair = abs(spd) < self.SPD_THRESHOLD
        
        # Statistical significance test (chi-square for binary, t-test for continuous)
        if self.df[prediction_col].dtype in ['int64', 'int32']:
            # Chi-square test for independence
            contingency = pd.crosstab(
                index=self.df[attribute],
                columns=self.df[prediction_col]
            )
            stat, p_value, dof, expected = stats.chi2_contingency(contingency)
        else:
            # Two-sample t-test
            stat, p_value = stats.ttest_ind(
                unpriv_group[prediction_col].dropna(),
                priv_group[prediction_col].dropna()
            )
        
        # Effect size (Cohen's d for continuous, Cramér's V for categorical)
        if self.df[prediction_col].dtype in ['int64', 'int32']:
            # Cramér's V
            n = len(self.df)
            effect_size = np.sqrt(stat / n)
        else:
            # Cohen's d
            n_unpriv = len(unpriv_group)
            n_priv = len(priv_group)
            var_unpriv = unpriv_group[prediction_col].var()
            var_priv = priv_group[prediction_col].var()
            pooled_std = np.sqrt(((n_unpriv-1)*var_unpriv + (n_priv-1)*var_priv) / (n_unpriv + n_priv - 2))
            effect_size = (p_unpriv - p_priv) / pooled_std if pooled_std > 0 else 0
        
        result = {
            'metric': 'SPD',
            'attribute': attribute,
            'privileged_group': privileged_value,
            'unprivileged_group': unprivileged_value,
            'p_privileged': round(p_priv, 4),
            'p_unprivileged': round(p_unpriv, 4),
            'spd_value': round(spd, 4),
            'abs_spd': round(abs(spd), 4),
            'threshold': self.SPD_THRESHOLD,
            'is_fair': is_fair,
            'p_value': round(p_value, 6),
            'is_significant': p_value < 0.05,
            'effect_size': round(effect_size, 4),
            'interpretation': self._interpret_spd(spd, abs(spd) < self.SPD_THRESHOLD),
            'privileged_count': len(priv_group),
            'unprivileged_count': len(unpriv_group)
        }
        
        return result
    
    # ============================================================================
    # DISPARATE IMPACT (DI)
    # ============================================================================
    
    def compute_di(self, attribute: str, privileged_value: str,
                   unprivileged_value: str, prediction_col: str = 'prediction') -> Dict:
        """
        Compute Disparate Impact
        
        DI = P(Ŷ=1|unprivileged) / P(Ŷ=1|privileged)
        Fair if: 0.80 ≤ DI ≤ 1.25 (conservative use DI ≤ 1.0)
        
        Args:
            attribute: Column name for protected attribute
            privileged_value: Value of privileged group
            unprivileged_value: Value of unprivileged group
            prediction_col: Column with predictions/scores
        
        Returns:
            Dictionary with DI, fairness verdict, and confidence interval
        """
        
        # Get groups
        priv_group = self.df[self.df[attribute] == privileged_value]
        unpriv_group = self.df[self.df[attribute] == unprivileged_value]
        
        # Compute selection rates
        if self.df[prediction_col].dtype in ['int64', 'int32']:
            p_priv = (priv_group[prediction_col] == 1).mean()
            p_unpriv = (unpriv_group[prediction_col] == 1).mean()
        else:
            p_priv = priv_group[prediction_col].mean()
            p_unpriv = unpriv_group[prediction_col].mean()
        
        # Avoid division by zero
        if p_priv == 0:
            di = np.inf if p_unpriv > 0 else 1.0
            logger.warning(f"⚠️  Warning: {privileged_value} group has 0% selection rate")
        else:
            di = p_unpriv / p_priv
        
        # Fairness verdict (80% rule: DI >= 0.8)
        is_fair = self.DI_LOWER_THRESHOLD <= di <= self.DI_UPPER_THRESHOLD
        
        # Confidence interval using Wilson score interval
        ci_lower, ci_upper = self._wilson_confidence_interval(p_unpriv, len(unpriv_group))
        
        result = {
            'metric': 'DI',
            'attribute': attribute,
            'privileged_group': privileged_value,
            'unprivileged_group': unprivileged_value,
            'p_privileged': round(p_priv, 4),
            'p_unprivileged': round(p_unpriv, 4),
            'di_value': round(di, 4) if di != np.inf else np.inf,
            'lower_threshold': self.DI_LOWER_THRESHOLD,
            'upper_threshold': self.DI_UPPER_THRESHOLD,
            'is_fair': is_fair,
            'ci_lower': round(ci_lower / p_priv if p_priv > 0 else 0, 4),
            'ci_upper': round(ci_upper / p_priv if p_priv > 0 else 0, 4),
            'interpretation': self._interpret_di(di),
            'privileged_count': len(priv_group),
            'unprivileged_count': len(unpriv_group)
        }
        
        return result
    
    # ============================================================================
    # COMPREHENSIVE FAIRNESS ANALYSIS
    # ============================================================================
    
    def analyze_fairness(self, attributes: Dict[str, Tuple[str, str]], 
                        prediction_col: str = 'prediction') -> Dict:
        """
        Comprehensive fairness analysis across multiple attributes
        
        Args:
            attributes: Dictionary mapping attribute names to (privileged, unprivileged) tuples
                Example: {
                    'gender': ('Male', 'Female'),
                    'experience_level': ('senior', 'entry')
                }
            prediction_col: Column with predictions
        
        Returns:
            Dictionary with all fairness metrics and summaries
        """
        
        logger.info("\n" + "="*80)
        logger.info("COMPREHENSIVE FAIRNESS ANALYSIS")
        logger.info("="*80)
        
        results = {
            'spd_metrics': [],
            'di_metrics': [],
            'overall_fairness': True,
            'summary': {}
        }
        
        for attribute, (priv, unpriv) in attributes.items():
            logger.info(f"\n📊 Analyzing attribute: {attribute}")
            logger.info(f"   Privileged: {priv}, Unprivileged: {unpriv}")
            
            # Compute SPD
            spd_result = self.compute_spd(attribute, priv, unpriv, prediction_col)
            results['spd_metrics'].append(spd_result)
            
            # Compute DI
            di_result = self.compute_di(attribute, priv, unpriv, prediction_col)
            results['di_metrics'].append(di_result)
            
            # Update overall fairness
            results['overall_fairness'] &= (spd_result['is_fair'] and di_result['is_fair'])
            
            # Log results
            logger.info(f"\n   SPD: {spd_result['abs_spd']} (Fair: {spd_result['is_fair']})")
            logger.info(f"   DI:  {spd_result['di_value'] if 'di_value' in spd_result else di_result['di_value']} (Fair: {di_result['is_fair']})")
            logger.info(f"   p-value: {spd_result['p_value']} (Significant: {spd_result['is_significant']})")
        
        # Compute summary statistics
        results['summary'] = {
            'total_attributes_analyzed': len(attributes),
            'fair_attributes': sum(1 for m in results['spd_metrics'] if m['is_fair']),
            'overall_system_fair': results['overall_fairness'],
            'avg_abs_spd': round(np.mean([m['abs_spd'] for m in results['spd_metrics']]), 4),
            'avg_di': round(np.mean([m['di_value'] for m in results['di_metrics'] if m['di_value'] != np.inf]), 4)
        }
        
        logger.info("\n" + "-"*80)
        logger.info("SUMMARY")
        logger.info("-"*80)
        logger.info(f"Overall System Fair: {results['overall_fairness']}")
        logger.info(f"Fair Attributes: {results['summary']['fair_attributes']}/{results['summary']['total_attributes_analyzed']}")
        logger.info(f"Average |SPD|: {results['summary']['avg_abs_spd']}")
        logger.info(f"Average DI: {results['summary']['avg_di']}")
        
        return results
    
    # ============================================================================
    # UTILITY FUNCTIONS
    # ============================================================================
    
    def _interpret_spd(self, spd: float, is_fair: bool) -> str:
        """Interpret SPD value"""
        if is_fair:
            return f"Fair (difference of {abs(spd):.1%})"
        elif spd > 0:
            return f"Bias against {spd:.1%} privileged group"
        else:
            return f"Bias against {abs(spd):.1%} unprivileged group"
    
    def _interpret_di(self, di: float) -> str:
        """Interpret DI value"""
        if di == np.inf:
            return "Undefined (privileged group has 0% selection)"
        elif di >= 0.8 and di <= 1.25:
            return f"Fair (DI = {di:.2f})"
        elif di < 0.8:
            return f"Adverse impact against unprivileged (DI = {di:.2f})"
        else:
            return f"Adverse impact against privileged (DI = {di:.2f})"
    
    def _wilson_confidence_interval(self, p: float, n: int, confidence: float = 0.95) -> Tuple[float, float]:
        """
        Compute Wilson score confidence interval
        More accurate for proportions, especially with small samples
        """
        z = stats.norm.ppf(1 - (1 - confidence) / 2)
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2*n)) / denominator
        adjustment = z * np.sqrt((p * (1-p) + z**2 / (4*n)) / n) / denominator
        
        return (center - adjustment, center + adjustment)
    
    # ============================================================================
    # SAVE RESULTS
    # ============================================================================
    
    def save_results(self, results: Dict, filename: str):
        """Save fairness analysis results to JSON"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✅ Results saved to: {filename}")
    
    def generate_fairness_report(self, results: Dict) -> str:
        """Generate human-readable fairness report"""
        
        report = "\n" + "="*80 + "\n"
        report += "FAIRNESS AUDIT REPORT\n"
        report += "="*80 + "\n\n"
        
        # Summary
        report += "EXECUTIVE SUMMARY\n"
        report += "-"*80 + "\n"
        summary = results['summary']
        report += f"Overall System Fair: {'✅ YES' if summary['overall_system_fair'] else '❌ NO'}\n"
        report += f"Fair Attributes: {summary['fair_attributes']}/{summary['total_attributes_analyzed']}\n"
        report += f"Average |SPD|: {summary['avg_abs_spd']:.4f}\n"
        report += f"Average DI: {summary['avg_di']:.4f}\n\n"
        
        # SPD Metrics
        report += "STATISTICAL PARITY DIFFERENCE (SPD) METRICS\n"
        report += "-"*80 + "\n"
        report += f"{'Attribute':<20} {'SPD':<10} {'Fair':<10} {'p-value':<10}\n"
        report += "-"*80 + "\n"
        
        for metric in results['spd_metrics']:
            fair_str = "✅" if metric['is_fair'] else "❌"
            report += f"{metric['attribute']:<20} {metric['abs_spd']:<10.4f} {fair_str:<10} {metric['p_value']:<10.6f}\n"
        
        report += "\n"
        
        # DI Metrics
        report += "DISPARATE IMPACT (DI) METRICS\n"
        report += "-"*80 + "\n"
        report += f"{'Attribute':<20} {'DI':<10} {'Fair':<10}\n"
        report += "-"*80 + "\n"
        
        for metric in results['di_metrics']:
            fair_str = "✅" if metric['is_fair'] else "❌"
            di_val = f"{metric['di_value']:.4f}" if metric['di_value'] != np.inf else "INF"
            report += f"{metric['attribute']:<20} {di_val:<10} {fair_str:<10}\n"
        
        report += "\n"
        
        # Recommendations
        report += "RECOMMENDATIONS\n"
        report += "-"*80 + "\n"
        
        unfair_attrs = [m['attribute'] for m in results['spd_metrics'] if not m['is_fair']]
        if unfair_attrs:
            report += f"⚠️  Unfair attributes detected: {', '.join(unfair_attrs)}\n"
            report += "Recommendations:\n"
            report += "1. Investigate bias sources in feature engineering\n"
            report += "2. Apply fairness constraints during model training\n"
            report += "3. Use reweighting or threshold adjustment techniques\n"
        else:
            report += "✅ System shows fair treatment across all analyzed attributes.\n"
        
        report += "\n" + "="*80 + "\n"
        
        return report


# ============================================================================
# HELPER: CREATE DATAFRAME FROM SYNTHETIC DATA
# ============================================================================

def load_and_prepare_data(synthetic_data_file: str) -> pd.DataFrame:
    """Load synthetic data and create prediction dataframe"""
    
    with open(synthetic_data_file, 'r') as f:
        data = json.load(f)
    
    resumes = data['resumes']
    
    # Create dataframe with predictions (for demo, using random predictions)
    # In real scenario, these would come from your model
    df = pd.DataFrame([
        {
            'id': r['id'],
            'name': r['name'],
            'gender': r['gender'],
            'years_experience': r['years_experience'],
            'experience_level': r['experience_level'],
            'prediction': np.random.randint(0, 2),  # Random for demo
            'prediction_score': np.random.uniform(0, 1)  # Random for demo
        }
        for r in resumes
    ])
    
    logger.info(f"✅ Loaded {len(df)} resumes from {synthetic_data_file}")
    
    return df


# ============================================================================
# MAIN: RUN FAIRNESS ANALYSIS
# ============================================================================

if __name__ == "__main__":
    # Load synthetic dataset
    df = load_and_prepare_data('fairxai_synthetic_resumes_600.json')
    
    # Initialize fairness calculator
    calculator = FairnessMetricsCalculator(df)
    
    # Define attributes to analyze
    attributes_to_analyze = {
        'gender': ('Male', 'Female'),
        'experience_level': ('senior', 'entry')
    }
    
    # Run comprehensive analysis
    results = calculator.analyze_fairness(
        attributes=attributes_to_analyze,
        prediction_col='prediction'
    )
    
    # Save results
    calculator.save_results(results, 'fairxai_fairness_results.json')
    
    # Generate report
    report = calculator.generate_fairness_report(results)
    print(report)
    
    # Save report
    with open('fairxai_fairness_report.txt', 'w') as f:
        f.write(report)
    
    logger.info("✅ Analysis complete! Check fairxai_fairness_results.json for detailed metrics.")
