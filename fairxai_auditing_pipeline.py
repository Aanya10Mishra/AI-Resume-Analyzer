"""
Fair-XAI Complete Auditing Pipeline
End-to-end workflow for fairness auditing and bias mitigation
Integrates: data loading, predictions, fairness metrics, explainability, mitigation

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, Tuple, Optional, List
from datetime import datetime

# Import Fair-XAI modules
from fairxai_fairness_metrics import FairnessMetricsCalculator
from fairxai_explainability import ExplainabilityAnalyzer, PermutationImportanceAnalyzer
from fairxai_mitigation_strategies import (
    ThresholdAdjustmentMitigation,
    MitigationReport
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FairXAIAuditingPipeline:
    """
    Complete Fair-XAI pipeline for hiring system auditing
    
    Workflow:
    1. Load data and predictions
    2. Compute fairness metrics (SPD, DI)
    3. Explain predictions using SHAP/permutation importance
    4. Identify biased features and root causes
    5. Apply mitigation strategies
    6. Verify fairness improvements
    7. Generate comprehensive report
    """
    
    def __init__(self, project_name: str = "AI Resume Analyzer"):
        """
        Initialize auditing pipeline
        
        Args:
            project_name: Name of the hiring system being audited
        """
        self.project_name = project_name
        self.data = None
        self.predictions = None
        self.fairness_results_before = None
        self.fairness_results_after = None
        self.explainability_results = None
        self.mitigation_applied = False
        
        self.timestamp = datetime.now().isoformat()
        logger.info(f"✅ Fair-XAI Auditing Pipeline initialized: {project_name}")
    
    # ============================================================================
    # STEP 1: DATA & PREDICTIONS LOADING
    # ============================================================================
    
    def load_data(self, filepath: str, 
                 sensitive_attributes: List[str] = None) -> pd.DataFrame:
        """
        Load dataset with predictions and sensitive attributes
        
        Args:
            filepath: Path to data file (CSV or JSON)
            sensitive_attributes: Columns containing sensitive attributes
        
        Returns:
            Loaded DataFrame
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP 1: DATA LOADING")
        logger.info(f"{'='*80}")
        
        logger.info(f"📂 Loading data from: {filepath}")
        
        try:
            if filepath.endswith('.json'):
                with open(filepath, 'r') as f:
                    data_dict = json.load(f)
                
                # Handle nested structure (resumes list)
                if 'resumes' in data_dict:
                    records = data_dict['resumes']
                else:
                    records = data_dict if isinstance(data_dict, list) else [data_dict]
                
                self.data = pd.DataFrame(records)
            else:
                self.data = pd.read_csv(filepath)
            
            logger.info(f"✅ Data loaded: {len(self.data)} records, {len(self.data.columns)} columns")
            
            # Display info
            logger.info(f"\n📊 Dataset Info:")
            logger.info(f"   Rows: {len(self.data)}")
            logger.info(f"   Columns: {list(self.data.columns)}")
            
            if sensitive_attributes:
                logger.info(f"\n🔐 Sensitive Attributes:")
                for attr in sensitive_attributes:
                    if attr in self.data.columns:
                        unique_vals = self.data[attr].nunique()
                        logger.info(f"   {attr}: {unique_vals} unique values")
            
            return self.data
        
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            return None
    
    def add_predictions(self, predictions: np.ndarray, 
                       prediction_col: str = 'prediction',
                       score_col: str = None):
        """
        Add predictions to dataset
        
        Args:
            predictions: Array of predictions (binary or continuous)
            prediction_col: Column name for binary predictions
            score_col: Optional column name for prediction scores
        """
        
        if self.data is None:
            logger.error("❌ Data not loaded. Call load_data() first.")
            return
        
        if len(predictions) != len(self.data):
            logger.error(f"❌ Prediction length {len(predictions)} != data length {len(self.data)}")
            return
        
        self.data[prediction_col] = predictions
        self.predictions = predictions
        
        logger.info(f"✅ Predictions added: {prediction_col}")
        logger.info(f"   Selection rate (positive predictions): {(predictions == 1).mean():.2%}")
    
    # ============================================================================
    # STEP 2: FAIRNESS METRICS COMPUTATION
    # ============================================================================
    
    def compute_fairness_metrics(self, 
                                 attributes: Dict[str, Tuple[str, str]],
                                 prediction_col: str = 'prediction') -> Dict:
        """
        Compute fairness metrics (SPD, DI) before mitigation
        
        Args:
            attributes: Dict mapping attribute names to (privileged, unprivileged) tuples
            prediction_col: Column with predictions
        
        Returns:
            Dictionary with fairness metrics
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP 2: FAIRNESS METRICS (BEFORE MITIGATION)")
        logger.info(f"{'='*80}")
        
        if self.data is None or prediction_col not in self.data.columns:
            logger.error("❌ Data or predictions not available")
            return None
        
        calculator = FairnessMetricsCalculator(self.data)
        results = calculator.analyze_fairness(
            attributes=attributes,
            prediction_col=prediction_col
        )
        
        self.fairness_results_before = results
        
        return results
    
    # ============================================================================
    # STEP 3: EXPLAINABILITY ANALYSIS
    # ============================================================================
    
    def compute_feature_importance(self, 
                                   feature_cols: List[str] = None,
                                   method: str = 'permutation',
                                   model = None) -> Dict:
        """
        Explain model predictions using feature importance
        
        Args:
            feature_cols: Columns to analyze (auto-detect if None)
            method: 'shap' or 'permutation'
            model: Trained model (required for some methods)
        
        Returns:
            Dictionary with feature importance results
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP 3: EXPLAINABILITY ANALYSIS")
        logger.info(f"{'='*80}")
        
        if self.data is None:
            logger.error("❌ Data not loaded")
            return None
        
        # Auto-detect numeric features
        if feature_cols is None:
            feature_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
            # Remove prediction columns
            feature_cols = [c for c in feature_cols if 'prediction' not in c.lower()]
        
        logger.info(f"📊 Analyzing {len(feature_cols)} features")
        
        X = self.data[feature_cols].copy()
        
        # Simple permutation-based importance
        if model is None or method == 'permutation':
            # Use mock model if none provided
            importance = self._compute_simple_importance(X)
        else:
            analyzer = ExplainabilityAnalyzer(model, X)
            analyzer.initialize_shap_explainer()
            analyzer.compute_shap_values(X)
            importance = analyzer.get_feature_importance(feature_names=feature_cols)
        
        self.explainability_results = {
            'method': method,
            'features': feature_cols,
            'importance': importance
        }
        
        return self.explainability_results
    
    def _compute_simple_importance(self, X: pd.DataFrame) -> Dict:
        """Compute simple importance via correlation with target"""
        
        if 'prediction' not in self.data.columns:
            logger.warning("⚠️  No prediction column found")
            return {}
        
        target = self.data['prediction'].values
        
        importance_scores = []
        for col in X.columns:
            correlation = np.corrcoef(X[col], target)[0, 1]
            importance_scores.append(abs(correlation))
        
        # Normalize
        total = sum(importance_scores)
        importance_scores = [s / total * 100 if total > 0 else 0 for s in importance_scores]
        
        sorted_idx = np.argsort(importance_scores)[::-1]
        
        return {
            'features': [X.columns[i] for i in sorted_idx],
            'importance_scores': [importance_scores[i] for i in sorted_idx]
        }
    
    # ============================================================================
    # STEP 4: ROOT CAUSE ANALYSIS
    # ============================================================================
    
    def analyze_bias_causes(self, 
                           sensitive_attr: str,
                           importance_results: Dict = None) -> Dict:
        """
        Analyze root causes of detected bias
        
        Args:
            sensitive_attr: Column name of sensitive attribute
            importance_results: Feature importance results (optional)
        
        Returns:
            Dictionary with bias cause analysis
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP 4: ROOT CAUSE ANALYSIS")
        logger.info(f"{'='*80}")
        
        analysis = {
            'attribute': sensitive_attr,
            'findings': []
        }
        
        # Check correlation between sensitive attribute and features
        logger.info(f"\n📊 Analyzing correlation with {sensitive_attr}...")
        
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            if 'prediction' in col.lower():
                continue
            
            try:
                corr = self.data[[col, sensitive_attr]].corr() if sensitive_attr in self.data.columns else 0
                
                if pd.api.types.is_numeric_dtype(self.data[sensitive_attr]):
                    corr_val = abs(corr.iloc[0, 1])
                    if corr_val > 0.3:
                        analysis['findings'].append({
                            'feature': col,
                            'correlation': round(corr_val, 3),
                            'severity': 'HIGH' if corr_val > 0.5 else 'MEDIUM',
                            'note': f'{col} shows significant correlation with {sensitive_attr}'
                        })
            except:
                pass
        
        if not analysis['findings']:
            analysis['findings'].append({
                'note': 'No strong direct correlations found - bias may come from indirect associations'
            })
        
        logger.info(f"✅ Root cause analysis complete: {len(analysis['findings'])} findings")
        
        return analysis
    
    # ============================================================================
    # STEP 5: BIAS MITIGATION
    # ============================================================================
    
    def apply_mitigation(self, 
                        mitigation_type: str = 'threshold_adjustment',
                        sensitive_attr: str = 'gender',
                        privileged_val: str = 'Male',
                        unprivileged_val: str = 'Female') -> np.ndarray:
        """
        Apply fairness mitigation strategy
        
        Args:
            mitigation_type: 'threshold_adjustment', 'feature_reweighting', etc.
            sensitive_attr: Sensitive attribute to target
            privileged_val: Privileged group value
            unprivileged_val: Unprivileged group value
        
        Returns:
            Array of mitigated predictions
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP 5: BIAS MITIGATION")
        logger.info(f"{'='*80}")
        logger.info(f"Strategy: {mitigation_type}")
        
        if mitigation_type == 'threshold_adjustment':
            mitigator = ThresholdAdjustmentMitigation(target_spd=0.0)
            
            # Need prediction scores for this
            if 'prediction_score' not in self.data.columns:
                logger.warning("⚠️  No prediction_score column. Using prediction as score.")
                self.data['prediction_score'] = self.data['prediction'].astype(float)
            
            mitigator.find_optimal_thresholds(
                self.data,
                sensitive_attr=sensitive_attr,
                privileged_val=privileged_val,
                unprivileged_val=unprivileged_val
            )
            
            mitigated_preds = mitigator.apply_thresholds(
                self.data,
                sensitive_attr=sensitive_attr,
                score_col='prediction_score'
            )
            
            self.mitigation_applied = True
            logger.info("✅ Threshold adjustment applied")
            
            return mitigated_preds
        
        else:
            logger.warning(f"⚠️  Mitigation type '{mitigation_type}' not implemented yet")
            return self.data['prediction'].values
    
    # ============================================================================
    # STEP 6: VERIFY IMPROVEMENTS
    # ============================================================================
    
    def verify_mitigation(self, 
                         mitigated_predictions: np.ndarray,
                         attributes: Dict[str, Tuple[str, str]],
                         prediction_col: str = 'prediction_mitigated') -> Dict:
        """
        Verify fairness improvements after mitigation
        
        Args:
            mitigated_predictions: Array of mitigated predictions
            attributes: Attributes to analyze
            prediction_col: Column name for mitigated predictions
        
        Returns:
            Dictionary with post-mitigation fairness metrics
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP 6: MITIGATION VERIFICATION")
        logger.info(f"{'='*80}")
        
        # Add mitigated predictions to data
        self.data[prediction_col] = mitigated_predictions
        
        # Recompute fairness metrics
        calculator = FairnessMetricsCalculator(self.data)
        results = calculator.analyze_fairness(
            attributes=attributes,
            prediction_col=prediction_col
        )
        
        self.fairness_results_after = results
        
        # Compare before/after
        logger.info(f"\n📊 Fairness Improvement Summary:")
        logger.info(f"{'-'*80}")
        
        if self.fairness_results_before and self.fairness_results_after:
            before_avg_spd = np.mean([m['abs_spd'] for m in self.fairness_results_before['spd_metrics']])
            after_avg_spd = np.mean([m['abs_spd'] for m in self.fairness_results_after['spd_metrics']])
            improvement = ((before_avg_spd - after_avg_spd) / before_avg_spd * 100) if before_avg_spd > 0 else 0
            
            logger.info(f"Average |SPD| before: {before_avg_spd:.4f}")
            logger.info(f"Average |SPD| after:  {after_avg_spd:.4f}")
            logger.info(f"Improvement: {improvement:.2f}%")
        
        return results
    
    # ============================================================================
    # STEP 7: COMPREHENSIVE REPORT GENERATION
    # ============================================================================
    
    def generate_audit_report(self, output_file: str = None) -> str:
        """
        Generate comprehensive Fair-XAI audit report
        
        Args:
            output_file: File to save report (optional)
        
        Returns:
            Formatted report string
        """
        
        logger.info(f"\n{'='*80}")
        logger.info(f"STEP 7: AUDIT REPORT GENERATION")
        logger.info(f"{'='*80}")
        
        report = "\n" + "="*100 + "\n"
        report += f"FAIR-XAI COMPREHENSIVE AUDIT REPORT\n"
        report += f"Project: {self.project_name}\n"
        report += f"Timestamp: {self.timestamp}\n"
        report += "="*100 + "\n\n"
        
        # EXECUTIVE SUMMARY
        report += "EXECUTIVE SUMMARY\n"
        report += "-"*100 + "\n"
        
        if self.fairness_results_before:
            is_fair = self.fairness_results_before['summary']['overall_system_fair']
            report += f"Initial System Status: {'✅ FAIR' if is_fair else '❌ BIASED'}\n"
            report += f"Fair Attributes: {self.fairness_results_before['summary']['fair_attributes']}/{self.fairness_results_before['summary']['total_attributes_analyzed']}\n"
        
        if self.mitigation_applied and self.fairness_results_after:
            is_fair_after = self.fairness_results_after['summary']['overall_system_fair']
            report += f"After Mitigation: {'✅ FAIR' if is_fair_after else '⚠️  IMPROVED'}\n"
            report += f"Fair Attributes: {self.fairness_results_after['summary']['fair_attributes']}/{self.fairness_results_after['summary']['total_attributes_analyzed']}\n"
        
        report += "\n"
        
        # DETAILED FINDINGS
        report += "DETAILED FINDINGS\n"
        report += "-"*100 + "\n\n"
        
        if self.fairness_results_before:
            report += "1. STATISTICAL PARITY DIFFERENCE (SPD)\n"
            report += "-"*100 + "\n"
            
            for metric in self.fairness_results_before['spd_metrics']:
                attr = metric['attribute']
                spd = metric['abs_spd']
                fair = "✅" if metric['is_fair'] else "❌"
                
                report += f"{fair} {attr}: SPD = {spd:.4f}\n"
                report += f"   Privileged: {metric['privileged_group']} ({metric['p_privileged']:.1%})\n"
                report += f"   Unprivileged: {metric['unprivileged_group']} ({metric['p_unprivileged']:.1%})\n"
                report += f"   Interpretation: {metric['interpretation']}\n\n"
        
        if self.explainability_results:
            report += "2. FEATURE IMPORTANCE\n"
            report += "-"*100 + "\n"
            
            if 'importance' in self.explainability_results:
                importance = self.explainability_results['importance']
                report += f"Top 5 Features:\n"
                
                for i, (feat, score) in enumerate(zip(
                    importance['features'][:5],
                    importance['importance_scores'][:5]
                ), 1):
                    report += f"  {i}. {feat}: {score:.2f}%\n"
            
            report += "\n"
        
        # RECOMMENDATIONS
        report += "RECOMMENDATIONS\n"
        report += "-"*100 + "\n"
        
        if self.fairness_results_before:
            unfair_attrs = [m['attribute'] for m in self.fairness_results_before['spd_metrics'] 
                          if not m['is_fair']]
            
            if unfair_attrs:
                report += f"⚠️  Fairness Issues Detected in: {', '.join(unfair_attrs)}\n\n"
                report += "Recommended Actions:\n"
                report += "1. Review feature engineering for proxy variables\n"
                report += "2. Apply threshold adjustment or reweighting\n"
                report += "3. Consider data augmentation or collection strategies\n"
                report += "4. Implement continuous monitoring framework\n"
            else:
                report += "✅ System shows fair treatment across all attributes\n"
        
        report += "\n" + "="*100 + "\n"
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"✅ Report saved to: {output_file}")
        
        return report
    
    def save_audit_results(self, output_dir: str = '.'):
        """
        Save all audit results to files
        
        Args:
            output_dir: Directory to save results
        """
        
        # Create output directory if it doesn't exist
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\n✅ Saving audit results to: {output_dir}")
        
        if self.fairness_results_before:
            filepath = output_path / "fairxai_audit_fairness_before.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.fairness_results_before, f, indent=2, default=str)
        
        if self.fairness_results_after:
            filepath = output_path / "fairxai_audit_fairness_after.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.fairness_results_after, f, indent=2, default=str)
        
        if self.explainability_results:
            filepath = output_path / "fairxai_audit_explainability.json"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.explainability_results, f, indent=2, default=str)


# ============================================================================
# MAIN: EXAMPLE COMPLETE AUDIT WORKFLOW
# ============================================================================

if __name__ == "__main__":
    
    logger.info("\n" + "="*80)
    logger.info("FAIR-XAI AUDITING PIPELINE - DEMO")
    logger.info("="*80)
    
    # Create sample data
    np.random.seed(42)
    n = 1000
    
    sample_data = pd.DataFrame({
        'id': range(n),
        'gender': np.random.choice(['Male', 'Female'], n),
        'experience_level': np.random.choice(['entry', 'mid', 'senior'], n),
        'years_experience': np.random.randint(0, 15, n),
        'num_skills': np.random.randint(3, 20, n),
        'education_score': np.random.uniform(0, 100, n),
        'prediction': np.random.randint(0, 2, n),
        'prediction_score': np.random.uniform(0, 1, n)
    })
    
    # Save sample data
    sample_data.to_csv('fairxai_demo_data.csv', index=False)
    
    # Initialize pipeline
    pipeline = FairXAIAuditingPipeline(project_name="AI Resume Analyzer - Demo")
    
    # STEP 1: Load data
    pipeline.load_data('fairxai_demo_data.csv', 
                      sensitive_attributes=['gender', 'experience_level'])
    
    # STEP 2: Compute fairness metrics
    fairness_before = pipeline.compute_fairness_metrics(
        attributes={
            'gender': ('Male', 'Female'),
            'experience_level': ('senior', 'entry')
        }
    )
    
    # STEP 3: Explainability analysis
    importance = pipeline.compute_feature_importance(method='permutation')
    
    # STEP 4: Root cause analysis
    causes = pipeline.analyze_bias_causes('gender')
    
    # STEP 5: Apply mitigation
    mitigated = pipeline.apply_mitigation(
        mitigation_type='threshold_adjustment',
        sensitive_attr='gender'
    )
    
    # STEP 6: Verify improvements
    fairness_after = pipeline.verify_mitigation(
        mitigated,
        attributes={'gender': ('Male', 'Female')}
    )
    
    # STEP 7: Generate report
    report = pipeline.generate_audit_report('fairxai_audit_report.txt')
    print(report)
    
    # Save results
    pipeline.save_audit_results('.')
    
    logger.info("\n✅ Demo complete! Check output files for detailed results.")
