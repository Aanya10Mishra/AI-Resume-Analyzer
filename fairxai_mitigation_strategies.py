"""
Fair-XAI Mitigation Strategies
Techniques to mitigate bias and improve fairness in hiring predictions

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"

Mitigation Strategies:
1. Threshold Adjustment - Modify decision thresholds per group
2. Feature Reweighting - Reduce weight of biased features
3. Fairness Constraints - Add constraints during model training
4. Equalized Odds Post-processing - Adjust predictions for equal TPR/FPR
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Tuple, List, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiasGoldfingerAlgorithm:
    """Fairness-aware bias mitigation and correction"""
    
    pass

class ThresholdAdjustmentMitigation:
    """
    Mitigation via threshold adjustment
    Adjusts decision thresholds per group to achieve fairness
    
    Approach:
    1. Identify different optimal thresholds for each group
    2. Apply group-specific thresholds during prediction
    3. More positive outcomes for unprivileged group
    """
    
    def __init__(self, target_spd: float = 0.0, target_di: float = 1.0):
        """
        Initialize threshold adjustment
        
        Args:
            target_spd: Target Statistical Parity Difference (0 = perfect parity)
            target_di: Target Disparate Impact ratio (1.0 = perfect equality)
        """
        self.target_spd = target_spd
        self.target_di = target_di
        self.thresholds = {}
        logger.info(f"✅ Threshold adjustment initialized (target_SPD={target_spd})")
    
    def find_optimal_thresholds(self, df: pd.DataFrame, 
                               sensitive_attr: str, 
                               score_col: str = 'prediction_score',
                               privileged_val: str = 'Male',
                               unprivileged_val: str = 'Female') -> Dict[str, float]:
        """
        Find optimal thresholds for fairness
        
        Args:
            df: DataFrame with prediction scores and sensitive attribute
            sensitive_attr: Name of sensitive attribute column
            score_col: Column with continuous prediction scores
            privileged_val: Value of privileged group
            unprivileged_val: Value of unprivileged group
        
        Returns:
            Dictionary mapping group values to optimal thresholds
        """
        
        logger.info(f"\n🔄 Finding optimal thresholds for fairness...")
        logger.info(f"   Sensitive attribute: {sensitive_attr}")
        logger.info(f"   Target SPD: {self.target_spd}")
        
        # Get scores for each group
        priv_scores = df[df[sensitive_attr] == privileged_val][score_col].values
        unpriv_scores = df[df[sensitive_attr] == unprivileged_val][score_col].values
        
        best_thresholds = {privileged_val: 0.5, unprivileged_val: 0.5}
        best_spd_diff = float('inf')
        
        # Grid search for best thresholds
        for t_priv in np.linspace(0.0, 1.0, 21):  # 5% increments
            for t_unpriv in np.linspace(0.0, 1.0, 21):
                # Compute selection rates
                p_priv = (priv_scores >= t_priv).mean()
                p_unpriv = (unpriv_scores >= t_unpriv).mean()
                
                # Compute SPD
                spd = p_unpriv - p_priv
                
                # Check if closer to target
                if abs(spd - self.target_spd) < best_spd_diff:
                    best_spd_diff = abs(spd - self.target_spd)
                    best_thresholds[privileged_val] = t_priv
                    best_thresholds[unprivileged_val] = t_unpriv
        
        self.thresholds = best_thresholds
        
        logger.info(f"\n✅ Optimal thresholds found:")
        for group, threshold in best_thresholds.items():
            logger.info(f"   {group}: {threshold:.3f}")
        
        return best_thresholds
    
    def apply_thresholds(self, df: pd.DataFrame, 
                        sensitive_attr: str,
                        score_col: str = 'prediction_score') -> np.ndarray:
        """
        Apply group-specific thresholds to predictions
        
        Args:
            df: DataFrame with scores
            sensitive_attr: Sensitive attribute column
            score_col: Column with continuous scores
        
        Returns:
            Array of adjusted predictions (0 or 1)
        """
        
        if not self.thresholds:
            logger.error("Thresholds not computed. Call find_optimal_thresholds() first.")
            return None
        
        predictions = np.zeros(len(df))
        
        for group, threshold in self.thresholds.items():
            mask = df[sensitive_attr] == group
            predictions[mask] = (df[mask][score_col] >= threshold).astype(int)
        
        logger.info(f"✅ Thresholds applied to {len(df)} predictions")
        
        return predictions


class FeatureReweightingMitigation:
    """
    Reduce weight of biased features during prediction
    
    Approach:
    1. Identify biased features (high SHAP difference across groups)
    2. Reduce weight of these features in the model
    3. Retrain or adjust scoring function
    """
    
    def __init__(self, bias_threshold: float = 0.05):
        """
        Initialize feature reweighting
        
        Args:
            bias_threshold: SHAP difference threshold to identify biased features
        """
        self.bias_threshold = bias_threshold
        self.feature_weights = {}
        logger.info(f"✅ Feature reweighting initialized (threshold={bias_threshold})")
    
    def identify_biased_features(self, shap_by_group: Dict[str, np.ndarray],
                                feature_names: List[str]) -> Dict:
        """
        Identify features with high bias
        
        Args:
            shap_by_group: Dict mapping group names to SHAP value arrays
            feature_names: List of feature names
        
        Returns:
            Dictionary with identified biased features
        """
        
        logger.info(f"\n🔍 Identifying biased features...")
        
        biased_features = {}
        
        group_vals = list(shap_by_group.values())
        if len(group_vals) < 2:
            logger.warning("⚠️  Need at least 2 groups for bias analysis")
            return {}
        
        # Compute SHAP difference for each feature
        feature_bias = np.abs(group_vals[0].mean(axis=0) - group_vals[1].mean(axis=0))
        
        for i, (feat_name, bias_val) in enumerate(zip(feature_names, feature_bias)):
            if bias_val > self.bias_threshold:
                biased_features[feat_name] = {
                    'bias_score': float(bias_val),
                    'severity': self._classify_bias_severity(bias_val),
                    'recommended_weight_reduction': min(0.9, bias_val * 2)  # Reduce by 2x bias score
                }
                logger.info(f"  ❌ {feat_name}: bias={bias_val:.4f}")
        
        if not biased_features:
            logger.info(f"  ✅ No biased features detected (threshold={self.bias_threshold})")
        
        return biased_features
    
    def _classify_bias_severity(self, bias_score: float) -> str:
        """Classify bias severity"""
        if bias_score < 0.02:
            return "low"
        elif bias_score < 0.05:
            return "medium"
        elif bias_score < 0.10:
            return "high"
        else:
            return "critical"
    
    def compute_feature_weights(self, biased_features: Dict, 
                               total_features: int) -> np.ndarray:
        """
        Compute adjusted feature weights
        
        Args:
            biased_features: Dict of identified biased features
            total_features: Total number of features
        
        Returns:
            Array of feature weights [0, 1] where 1 = full weight
        """
        
        weights = np.ones(total_features)
        
        for feat_name, info in biased_features.items():
            # Assume feature name has pattern like "Feature_0"
            try:
                feat_idx = int(feat_name.split('_')[-1])
                reduction = info['recommended_weight_reduction']
                weights[feat_idx] = 1.0 - reduction
            except:
                pass
        
        logger.info(f"\n📊 Feature weights computed:")
        logger.info(f"   Mean weight: {weights.mean():.3f}")
        logger.info(f"   Min weight: {weights.min():.3f}")
        
        return weights


class EqualizedOddsMitigation:
    """
    Post-processing to achieve equalized odds
    
    Equalized odds: TPR (true positive rate) equal across groups
    
    Approach:
    1. Compute confusion matrices per group
    2. Find adjustment matrix that equalizes TPR and FPR
    3. Apply adjustment to posteriors
    """
    
    def __init__(self):
        """Initialize equalized odds mitigation"""
        self.adjustment_matrix = {}
        logger.info("✅ Equalized odds mitigation initialized")
    
    def compute_confusion_matrices(self, y_true: np.ndarray, 
                                   y_pred: np.ndarray,
                                   groups: np.ndarray) -> Dict:
        """
        Compute confusion matrices per group
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            groups: Group assignment for each sample
        
        Returns:
            Dictionary with TP, FP, TN, FN for each group
        """
        
        logger.info(f"\n📊 Computing confusion matrices...")
        
        confusion = {}
        unique_groups = np.unique(groups)
        
        for group in unique_groups:
            mask = groups == group
            y_t = y_true[mask]
            y_p = y_pred[mask]
            
            tp = ((y_t == 1) & (y_p == 1)).sum()
            fp = ((y_t == 0) & (y_p == 1)).sum()
            tn = ((y_t == 0) & (y_p == 0)).sum()
            fn = ((y_t == 1) & (y_p == 0)).sum()
            
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
            
            confusion[str(group)] = {
                'TP': int(tp),
                'FP': int(fp),
                'TN': int(tn),
                'FN': int(fn),
                'TPR': round(tpr, 4),
                'FPR': round(fpr, 4)
            }
            
            logger.info(f"  Group {group}: TPR={tpr:.3f}, FPR={fpr:.3f}")
        
        return confusion


class MitigationReport:
    """Generate comprehensive mitigation report"""
    
    @staticmethod
    def generate_report(before_metrics: Dict, after_metrics: Dict, 
                       mitigation_strategy: str) -> str:
        """
        Generate before/after fairness comparison report
        
        Args:
            before_metrics: Fairness metrics before mitigation
            after_metrics: Fairness metrics after mitigation
            mitigation_strategy: Name of mitigation technique used
        
        Returns:
            Formatted report string
        """
        
        report = "\n" + "="*80 + "\n"
        report += "FAIRNESS MITIGATION REPORT\n"
        report += "="*80 + "\n\n"
        
        report += f"Mitigation Strategy: {mitigation_strategy}\n\n"
        
        # Extract SPD metrics
        before_spd = before_metrics['spd_metrics'][0]['abs_spd']
        after_spd = after_metrics['spd_metrics'][0]['abs_spd']
        improvement = ((before_spd - after_spd) / before_spd * 100) if before_spd > 0 else 0
        
        report += "STATISTICAL PARITY DIFFERENCE (SPD)\n"
        report += "-"*80 + "\n"
        report += f"Before Mitigation: {before_spd:.4f}\n"
        report += f"After Mitigation:  {after_spd:.4f}\n"
        report += f"Improvement: {improvement:.2f}%\n\n"
        
        # Extract DI metrics
        if 'di_metrics' in before_metrics:
            before_di = before_metrics['di_metrics'][0]['di_value']
            after_di = after_metrics['di_metrics'][0]['di_value']
            
            report += "DISPARATE IMPACT (DI)\n"
            report += "-"*80 + "\n"
            report += f"Before Mitigation: {before_di:.4f}\n"
            report += f"After Mitigation:  {after_di:.4f}\n\n"
        
        # Overall assessment
        report += "ASSESSMENT\n"
        report += "-"*80 + "\n"
        
        if after_metrics['summary']['overall_system_fair']:
            report += "✅ System is now FAIR after mitigation\n"
        else:
            report += "⚠️  System still shows some fairness issues\n"
        
        report += f"Fair Attributes: {after_metrics['summary']['fair_attributes']}/{after_metrics['summary']['total_attributes_analyzed']}\n"
        report += "\n" + "="*80 + "\n"
        
        return report


# ============================================================================
# MAIN: DEMO MITIGATION WORKFLOW
# ============================================================================

if __name__ == "__main__":
    import pandas as pd
    
    logger.info("=" * 80)
    logger.info("BIAS MITIGATION DEMO")
    logger.info("=" * 80)
    
    # Create sample data
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'prediction_score': np.random.uniform(0, 1, n_samples),
        'prediction': np.random.randint(0, 2, n_samples)
    })
    
    logger.info(f"\n📊 Sample data: {len(df)} records")
    
    # Demo 1: Threshold Adjustment
    logger.info("\n" + "-"*80)
    logger.info("DEMO 1: THRESHOLD ADJUSTMENT")
    logger.info("-"*80)
    
    threshold_mitigator = ThresholdAdjustmentMitigation(target_spd=0.0)
    thresholds = threshold_mitigator.find_optimal_thresholds(
        df, 
        sensitive_attr='gender',
        privileged_val='Male',
        unprivileged_val='Female'
    )
    adjusted_preds = threshold_mitigator.apply_thresholds(df, 'gender')
    
    # Demo 2: Feature Reweighting
    logger.info("\n" + "-"*80)
    logger.info("DEMO 2: FEATURE REWEIGHTING")
    logger.info("-"*80)
    
    # Simulated SHAP values
    shap_by_group = {
        'Male': np.random.randn(500, 10),
        'Female': np.random.randn(500, 10) + 0.1  # Slight bias
    }
    feature_names = [f"Feature_{i}" for i in range(10)]
    
    reweight_mitigator = FeatureReweightingMitigation(bias_threshold=0.05)
    biased_features = reweight_mitigator.identify_biased_features(shap_by_group, feature_names)
    weights = reweight_mitigator.compute_feature_weights(biased_features, 10)
    
    logger.info("\n✅ Mitigation demos complete!")
