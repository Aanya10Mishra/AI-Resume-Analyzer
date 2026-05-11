"""
Fair-XAI Institutional Bias Explainability
Feature importance analysis for institutional bias drivers
Explains which features contribute most to institutional hiring bias

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstitutionalBiasExplainability:
    """
    Analyze which features drive institutional bias in hiring predictions
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize institutional bias explainability analyzer
        
        Args:
            df: DataFrame with institution_tier and other features
        """
        self.df = df.copy()
        self.analysis_results = {}
        
        # Add institution tier categorization if not present
        if 'institution_tier' not in self.df.columns:
            self._add_institution_tiers()
        
        logger.info("✅ Institutional Bias Explainability Analyzer initialized")
    
    def _add_institution_tiers(self):
        """Add institution tier column to dataframe"""
        tier_1_universities = {
            'harvard', 'yale', 'princeton', 'stanford', 'mit', 'columbia',
            'penn', 'caltech', 'northwestern', 'duke', 'chicago', 'cornell',
            'carnegie'
        }
        
        tier_2_universities = {
            'michigan', 'uc berkeley', 'berkeley', 'california', 'illinois',
            'texas', 'wisconsin', 'minnesota', 'georgia tech', 'georgia',
            'purdue', 'ohio state', 'penn state', 'nyu', 'boston', 'bu',
            'washington', 'usc'
        }
        
        def categorize(institution):
            if not institution or pd.isna(institution):
                return 'Tier-3'
            inst_lower = str(institution).lower().strip()
            for tier1 in tier_1_universities:
                if tier1 in inst_lower:
                    return 'Tier-1'
            for tier2 in tier_2_universities:
                if tier2 in inst_lower:
                    return 'Tier-2'
            return 'Tier-3'
        
        if 'institution' in self.df.columns:
            self.df['institution_tier'] = self.df['institution'].apply(categorize)
        elif 'education' in self.df.columns or 'education_enhanced' in self.df.columns:
            edu_col = 'education_enhanced' if 'education_enhanced' in self.df.columns else 'education'
            self.df['institution_tier'] = self.df[edu_col].apply(
                lambda x: categorize(str(x).split(' in ')[1] if ' in ' in str(x) else x)
            )
        else:
            self.df['institution_tier'] = 'Tier-3'
    
    # ============================================================================
    # FEATURE CORRELATION WITH INSTITUTION TIER
    # ============================================================================
    
    def analyze_feature_institution_correlation(self, 
                                               numeric_features: List[str] = None) -> Dict:
        """
        Analyze correlation between numeric features and institution tier
        
        Args:
            numeric_features: List of numeric columns to analyze
        
        Returns:
            Dictionary with correlation analysis
        """
        logger.info("\n🔍 Analyzing feature-institution correlations...")
        
        if numeric_features is None:
            # Auto-detect numeric columns
            numeric_features = self.df.select_dtypes(include=[np.number]).columns.tolist()
            # Remove institution_tier if present
            numeric_features = [col for col in numeric_features if 'institution' not in col.lower()]
        
        # Encode institution tier
        tier_mapping = {'Tier-1': 1, 'Tier-2': 2, 'Tier-3': 3}
        institution_numeric = self.df['institution_tier'].map(tier_mapping)
        
        correlations = {}
        p_values = {}
        
        for feature in numeric_features:
            if feature not in self.df.columns:
                continue
            
            # Skip missing values
            valid_mask = self.df[feature].notna() & institution_numeric.notna()
            if valid_mask.sum() < 10:  # Need at least 10 samples
                continue
            
            x = self.df.loc[valid_mask, feature]
            y = institution_numeric.loc[valid_mask]
            
            # Pearson correlation
            corr = x.corr(y)
            correlations[feature] = corr
            
            logger.info(f"  {feature}: correlation = {corr:.4f}")
        
        # Sort by absolute correlation
        sorted_corr = dict(sorted(correlations.items(), 
                                 key=lambda x: abs(x[1]), 
                                 reverse=True))
        
        return {
            'correlations': sorted_corr,
            'strongly_correlated': {k: v for k, v in sorted_corr.items() 
                                   if abs(v) > 0.3}
        }
    
    # ============================================================================
    # FEATURE IMPORTANCE BY GROUP
    # ============================================================================
    
    def compute_feature_importance_by_tier(self, 
                                          target_col: str = 'strength_score') -> Dict:
        """
        Compare how feature distributions differ across institution tiers
        
        Args:
            target_col: Column to analyze
        
        Returns:
            Dictionary with feature differences across tiers
        """
        logger.info("\n📊 Computing feature importance by institution tier...")
        
        importance = {}
        
        # Numeric features
        numeric_features = self.df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_features = [col for col in numeric_features 
                           if col not in ['institution_tier', 'strength_score', 'is_strong']]
        
        for feature in numeric_features:
            if feature not in self.df.columns or self.df[feature].isna().all():
                continue
            
            # Get feature values by tier
            tier1_vals = self.df[self.df['institution_tier'] == 'Tier-1'][feature].dropna()
            tier2_vals = self.df[self.df['institution_tier'] == 'Tier-2'][feature].dropna()
            tier3_vals = self.df[self.df['institution_tier'] == 'Tier-3'][feature].dropna()
            
            if len(tier1_vals) == 0 or len(tier2_vals) == 0 or len(tier3_vals) == 0:
                continue
            
            # Compute differences
            mean_diff_1_2 = abs(tier1_vals.mean() - tier2_vals.mean()) / (tier1_vals.std() + tier2_vals.std() + 1e-6)
            mean_diff_1_3 = abs(tier1_vals.mean() - tier3_vals.mean()) / (tier1_vals.std() + tier3_vals.std() + 1e-6)
            max_diff = max(mean_diff_1_2, mean_diff_1_3)
            
            importance[feature] = {
                'tier1_mean': round(tier1_vals.mean(), 4),
                'tier2_mean': round(tier2_vals.mean(), 4),
                'tier3_mean': round(tier3_vals.mean(), 4),
                'diff_1_vs_2': round(mean_diff_1_2, 4),
                'diff_1_vs_3': round(mean_diff_1_3, 4),
                'importance_score': round(max_diff, 4)
            }
        
        # Sort by importance
        sorted_importance = dict(sorted(importance.items(),
                                       key=lambda x: x[1]['importance_score'],
                                       reverse=True))
        
        return sorted_importance
    
    # ============================================================================
    # BIAS DRIVERS IDENTIFICATION
    # ============================================================================
    
    def identify_bias_drivers(self, threshold: float = 0.3) -> Dict:
        """
        Identify features that likely drive institutional bias
        
        Args:
            threshold: Correlation/difference threshold (0.3 = moderate)
        
        Returns:
            Dictionary with identified bias drivers
        """
        logger.info("\n🎯 Identifying institutional bias drivers...")
        
        # Get correlations
        corr_analysis = self.analyze_feature_institution_correlation()
        strong_corr = corr_analysis.get('strongly_correlated', {})
        
        # Get importance by tier
        importance_by_tier = self.compute_feature_importance_by_tier()
        high_diff_features = {k: v for k, v in importance_by_tier.items() 
                             if v['importance_score'] > threshold}
        
        drivers = {}
        for feature in strong_corr:
            if feature in high_diff_features:
                drivers[feature] = {
                    'correlation_with_tier': strong_corr[feature],
                    'mean_difference_score': high_diff_features[feature]['importance_score'],
                    'tier1_vs_tier2_diff': high_diff_features[feature]['diff_1_vs_2'],
                    'tier1_vs_tier3_diff': high_diff_features[feature]['diff_1_vs_3'],
                    'risk_level': 'HIGH' if high_diff_features[feature]['importance_score'] > 0.5 else 'MEDIUM'
                }
        
        logger.info(f"\n📍 Found {len(drivers)} potential bias drivers:")
        for feature, info in drivers.items():
            logger.info(f"   {feature}: {info['risk_level']} risk (score={info['mean_difference_score']:.3f})")
        
        return drivers
    
    # ============================================================================
    # PREDICTION VARIANCE BY INSTITUTION
    # ============================================================================
    
    def analyze_prediction_variance(self, target_col: str = 'strength_score') -> Dict:
        """
        Analyze how prediction variance differs across institution tiers
        
        Args:
            target_col: Prediction column
        
        Returns:
            Dictionary with variance analysis
        """
        logger.info("\n📈 Analyzing prediction variance by institution...")
        
        variance_analysis = {}
        
        for tier in ['Tier-1', 'Tier-2', 'Tier-3']:
            tier_data = self.df[self.df['institution_tier'] == tier][target_col]
            
            if len(tier_data) == 0:
                continue
            
            variance_analysis[tier] = {
                'mean': round(tier_data.mean(), 4),
                'std': round(tier_data.std(), 4),
                'variance': round(tier_data.var(), 4),
                'cv': round(tier_data.std() / (tier_data.mean() + 1e-6), 4),  # Coefficient of variation
                'count': len(tier_data),
                'percentile_25': round(tier_data.quantile(0.25), 4),
                'percentile_75': round(tier_data.quantile(0.75), 4),
                'iqr': round(tier_data.quantile(0.75) - tier_data.quantile(0.25), 4)
            }
        
        return variance_analysis
    
    # ============================================================================
    # INSTITUTIONAL ADVANTAGE ANALYSIS
    # ============================================================================
    
    def analyze_institutional_advantage(self, target_col: str = 'strength_score') -> Dict:
        """
        Measure the advantage/disadvantage of each institution tier
        
        Args:
            target_col: Prediction column
        
        Returns:
            Dictionary with advantage metrics
        """
        logger.info("\n🏆 Analyzing institutional advantage...")
        
        tier_stats = {}
        overall_mean = self.df[target_col].mean()
        
        for tier in ['Tier-1', 'Tier-2', 'Tier-3']:
            tier_data = self.df[self.df['institution_tier'] == tier][target_col]
            
            if len(tier_data) == 0:
                continue
            
            tier_mean = tier_data.mean()
            advantage = tier_mean - overall_mean
            
            tier_stats[tier] = {
                'mean_score': round(tier_mean, 4),
                'overall_mean': round(overall_mean, 4),
                'advantage': round(advantage, 4),
                'advantage_percent': round((advantage / overall_mean) * 100, 2),
                'percentile': round((self.df[target_col] <= tier_mean).mean() * 100, 2),
                'count': len(tier_data)
            }
        
        # Identify most/least advantaged
        advantages = {k: v['advantage'] for k, v in tier_stats.items()}
        most_advantaged = max(advantages.items(), key=lambda x: x[1])
        least_advantaged = min(advantages.items(), key=lambda x: x[1])
        
        logger.info(f"\n   Most Advantaged: {most_advantaged[0]} (+{most_advantaged[1]:.4f})")
        logger.info(f"   Least Advantaged: {least_advantaged[0]} ({least_advantaged[1]:.4f})")
        
        return {
            'tier_statistics': tier_stats,
            'most_advantaged': most_advantaged[0],
            'least_advantaged': least_advantaged[0],
            'advantage_gap': round(most_advantaged[1] - least_advantaged[1], 4)
        }
    
    # ============================================================================
    # COMPREHENSIVE EXPLAINABILITY REPORT
    # ============================================================================
    
    def generate_comprehensive_report(self) -> Dict:
        """
        Generate comprehensive explainability report for institutional bias
        
        Returns:
            Complete analysis dictionary
        """
        logger.info("\n" + "="*80)
        logger.info("INSTITUTIONAL BIAS EXPLAINABILITY ANALYSIS")
        logger.info("="*80)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'dataset_size': len(self.df),
            'institution_distribution': self.df['institution_tier'].value_counts().to_dict(),
            'feature_institution_correlation': self.analyze_feature_institution_correlation(),
            'feature_importance_by_tier': self.compute_feature_importance_by_tier(),
            'bias_drivers': self.identify_bias_drivers(),
            'prediction_variance': self.analyze_prediction_variance(),
            'institutional_advantage': self.analyze_institutional_advantage()
        }
        
        logger.info("\n✅ Comprehensive explainability analysis complete!")
        
        return report
    
    def save_report(self, report: Dict, output_file: str = 'fairxai_institutional_bias_explainability.json'):
        """
        Save explainability report to JSON
        
        Args:
            report: Report dictionary
            output_file: Output filename
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"\n💾 Explainability report saved to: {output_file}")
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")


if __name__ == "__main__":
    """
    Example usage:
    python fairxai_institutional_bias_explainability.py
    """
    
    # Load enhanced synthetic dataset
    with open('fairxai_synthetic_resumes_enhanced_institutional.json', 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data['resumes'])
    
    # Create analyzer
    explainer = InstitutionalBiasExplainability(df)
    
    # Generate comprehensive report
    report = explainer.generate_comprehensive_report()
    
    # Save report
    explainer.save_report(report)
    
    # Print summary
    print("\n" + "="*80)
    print("EXPLAINABILITY SUMMARY")
    print("="*80)
    print(json.dumps({
        'bias_drivers': report.get('bias_drivers', {}),
        'institutional_advantage': report.get('institutional_advantage', {})
    }, indent=2))
