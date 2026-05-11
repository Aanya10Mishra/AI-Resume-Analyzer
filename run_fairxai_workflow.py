"""
FAIR-XAI EXECUTION SCRIPT
Ready-to-run workflow combining data loading + fairness auditing

DUAL-PURPOSE DATASET USAGE:
1. KAGGLE DATA (Real-World Validation)
   ├─ Purpose: Validate Resume Analyzer on real resumes
   ├─ Content: Actual resumes with education, skills, categories
   ├─ Usage: Extract features, evaluate realistic behavior
   └─ Fairness: Analyze actual prediction patterns

2. SYNTHETIC DATA (Controlled Fair-XAI Experiments)
   ├─ Purpose: Conduct controlled fairness experiments
   ├─ Content: 600 resumes with complete sensitive attributes (gender, experience)
   ├─ Usage: Compute SPD/DI, apply SHAP/explainability, test interventions
   └─ Fairness: Primary experimental dataset for bias analysis

WORKFLOW:
1. Load Kaggle CSV (real-world validation dataset)
2. Load Synthetic XLSX (controlled experimentation dataset)
3. Run fairness audit on SYNTHETIC for primary analysis
4. Run fairness audit on KAGGLE for validation
5. Compare results to demonstrate robustness
6. Generate comprehensive reports
"""

import sys
from pathlib import Path

# Add project directory to path
project_dir = Path.home() / "Documents" / "AI Resume Analyzer"
sys.path.insert(0, str(project_dir))

from fairxai_data_loader import FairXAIDataLoader, FairXAIDataExplorer
from fairxai_auditing_pipeline import FairXAIAuditingPipeline
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_complete_workflow():
    """
    Execute complete Fair-XAI workflow with your datasets
    """
    
    print("\n" + "="*100)
    print("FAIR-XAI COMPLETE WORKFLOW EXECUTION")
    print("="*100)
    
    # ========================================================================
    # PHASE 1: DATA LOADING & PREPARATION
    # ========================================================================
    
    print("\n" + "="*100)
    print("PHASE 1: DATA LOADING & PREPARATION")
    print("="*100)
    
    # Initialize loader
    loader = FairXAIDataLoader()
    explorer = FairXAIDataExplorer()
    
    # Load Kaggle data
    print("\n" + "-"*100)
    print("Loading Kaggle Dataset (Real Data)")
    print("-"*100)
    
    kaggle_df = loader.load_kaggle_data("preprocessed_resumes (1).csv")
    
    if kaggle_df is None:
        logger.error("[FAIL] Failed to load Kaggle data. Exiting.")
        return
    
    kaggle_exploration = explorer.explore_dataset(kaggle_df, "Kaggle Data")
    loader.save_processed_data(kaggle_df, 'kaggle', format='csv')
    
    # Load synthetic data
    print("\n" + "-"*100)
    print("Loading Synthetic Dataset (Controlled 600 Resumes)")
    print("-"*100)
    
    synthetic_df = loader.load_synthetic_data("Resume_Dataset_600_Balanced (1).xlsx")
    
    if synthetic_df is None:
        logger.error("[FAIL] Failed to load synthetic data. Exiting.")
        return
    
    synthetic_exploration = explorer.explore_dataset(synthetic_df, "Synthetic Data")
    loader.save_processed_data(synthetic_df, 'synthetic', format='csv')
    
    # Merge datasets
    print("\n" + "-"*100)
    print("Merging Datasets")
    print("-"*100)
    
    combined_df = loader.merge_datasets(kaggle_df, synthetic_df)
    loader.save_processed_data(combined_df, 'combined', format='csv')
    
    print("\n[OK] PHASE 1 COMPLETE: Data loaded and processed")
    
    # ========================================================================
    # PHASE 2: FAIRNESS AUDIT ON SYNTHETIC DATA (Primary Analysis)
    # ========================================================================
    
    print("\n" + "="*100)
    print("PHASE 2: FAIRNESS AUDIT ON SYNTHETIC DATA")
    print("="*100)
    print("\n[CHART] PURPOSE: Controlled Fair-XAI Experiments")
    print("   • Synthetic dataset has complete sensitive attributes (gender, experience)")
    print("   • Enables controlled fairness metrics (SPD, DI) computation")
    print("   • Apply explainability methods to identify bias drivers")
    print("   • Test fairness interventions in controlled environment")
    print("   • Results form PRIMARY basis for research paper")
    print("\n" + "="*100)
    
    pipeline_synthetic = FairXAIAuditingPipeline(
        project_name="AI Resume Analyzer - Synthetic Data Audit"
    )
    
    # Load synthetic data
    pipeline_synthetic.data = synthetic_df
    
    print("\n" + "-"*100)
    print("STEP 2: Computing Fairness Metrics (BEFORE Mitigation)")
    print("-"*100)
    
    fairness_synthetic_before = pipeline_synthetic.compute_fairness_metrics(
        attributes={
            'gender': ('Male', 'Female'),
            'experience_level': ('senior', 'entry')
        },
        prediction_col='prediction'
    )
    
    print("\n" + "-"*100)
    print("STEP 3: Feature Importance Analysis")
    print("-"*100)
    
    importance_synthetic = pipeline_synthetic.compute_feature_importance(method='permutation')
    
    print("\n" + "-"*100)
    print("STEP 4: Root Cause Analysis")
    print("-"*100)
    
    causes_synthetic = pipeline_synthetic.analyze_bias_causes('gender')
    
    print("\n" + "-"*100)
    print("STEP 5: Applying Bias Mitigation (Threshold Adjustment)")
    print("-"*100)
    
    mitigated_synthetic = pipeline_synthetic.apply_mitigation(
        mitigation_type='threshold_adjustment',
        sensitive_attr='gender',
        privileged_val='Male',
        unprivileged_val='Female'
    )
    
    print("\n" + "-"*100)
    print("STEP 6: Verifying Improvements (AFTER Mitigation)")
    print("-"*100)
    
    fairness_synthetic_after = pipeline_synthetic.verify_mitigation(
        mitigated_synthetic,
        attributes={
            'gender': ('Male', 'Female'),
            'experience_level': ('senior', 'entry')
        },
        prediction_col='prediction_mitigated'
    )
    
    print("\n" + "-"*100)
    print("STEP 7: Generating Comprehensive Report")
    print("-"*100)
    
    report_synthetic = pipeline_synthetic.generate_audit_report(
        'FAIRXAI_SYNTHETIC_AUDIT.txt'
    )
    
    pipeline_synthetic.save_audit_results('./fairxai_results_synthetic')
    
    print("\n[OK] PHASE 2 COMPLETE: Synthetic data audit finished")
    print("\n[CHART] Reports saved to: ./fairxai_results_synthetic/")
    
    # ========================================================================
    # PHASE 3: FAIRNESS AUDIT ON KAGGLE DATA (Validation)
    # ========================================================================
    
    print("\n" + "="*100)
    print("PHASE 3: FAIRNESS AUDIT ON KAGGLE DATA (Real-World Validation)")
    print("="*100)
    print("\n[INFO] PURPOSE: Real-World Model Validation")
    print("   • Kaggle dataset contains actual resumes (may have missing attributes)")
    print("   • Extract features: education, skills, experience, category")
    print("   • Evaluate realistic model behavior on real resumes")
    print("   • Validate that synthetic experiment patterns generalize")
    print("   • Demonstrate robustness and practical applicability")
    print("\n" + "="*100)
    
    pipeline_kaggle = FairXAIAuditingPipeline(
        project_name="AI Resume Analyzer - Kaggle Data Validation"
    )
    
    # Load Kaggle data
    pipeline_kaggle.data = kaggle_df
    
    print("\n" + "-"*100)
    print("Computing Fairness Metrics on Real Data")
    print("-"*100)
    
    # Analyze available attributes
    # Note: Kaggle may not have gender - adjust based on your data
    attributes_to_analyze = {}
    
    if 'gender' in kaggle_df.columns:
        attributes_to_analyze['gender'] = ('Male', 'Female')
        logger.info("[OK] Gender column found in Kaggle data")
    else:
        logger.warning("[WARN]  Gender column not found in Kaggle data")
    
    if 'experience_level' in kaggle_df.columns:
        attributes_to_analyze['experience_level'] = ('senior', 'entry')
        logger.info("[OK] Experience level column found in Kaggle data")
    
    if attributes_to_analyze:
        fairness_kaggle = pipeline_kaggle.compute_fairness_metrics(
            attributes=attributes_to_analyze,
            prediction_col='prediction'
        )
        
        importance_kaggle = pipeline_kaggle.compute_feature_importance()
        
        report_kaggle = pipeline_kaggle.generate_audit_report(
            'FAIRXAI_KAGGLE_AUDIT.txt'
        )
        
        pipeline_kaggle.save_audit_results('./fairxai_results_kaggle')
        
        print("\n[OK] PHASE 3 COMPLETE: Kaggle data audit finished")
        print("\n[CHART] Reports saved to: ./fairxai_results_kaggle/")
    else:
        logger.warning("[WARN]  No analyzable attributes in Kaggle data")
        print("\n[WARN] PHASE 3 SKIPPED: No matching attributes found")
    
    # ========================================================================
    # PHASE 4: COMPARATIVE ANALYSIS
    # ========================================================================
    
    print("\n" + "="*100)
    print("PHASE 4: COMPARATIVE ANALYSIS (Real vs Synthetic)")
    print("="*100)
    print("\n[CHECK] VALIDATION & ROBUSTNESS DEMONSTRATION")
    print("   • Compare fairness metrics: Synthetic (controlled) vs Kaggle (real)")
    print("   • Validate that bias patterns from synthetic generalize to real data")
    print("   • Demonstrate feature importance consistency across datasets")
    print("   • Prove mitigation strategies are robust and practical")
    print("   • Establish real-world applicability of research findings")
    print("\n" + "="*100)
    
    comparison = generate_comparison_report(
        pipeline_synthetic,
        pipeline_kaggle if attributes_to_analyze else None
    )
    
    # Save comparison
    with open('FAIRXAI_COMPARISON_REPORT.txt', 'w') as f:
        f.write(comparison)
    
    logger.info("\n[OK] Comparison report saved: FAIRXAI_COMPARISON_REPORT.txt")
    
    # ========================================================================
    # PHASE 5: SUMMARY
    # ========================================================================
    
    print("\n" + "="*100)
    print("[OK] COMPLETE WORKFLOW FINISHED")
    print("="*100)
    
    print("\n[FILES] OUTPUT FILES GENERATED:")
    print("\nSynthetic Data Analysis:")
    print("  ├─ fairxai_results_synthetic/fairxai_audit_fairness_before.json")
    print("  ├─ fairxai_results_synthetic/fairxai_audit_fairness_after.json")
    print("  ├─ fairxai_results_synthetic/fairxai_audit_explainability.json")
    print("  └─ FAIRXAI_SYNTHETIC_AUDIT.txt")
    
    if attributes_to_analyze:
        print("\nKaggle Data Analysis:")
        print("  ├─ fairxai_results_kaggle/fairxai_audit_fairness_before.json")
        print("  ├─ fairxai_results_kaggle/fairxai_audit_explainability.json")
        print("  └─ FAIRXAI_KAGGLE_AUDIT.txt")
    
    print("\nComparative Analysis:")
    print("  └─ FAIRXAI_COMPARISON_REPORT.txt")
    
    print("\nProcessed Data:")
    print("  ├─ fairxai_kaggle_processed.csv")
    print("  ├─ fairxai_synthetic_processed.csv")
    print("  └─ fairxai_combined_processed.csv")
    
    print("\n[CHART] NEXT STEPS FOR YOUR RESEARCH PAPER:")
    print("  1. Extract tables from JSON files (fairness metrics)")
    print("  2. Create figures (before/after comparison)")
    print("  3. Read FAIRXAI_SYNTHETIC_AUDIT.txt for main findings")
    print("  4. Compare with FAIRXAI_KAGGLE_AUDIT.txt for validation")
    print("  5. Use FAIRXAI_COMPARISON_REPORT.txt for real vs synthetic discussion")
    
    print("\n[TIP] NOTES:")
    print("  • Synthetic data: Complete audit with gender + experience analysis")
    print("  • Kaggle data: Real-world validation (gender may not be available)")
    print("  • All metrics exported as JSON for table creation")
    print("  • Reports are human-readable and can be included in appendix")
    
    print("\n" + "="*100)


def generate_comparison_report(pipeline_synthetic, pipeline_kaggle=None) -> str:
    """Generate comparison report between synthetic and real data"""
    
    report = "\n" + "="*100 + "\n"
    report += "FAIRNESS METRICS COMPARISON: SYNTHETIC vs KAGGLE\n"
    report += "="*100 + "\n"
    
    report += "\nPURPOSE:\n"
    report += "Validate that fairness findings from controlled synthetic dataset\n"
    report += "generalize to real-world Kaggle resume data.\n"
    
    report += "\n" + "-"*100 + "\n"
    report += "SYNTHETIC DATA RESULTS\n"
    report += "-"*100 + "\n"
    
    if pipeline_synthetic.fairness_results_before:
        spd_metrics = pipeline_synthetic.fairness_results_before['spd_metrics']
        di_metrics = pipeline_synthetic.fairness_results_before['di_metrics']
        
        report += f"\nBefore Mitigation:\n"
        for metric in spd_metrics:
            attr = metric['attribute']
            spd = metric['abs_spd']
            fair = "[OK]" if metric['is_fair'] else "[FAIL]"
            report += f"  {fair} {attr}: SPD = {spd:.4f}\n"
        
        for metric in di_metrics:
            attr = metric['attribute']
            di = metric['di_value']
            fair = "[OK]" if metric['is_fair'] else "[FAIL]"
            report += f"  {fair} {attr}: DI = {di:.4f}\n"
        
        if pipeline_synthetic.fairness_results_after:
            report += f"\nAfter Mitigation:\n"
            spd_metrics_after = pipeline_synthetic.fairness_results_after['spd_metrics']
            di_metrics_after = pipeline_synthetic.fairness_results_after['di_metrics']
            
            for metric in spd_metrics_after:
                attr = metric['attribute']
                spd = metric['abs_spd']
                fair = "[OK]" if metric['is_fair'] else "[FAIL]"
                report += f"  {fair} {attr}: SPD = {spd:.4f}\n"
    
    if pipeline_kaggle:
        report += "\n" + "-"*100 + "\n"
        report += "KAGGLE DATA RESULTS\n"
        report += "-"*100 + "\n"
        
        if pipeline_kaggle.fairness_results_before:
            spd_metrics = pipeline_kaggle.fairness_results_before['spd_metrics']
            
            report += f"\nBefore Mitigation:\n"
            for metric in spd_metrics:
                attr = metric['attribute']
                spd = metric['abs_spd']
                fair = "[OK]" if metric['is_fair'] else "[FAIL]"
                report += f"  {fair} {attr}: SPD = {spd:.4f}\n"
    else:
        report += "\n[WARN]  Kaggle data audit skipped (no matching attributes found)\n"
    
    report += "\n" + "-"*100 + "\n"
    report += "VALIDATION CONCLUSIONS\n"
    report += "-"*100 + "\n"
    
    report += "\n[CHECK] If synthetic and Kaggle metrics show similar patterns:\n"
    report += "  → Findings are VALID and generalize to real data\n"
    report += "  → Synthetic dataset can be used for fairness testing\n"
    report += "  → Mitigation strategies are robust\n"
    
    report += "\n[X] If metrics differ significantly:\n"
    report += "  → Investigate data distribution differences\n"
    report += "  → Adjust synthetic data generation\n"
    report += "  → Prioritize real data analysis\n"
    
    report += "\n" + "="*100 + "\n"
    
    return report


if __name__ == "__main__":
    
    try:
        run_complete_workflow()
        print("\n[OK] Workflow execution completed successfully!")
    except Exception as e:
        logger.error(f"[FAIL] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()

