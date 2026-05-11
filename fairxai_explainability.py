"""
Fair-XAI Explainability Module
SHAP-based feature importance analysis for model interpretability
Explains which features drive hiring predictions

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
"""

import numpy as np
import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("⚠️  SHAP not installed. Install with: pip install shap")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExplainabilityAnalyzer:
    """
    Explainability analysis using SHAP values
    Explains model predictions and identifies bias drivers
    """
    
    def __init__(self, model, X_train: pd.DataFrame):
        """
        Initialize explainability analyzer
        
        Args:
            model: Trained prediction model with predict() or predict_proba() method
            X_train: Training data for SHAP background (can be a sample)
        """
        self.model = model
        self.X_train = X_train
        self.explainer = None
        self.shap_values = None
        
        if SHAP_AVAILABLE:
            logger.info("✅ SHAP module available")
        else:
            logger.warning("⚠️  SHAP not available - some analysis features disabled")
    
    # ============================================================================
    # SHAP EXPLAINER INITIALIZATION
    # ============================================================================
    
    def initialize_shap_explainer(self, explainer_type: str = 'auto'):
        """
        Initialize SHAP explainer
        
        Args:
            explainer_type: 'auto', 'kernel', 'tree', 'sampling'
        """
        if not SHAP_AVAILABLE:
            logger.error("SHAP not available")
            return
        
        logger.info(f"🔄 Initializing SHAP explainer (type: {explainer_type})...")
        
        try:
            if explainer_type == 'auto':
                # Auto-select based on model type
                self.explainer = shap.Explainer(self.model, self.X_train)
            elif explainer_type == 'kernel':
                self.explainer = shap.KernelExplainer(self.model.predict, self.X_train)
            elif explainer_type == 'tree' and hasattr(self.model, 'predict'):
                self.explainer = shap.TreeExplainer(self.model)
            else:
                self.explainer = shap.KernelExplainer(self.model.predict, self.X_train)
            
            logger.info(f"✅ SHAP explainer initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize explainer: {e}")
            self.explainer = None
    
    def compute_shap_values(self, X_test: pd.DataFrame, max_samples: int = None) -> np.ndarray:
        """
        Compute SHAP values for test data
        
        Args:
            X_test: Test data for explanation
            max_samples: Limit to speedup (useful for large datasets)
        
        Returns:
            SHAP values array
        """
        if self.explainer is None:
            logger.error("Explainer not initialized. Call initialize_shap_explainer() first.")
            return None
        
        # Limit sample size if needed
        if max_samples and len(X_test) > max_samples:
            X_sample = X_test.sample(n=max_samples, random_state=42)
            logger.info(f"⚠️  Computing SHAP values for {max_samples} samples (out of {len(X_test)})")
        else:
            X_sample = X_test
        
        try:
            logger.info(f"🔄 Computing SHAP values for {len(X_sample)} samples...")
            self.shap_values = self.explainer(X_sample)
            logger.info(f"✅ SHAP values computed successfully")
            
            return self.shap_values.values
        except Exception as e:
            logger.error(f"❌ Failed to compute SHAP values: {e}")
            return None
    
    # ============================================================================
    # FEATURE IMPORTANCE ANALYSIS
    # ============================================================================
    
    def get_feature_importance(self, shap_values: np.ndarray = None, 
                              feature_names: List[str] = None) -> Dict:
        """
        Compute feature importance from SHAP values
        
        Args:
            shap_values: SHAP values (use self.shap_values if None)
            feature_names: Feature names for reporting
        
        Returns:
            Dictionary with global feature importance scores
        """
        if shap_values is None:
            shap_values = self.shap_values
        
        if shap_values is None:
            logger.error("No SHAP values available")
            return {}
        
        # Handle shape: (samples, features) or (samples, features, classes)
        if len(shap_values.shape) == 3:  # Multi-class
            shap_values = np.abs(shap_values).mean(axis=2)
        else:
            shap_values = np.abs(shap_values)
        
        # Compute mean absolute SHAP value per feature
        feature_importance = shap_values.mean(axis=0)
        
        if feature_names is None:
            feature_names = [f"Feature_{i}" for i in range(len(feature_importance))]
        
        # Sort by importance
        sorted_indices = np.argsort(feature_importance)[::-1]
        
        importance_dict = {
            'features': [feature_names[i] for i in sorted_indices],
            'importance_scores': feature_importance[sorted_indices].tolist(),
            'relative_importance': (feature_importance[sorted_indices] / feature_importance.sum() * 100).tolist()
        }
        
        logger.info("\n📊 Top 10 Most Important Features")
        logger.info("-" * 60)
        logger.info(f"{'Rank':<5} {'Feature':<30} {'Importance':<15}")
        logger.info("-" * 60)
        
        for i in range(min(10, len(importance_dict['features']))):
            rank = i + 1
            feature = importance_dict['features'][i]
            importance = importance_dict['importance_scores'][i]
            rel_imp = importance_dict['relative_importance'][i]
            
            logger.info(f"{rank:<5} {feature:<30} {importance:.4f} ({rel_imp:.2f}%)")
        
        return importance_dict
    
    # ============================================================================
    # BIAS DETECTION VIA SHAP
    # ============================================================================
    
    def analyze_bias_by_attribute(self, X_test: pd.DataFrame, 
                                 sensitive_attribute: str,
                                 shap_values: np.ndarray = None) -> Dict:
        """
        Analyze bias in SHAP values across protected attributes
        
        Args:
            X_test: Test data with sensitive attributes
            sensitive_attribute: Column name of protected attribute (e.g., 'gender')
            shap_values: SHAP values (use self.shap_values if None)
        
        Returns:
            Dictionary with bias analysis results
        """
        if shap_values is None:
            shap_values = self.shap_values
        
        if shap_values is None:
            logger.error("No SHAP values available")
            return {}
        
        logger.info(f"\n🔍 Analyzing bias in {sensitive_attribute}...")
        logger.info("-" * 60)
        
        # Handle shape
        if len(shap_values.shape) == 3:
            shap_values = np.abs(shap_values).mean(axis=2)
        else:
            shap_values = np.abs(shap_values)
        
        analysis = {
            'attribute': sensitive_attribute,
            'groups': {},
            'feature_bias': {}
        }
        
        # Analyze each group
        unique_groups = X_test[sensitive_attribute].unique()
        
        for group in unique_groups:
            group_mask = X_test[sensitive_attribute] == group
            group_shap = shap_values[group_mask]
            
            analysis['groups'][str(group)] = {
                'count': int(group_mask.sum()),
                'mean_abs_shap': group_shap.mean(axis=0).tolist(),
                'median_abs_shap': np.median(group_shap, axis=0).tolist(),
                'std_abs_shap': group_shap.std(axis=0).tolist()
            }
            
            logger.info(f"Group: {group} (n={int(group_mask.sum())})")
        
        # Identify biased features (high difference across groups)
        if len(unique_groups) == 2:
            group_vals = list(analysis['groups'].values())
            feature_means_1 = np.array(group_vals[0]['mean_abs_shap'])
            feature_means_2 = np.array(group_vals[1]['mean_abs_shap'])
            
            feature_bias = np.abs(feature_means_1 - feature_means_2)
            
            analysis['feature_bias'] = {
                'feature_differences': feature_bias.tolist(),
                'max_bias_feature': int(np.argmax(feature_bias)),
                'max_bias_value': float(np.max(feature_bias)),
                'interpretation': self._interpret_feature_bias(feature_bias)
            }
        
        return analysis
    
    def _interpret_feature_bias(self, feature_bias: np.ndarray) -> str:
        """Interpret feature bias values"""
        max_bias = np.max(feature_bias)
        
        if max_bias < 0.01:
            return "✅ Minimal bias across groups"
        elif max_bias < 0.05:
            return "⚠️  Low bias across groups"
        elif max_bias < 0.10:
            return "❌ Moderate bias across groups"
        else:
            return "🚨 High bias across groups - requires mitigation"
    
    # ============================================================================
    # VISUALIZATION
    # ============================================================================
    
    def plot_shap_summary(self, max_display: int = 15, filename: str = None):
        """
        Plot SHAP summary plot (bar chart of feature importance)
        
        Args:
            max_display: Number of top features to display
            filename: Save plot to file if provided
        """
        if not SHAP_AVAILABLE or self.shap_values is None:
            logger.error("Cannot create plot: SHAP values not available")
            return
        
        try:
            plt.figure(figsize=(12, 6))
            shap.summary_plot(self.shap_values, self.X_train, plot_type="bar", 
                            max_display=max_display, show=False)
            
            if filename:
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                logger.info(f"✅ Plot saved to: {filename}")
            else:
                plt.show()
            
            plt.close()
        except Exception as e:
            logger.error(f"❌ Failed to create plot: {e}")
    
    def plot_feature_importance_comparison(self, importance_by_group: Dict, 
                                          filename: str = None):
        """
        Plot feature importance comparison across groups
        
        Args:
            importance_by_group: Dict mapping group names to importance arrays
            filename: Save plot to file if provided
        """
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            x = np.arange(len(list(importance_by_group.values())[0]))
            width = 0.8 / len(importance_by_group)
            
            for i, (group, importance) in enumerate(importance_by_group.items()):
                ax.bar(x + i * width, importance, width, label=group)
            
            ax.set_ylabel('Mean |SHAP value|')
            ax.set_title('Feature Importance Comparison Across Groups')
            ax.set_xticks(x + width * (len(importance_by_group) - 1) / 2)
            ax.set_xticklabels([f'F{i}' for i in range(len(x))], rotation=45)
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            
            if filename:
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                logger.info(f"✅ Plot saved to: {filename}")
            else:
                plt.show()
            
            plt.close()
        except Exception as e:
            logger.error(f"❌ Failed to create comparison plot: {e}")
    
    # ============================================================================
    # SAVE & LOAD
    # ============================================================================
    
    def save_analysis(self, analysis: Dict, filename: str):
        """Save analysis results to JSON"""
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"✅ Analysis saved to: {filename}")


# ============================================================================
# SIMPLE ALTERNATIVE: FEATURE IMPORTANCE WITHOUT SHAP
# ============================================================================

class PermutationImportanceAnalyzer:
    """
    Simplified feature importance using permutation importance
    Works without SHAP and with any model
    """
    
    def __init__(self, model, X_train: pd.DataFrame, y_train: np.ndarray, 
                 metric: str = 'accuracy'):
        """
        Initialize permutation importance analyzer
        
        Args:
            model: Trained model with predict() method
            X_train: Training features
            y_train: Training labels
            metric: 'accuracy', 'auc', 'f1', etc.
        """
        self.model = model
        self.X_train = X_train
        self.y_train = y_train
        self.metric = metric
    
    def compute_importance(self, n_repeats: int = 10) -> Dict:
        """
        Compute permutation importance for all features
        
        Args:
            n_repeats: Number of times to permute each feature
        
        Returns:
            Dictionary with importance scores
        """
        logger.info(f"🔄 Computing permutation importance ({n_repeats} repeats)...")
        
        baseline_score = self._compute_score()
        feature_importance = np.zeros(self.X_train.shape[1])
        
        for i in range(self.X_train.shape[1]):
            scores = []
            
            for _ in range(n_repeats):
                X_permuted = self.X_train.copy()
                X_permuted.iloc[:, i] = np.random.permutation(X_permuted.iloc[:, i])
                
                permuted_score = self._compute_score(X_permuted)
                scores.append(baseline_score - permuted_score)
            
            feature_importance[i] = np.mean(scores)
            logger.info(f"  Feature {i}: {feature_importance[i]:.4f}")
        
        # Sort by importance
        sorted_indices = np.argsort(feature_importance)[::-1]
        
        return {
            'features': self.X_train.columns.tolist(),
            'importance_scores': feature_importance[sorted_indices].tolist(),
            'relative_importance': (feature_importance[sorted_indices] / feature_importance.sum() * 100).tolist()
        }
    
    def _compute_score(self, X=None) -> float:
        """Compute model score"""
        if X is None:
            X = self.X_train
        
        predictions = self.model.predict(X)
        
        if self.metric == 'accuracy':
            return (predictions == self.y_train).mean()
        elif self.metric == 'auc':
            from sklearn.metrics import roc_auc_score
            return roc_auc_score(self.y_train, predictions)
        else:
            return (predictions == self.y_train).mean()


# ============================================================================
# MAIN: RUN EXPLAINABILITY ANALYSIS
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("EXPLAINABILITY MODULE - DEMO")
    logger.info("=" * 80)
    
    # Create dummy data for demonstration
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification
    
    X, y = make_classification(n_samples=200, n_features=10, n_informative=5,
                               n_redundant=2, random_state=42)
    X_df = pd.DataFrame(X, columns=[f'Feature_{i}' for i in range(X.shape[1])])
    
    # Train simple model
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X_df[:100], y[:100])
    
    logger.info("\n✅ Demo model trained")
    
    # Analyze with permutation importance
    analyzer = PermutationImportanceAnalyzer(model, X_df[:50], y[:50])
    importance = analyzer.compute_importance(n_repeats=5)
    
    logger.info("\n📊 Top Features:")
    for feat, imp in zip(importance['features'][:5], importance['importance_scores'][:5]):
        logger.info(f"  {feat}: {imp:.4f}")
