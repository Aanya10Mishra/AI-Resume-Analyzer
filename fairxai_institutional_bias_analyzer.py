"""
Fair-XAI Institutional Bias Analyzer
Analyzes institutional bias in hiring decisions based on educational institution prestige/tier
Datasets: Synthetic, Kaggle, Combined

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"

Institutional Bias Definition:
  Disparities in hiring decisions based on the prestige/tier of the educational institution
  where the candidate obtained their degree.
  
  Categories:
  - Tier-1: Top-tier universities (Ivy League, Stanford, MIT, etc.)
  - Tier-2: Strong regional/national universities (State flagships, etc.)
  - Tier-3: Tier-3 universities (small colleges, less prestigious institutions)
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstitutionalBiasAnalyzer:
    """
    Analyze hiring bias based on educational institution prestige
    Supports synthetic, real-world, and combined datasets
    """
    
    # Institution categorization
    TIER_1_INSTITUTIONS = {
        'harvard', 'yale', 'princeton', 'stanford', 'mit', 'columbia',
        'penn', 'caltech', 'northwestern', 'duke', 'chicago', 'cornell',
        'stanford', 'carnegie'  # Carnegie Mellon
    }
    
    TIER_2_INSTITUTIONS = {
        'michigan', 'uc berkeley', 'berkeley', 'california', 'illinois',
        'texas', 'wisconsin', 'minnesota', 'georgia tech', 'georgia',
        'purdue', 'ohio state', 'penn state', 'nyu', 'boston', 'bu',
        'university of washington', 'university of southern california', 'usc'
    }
    
    # Fairness thresholds
    SPD_THRESHOLD = 0.10
    DI_LOWER_THRESHOLD = 0.80
    DI_UPPER_THRESHOLD = 1.25
    
    def __init__(self):
        """Initialize institutional bias analyzer"""
        self.data = None
        self.results = {}
        logger.info("✅ Institutional Bias Analyzer initialized")
    
    # ============================================================================
    # INSTITUTION CATEGORIZATION
    # ============================================================================
    
    def categorize_institution(self, institution_name: str) -> str:
        """
        Categorize institution into tier levels
        
        Args:
            institution_name: Name of the educational institution
        
        Returns:
            Tier category: 'Tier-1', 'Tier-2', or 'Tier-3'
        """
        if not institution_name or pd.isna(institution_name):
            return 'Tier-3'
        
        inst_lower = str(institution_name).lower().strip()
        
        # Check Tier-1
        for tier1_inst in self.TIER_1_INSTITUTIONS:
            if tier1_inst in inst_lower:
                return 'Tier-1'
        
        # Check Tier-2
        for tier2_inst in self.TIER_2_INSTITUTIONS:
            if tier2_inst in inst_lower:
                return 'Tier-2'
        
        # Default to Tier-3
        return 'Tier-3'
    
    def add_institution_tiers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add institution tier column to dataset
        
        Args:
            df: Input dataframe
        
        Returns:
            DataFrame with 'institution_tier' column
        """
        # Look for institution field first (enhanced datasets)
        if 'institution' in df.columns:
            logger.info(f"📚 Categorizing institutions from 'institution' column...")
            df['institution_name'] = df['institution']
        else:
            # Look for education field (various possible names)
            education_col = None
            for col in ['education', 'Education', 'education_enhanced', 'university', 'University']:
                if col in df.columns:
                    education_col = col
                    break
            
            if education_col is None:
                logger.warning("⚠️  No institution/education column found. Creating default tiers...")
                df['institution_tier'] = 'Tier-3'
                return df
            
            logger.info(f"📚 Categorizing institutions from '{education_col}' column...")
            
            # Extract institution name and categorize
            df['institution_name'] = df[education_col].apply(
                lambda x: str(x).split(' in ')[0] if pd.notna(x) else 'Unknown'
            )
        
        df['institution_tier'] = df['institution_name'].apply(
            self.categorize_institution
        )
        
        # Log distribution
        tier_dist = df['institution_tier'].value_counts()
        logger.info(f"   Tier-1 (Prestigious): {tier_dist.get('Tier-1', 0)}")
        logger.info(f"   Tier-2 (Strong Regional): {tier_dist.get('Tier-2', 0)}")
        logger.info(f"   Tier-3 (Other): {tier_dist.get('Tier-3', 0)}")
        
        return df
    
    # ============================================================================
    # STATISTICAL PARITY DIFFERENCE (SPD) FOR INSTITUTIONS
    # ============================================================================
    
    def compute_spd_by_institution(self, df: pd.DataFrame, 
                                   prediction_col: str = 'strength_score') -> List[Dict]:
        """
        Compute Statistical Parity Difference by institution tier
        
        SPD = P(Ŷ=1|unprivileged tier) - P(Ŷ=1|privileged tier)
        Fair if: |SPD| < 0.10
        
        Args:
            df: DataFrame with predictions and institution_tier
            prediction_col: Column with prediction scores
        
        Returns:
            List of SPD results by institution tier comparison
        """
        logger.info("\n🔍 Computing SPD for Institution Tiers...")
        
        spd_results = []
        
        # Compare Tier-1 (privileged) vs Tier-2 (unprivileged)
        tier1_group = df[df['institution_tier'] == 'Tier-1']
        tier2_group = df[df['institution_tier'] == 'Tier-2']
        tier3_group = df[df['institution_tier'] == 'Tier-3']
        
        # Comparisons
        comparisons = [
            ('Tier-1', 'Tier-2', tier1_group, tier2_group),
            ('Tier-1', 'Tier-3', tier1_group, tier3_group),
            ('Tier-2', 'Tier-3', tier2_group, tier3_group),
        ]
        
        for priv_tier, unpriv_tier, priv_group, unpriv_group in comparisons:
            if len(priv_group) == 0 or len(unpriv_group) == 0:
                logger.warning(f"   ⚠️  Skipping {priv_tier} vs {unpriv_tier}: insufficient data")
                continue
            
            # Compute mean scores
            p_priv = priv_group[prediction_col].mean()
            p_unpriv = unpriv_group[prediction_col].mean()
            spd = p_unpriv - p_priv
            
            # Fairness verdict
            is_fair = abs(spd) < self.SPD_THRESHOLD
            
            # Statistical significance (t-test)
            stat, p_value = stats.ttest_ind(
                unpriv_group[prediction_col].dropna(),
                priv_group[prediction_col].dropna()
            )
            
            # Effect size (Cohen's d)
            n_unpriv = len(unpriv_group)
            n_priv = len(priv_group)
            var_unpriv = unpriv_group[prediction_col].var()
            var_priv = priv_group[prediction_col].var()
            
            if var_unpriv > 0 and var_priv > 0:
                pooled_std = np.sqrt(
                    ((n_unpriv-1)*var_unpriv + (n_priv-1)*var_priv) / (n_unpriv + n_priv - 2)
                )
                effect_size = (p_unpriv - p_priv) / pooled_std if pooled_std > 0 else 0
            else:
                effect_size = 0
            
            result = {
                'metric': 'SPD',
                'bias_type': 'Institutional Bias',
                'privileged_group': priv_tier,
                'unprivileged_group': unpriv_tier,
                'mean_privileged': round(p_priv, 4),
                'mean_unprivileged': round(p_unpriv, 4),
                'spd_value': round(spd, 4),
                'abs_spd': round(abs(spd), 4),
                'threshold': self.SPD_THRESHOLD,
                'is_fair': bool(is_fair),
                'p_value': round(p_value, 6),
                'is_significant': p_value < 0.05,
                'effect_size': round(effect_size, 4),
                'interpretation': self._interpret_spd(spd),
                'privileged_count': len(priv_group),
                'unprivileged_count': len(unpriv_group)
            }
            
            spd_results.append(result)
            
            # Log result
            fairness_emoji = "✅ FAIR" if is_fair else "❌ BIASED"
            logger.info(f"   {fairness_emoji} | {priv_tier} vs {unpriv_tier}: SPD = {spd:.4f} (p={p_value:.4f})")
        
        return spd_results
    
    # ============================================================================
    # DISPARATE IMPACT (DI) FOR INSTITUTIONS
    # ============================================================================
    
    def compute_di_by_institution(self, df: pd.DataFrame,
                                  prediction_col: str = 'strength_score',
                                  threshold: float = 0.5) -> List[Dict]:
        """
        Compute Disparate Impact by institution tier
        
        DI = P(Ŷ=1|unprivileged tier) / P(Ŷ=1|privileged tier)
        Fair if: 0.80 ≤ DI ≤ 1.25 (80% rule)
        
        Args:
            df: DataFrame with predictions and institution_tier
            prediction_col: Column with prediction scores
            threshold: Score threshold for "positive" outcome (strong candidate)
        
        Returns:
            List of DI results by institution tier comparison
        """
        logger.info("\n📊 Computing Disparate Impact for Institution Tiers...")
        
        di_results = []
        
        # Binarize predictions
        df_binary = df.copy()
        df_binary['binary_prediction'] = (df_binary[prediction_col] >= threshold).astype(int)
        
        # Get groups
        tier1_group = df_binary[df_binary['institution_tier'] == 'Tier-1']
        tier2_group = df_binary[df_binary['institution_tier'] == 'Tier-2']
        tier3_group = df_binary[df_binary['institution_tier'] == 'Tier-3']
        
        # Comparisons
        comparisons = [
            ('Tier-1', 'Tier-2', tier1_group, tier2_group),
            ('Tier-1', 'Tier-3', tier1_group, tier3_group),
            ('Tier-2', 'Tier-3', tier2_group, tier3_group),
        ]
        
        for priv_tier, unpriv_tier, priv_group, unpriv_group in comparisons:
            if len(priv_group) == 0 or len(unpriv_group) == 0:
                logger.warning(f"   ⚠️  Skipping {priv_tier} vs {unpriv_tier}: insufficient data")
                continue
            
            # Compute selection rates
            p_priv = (priv_group['binary_prediction'] == 1).mean()
            p_unpriv = (unpriv_group['binary_prediction'] == 1).mean()
            
            # Compute DI
            if p_priv == 0:
                di = np.inf if p_unpriv > 0 else 1.0
            else:
                di = p_unpriv / p_priv
            
            # Fairness verdict
            is_fair = self.DI_LOWER_THRESHOLD <= di <= self.DI_UPPER_THRESHOLD
            
            # Confidence interval (Wilson score)
            ci_lower, ci_upper = self._wilson_confidence_interval(p_unpriv, len(unpriv_group))
            
            result = {
                'metric': 'DI',
                'bias_type': 'Institutional Bias',
                'privileged_group': priv_tier,
                'unprivileged_group': unpriv_tier,
                'selection_rate_privileged': round(p_priv, 4),
                'selection_rate_unprivileged': round(p_unpriv, 4),
                'di_value': round(di, 4) if di != np.inf else float('inf'),
                'lower_threshold': self.DI_LOWER_THRESHOLD,
                'upper_threshold': self.DI_UPPER_THRESHOLD,
                'is_fair': bool(is_fair),
                'ci_lower': round(ci_lower, 4),
                'ci_upper': round(ci_upper, 4),
                'interpretation': self._interpret_di(di),
                'privileged_count': len(priv_group),
                'unprivileged_count': len(unpriv_group),
                'threshold': threshold
            }
            
            di_results.append(result)
            
            # Log result
            fairness_emoji = "✅ FAIR" if is_fair else "❌ BIASED"
            logger.info(f"   {fairness_emoji} | {priv_tier} vs {unpriv_tier}: DI = {di:.4f}")
        
        return di_results
    
    # ============================================================================
    # INTERPRETATION METHODS
    # ============================================================================
    
    def _interpret_spd(self, spd: float) -> str:
        """Interpret SPD value"""
        if abs(spd) < self.SPD_THRESHOLD:
            return f"Fair (difference of {abs(spd)*100:.1f}%)"
        elif spd > 0:
            return f"Bias in favor of unprivileged group (+{spd*100:.1f}%)"
        else:
            return f"Bias in favor of privileged group ({spd*100:.1f}%)"
    
    def _interpret_di(self, di: float) -> str:
        """Interpret DI value"""
        if di == np.inf:
            return "Severe bias: privileged group has 0% selection"
        elif di < self.DI_LOWER_THRESHOLD:
            return f"Severe adverse impact (DI = {di:.2f}, below 80% rule)"
        elif self.DI_LOWER_THRESHOLD <= di <= self.DI_UPPER_THRESHOLD:
            return f"Fair (DI = {di:.2f}, within acceptable range)"
        else:
            return f"Potential reverse discrimination (DI = {di:.2f}, above 1.25)"
    
    def _wilson_confidence_interval(self, p: float, n: int, 
                                    confidence: float = 0.95) -> Tuple[float, float]:
        """
        Wilson score confidence interval
        
        Args:
            p: Proportion
            n: Sample size
            confidence: Confidence level (default 0.95)
        
        Returns:
            (lower_bound, upper_bound)
        """
        if n == 0:
            return 0.0, 1.0
        
        z = stats.norm.ppf((1 + confidence) / 2)
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2*n)) / denominator
        adjustment = z * np.sqrt(p * (1-p) / n + z**2 / (4*n**2)) / denominator
        
        return max(0, center - adjustment), min(1, center + adjustment)
    
    # ============================================================================
    # DISTRIBUTION ANALYSIS
    # ============================================================================
    
    def analyze_prediction_distribution(self, df: pd.DataFrame,
                                       prediction_col: str = 'strength_score') -> Dict:
        """
        Analyze prediction score distribution by institution tier
        
        Args:
            df: DataFrame with predictions and institution_tier
            prediction_col: Column with prediction scores
        
        Returns:
            Dictionary with distribution statistics
        """
        logger.info("\n📈 Analyzing Prediction Distribution by Institution Tier...")
        
        distribution = {}
        
        for tier in ['Tier-1', 'Tier-2', 'Tier-3']:
            tier_data = df[df['institution_tier'] == tier][prediction_col]
            
            if len(tier_data) == 0:
                continue
            
            distribution[tier] = {
                'count': len(tier_data),
                'mean': round(tier_data.mean(), 4),
                'median': round(tier_data.median(), 4),
                'std': round(tier_data.std(), 4),
                'min': round(tier_data.min(), 4),
                'max': round(tier_data.max(), 4),
                'q25': round(tier_data.quantile(0.25), 4),
                'q75': round(tier_data.quantile(0.75), 4),
            }
        
        return distribution
    
    # ============================================================================
    # COMPLETE ANALYSIS PIPELINE
    # ============================================================================
    
    def analyze_dataset(self, filepath: str, dataset_name: str = 'synthetic') -> Dict:
        """
        Complete institutional bias analysis pipeline
        
        Args:
            filepath: Path to data file (JSON or CSV)
            dataset_name: Name of dataset (synthetic, kaggle, combined)
        
        Returns:
            Comprehensive analysis results
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"INSTITUTIONAL BIAS ANALYSIS: {dataset_name.upper()}")
        logger.info(f"{'='*80}\n")
        
        # Load data
        logger.info(f"📂 Loading data from: {filepath}")
        try:
            if filepath.endswith('.json'):
                with open(filepath, 'r') as f:
                    data_dict = json.load(f)
                
                if 'resumes' in data_dict:
                    records = data_dict['resumes']
                else:
                    records = data_dict if isinstance(data_dict, list) else [data_dict]
                
                self.data = pd.DataFrame(records)
            else:
                self.data = pd.read_csv(filepath)
            
            logger.info(f"✅ Data loaded: {len(self.data)} records")
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            return {}
        
        # Add institution tiers
        self.data = self.add_institution_tiers(self.data)
        
        # Prepare prediction column
        if 'strength_score' not in self.data.columns:
            if 'is_strong' in self.data.columns:
                self.data['strength_score'] = self.data['is_strong'].astype(float)
            else:
                logger.warning("⚠️  No strength_score or is_strong column found")
                self.data['strength_score'] = np.random.random(len(self.data))
        
        # Analysis
        self.results[dataset_name] = {
            'dataset': dataset_name,
            'timestamp': datetime.now().isoformat(),
            'total_records': len(self.data),
            'institution_distribution': self.data['institution_tier'].value_counts().to_dict(),
            'spd_metrics': self.compute_spd_by_institution(self.data),
            'di_metrics': self.compute_di_by_institution(self.data),
            'distribution': self.analyze_prediction_distribution(self.data)
        }
        
        logger.info(f"\n✅ Analysis complete!")
        
        return self.results[dataset_name]
    
    def save_results(self, output_dir: str = '.', dataset_name: str = 'synthetic'):
        """
        Save analysis results to JSON file
        
        Args:
            output_dir: Output directory path
            dataset_name: Dataset name for filename
        """
        filename = f"{output_dir}/fairxai_institutional_bias_{dataset_name}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(self.results[dataset_name], f, indent=2, default=str)
            
            logger.info(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")


if __name__ == "__main__":
    """
    Example usage:
    python fairxai_institutional_bias_analyzer.py
    """
    
    analyzer = InstitutionalBiasAnalyzer()
    
    # Analyze enhanced synthetic dataset with institutional diversity
    synthetic_path = "fairxai_synthetic_resumes_enhanced_institutional.json"
    synthetic_results = analyzer.analyze_dataset(synthetic_path, 'synthetic')
    analyzer.save_results('.', 'synthetic')
    
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print(json.dumps(synthetic_results, indent=2, default=str))
