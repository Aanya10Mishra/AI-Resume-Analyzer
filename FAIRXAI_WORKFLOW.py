"""
COMPLETE FAIR-XAI WORKFLOW WITH YOUR DATASETS
═══════════════════════════════════════════════

Your Data:
1. Kaggle: preprocessed_resumes(1).csv (Real-world data)
2. Synthetic: Resume_Dataset_600_Balanced(1).xlsx (600 balanced resumes)

This script shows the complete end-to-end workflow.
"""

# ============================================================================
# WORKFLOW: Load Data → Audit → Compare Results
# ============================================================================

"""
QUICK START (Copy & Paste)
══════════════════════════════════════════════════════════════════════════════

Step 1: Load your datasets
───────────────────────────

from fairxai_data_loader import FairXAIDataLoader

loader = FairXAIDataLoader()

# Load Kaggle (real data)
kaggle_df = loader.load_kaggle_data("preprocessed_resumes (1).csv")

# Load Synthetic (600 balanced resumes)
synthetic_df = loader.load_synthetic_data("Resume_Dataset_600_Balanced (1).xlsx")

# Merge for comparison
combined_df = loader.merge_datasets(kaggle_df, synthetic_df)


Step 2: Run fairness audit on SYNTHETIC data (recommended for gender analysis)
──────────────────────────────────────────────────────────────────────────────

from fairxai_auditing_pipeline import FairXAIAuditingPipeline

# Initialize pipeline
pipeline = FairXAIAuditingPipeline(project_name="AI Resume Analyzer - Synthetic")

# Load processed synthetic data
pipeline.data = synthetic_df

# Run 7-step audit
fairness_before = pipeline.compute_fairness_metrics({
    'gender': ('Male', 'Female'),
    'experience_level': ('senior', 'entry')
})

importance = pipeline.compute_feature_importance()
causes = pipeline.analyze_bias_causes('gender')
mitigated = pipeline.apply_mitigation('threshold_adjustment', 'gender')
fairness_after = pipeline.verify_mitigation(mitigated, {'gender': ('Male', 'Female')})

report = pipeline.generate_audit_report('SYNTHETIC_AUDIT.txt')
pipeline.save_audit_results('./fairxai_results_synthetic')


Step 3: Run fairness audit on KAGGLE data (real-world validation)
─────────────────────────────────────────────────────────────────

pipeline_kaggle = FairXAIAuditingPipeline(project_name="AI Resume Analyzer - Kaggle")
pipeline_kaggle.data = kaggle_df

# Note: Kaggle may not have gender data - analyze other attributes
fairness_before_kg = pipeline_kaggle.compute_fairness_metrics({
    'experience_level': ('senior', 'entry')
    # 'gender': ('Male', 'Female') # Uncomment if gender exists
})

report_kg = pipeline_kaggle.generate_audit_report('KAGGLE_AUDIT.txt')
pipeline_kaggle.save_audit_results('./fairxai_results_kaggle')


Step 4: Compare results (Real vs Synthetic)
────────────────────────────────────────────

import json

# Load results
with open('./fairxai_results_synthetic/fairxai_audit_fairness_before.json') as f:
    synthetic_metrics = json.load(f)

with open('./fairxai_results_kaggle/fairxai_audit_fairness_before.json') as f:
    kaggle_metrics = json.load(f)

# Compare fairness gaps
print("SYNTHETIC DATA FAIRNESS:")
print(json.dumps(synthetic_metrics, indent=2))

print("\\nKAGGLE DATA FAIRNESS:")
print(json.dumps(kaggle_metrics, indent=2))

print("\\nCOMPARISON:")
print("✓ Do both show similar patterns?")
print("✓ Is synthetic data more balanced?")
print("✓ Do interventions generalize to real data?")


═══════════════════════════════════════════════════════════════════════════════
"""

# ============================================================================
# DETAILED WORKFLOW WITH EXPLANATIONS
# ============================================================================

DETAILED_WORKFLOW = """

DETAILED STEP-BY-STEP WORKFLOW
═══════════════════════════════════════════════════════════════════════════════

📁 STEP 1: DATA LOADING & PREPARATION
──────────────────────────────────────

1.1 Load Kaggle Data (Real-World)
─────────────────────────────────

from fairxai_data_loader import FairXAIDataLoader, FairXAIDataExplorer

loader = FairXAIDataLoader(
    downloads_dir="C:/Users/Manvi/Downloads",
    project_dir="C:/Users/Manvi/Documents/AI Resume Analyzer"
)

# Load CSV file
kaggle_df = loader.load_kaggle_data("preprocessed_resumes (1).csv")

# Explore structure
explorer = FairXAIDataExplorer()
exploration = explorer.explore_dataset(kaggle_df, "Kaggle Data")

# Save processed version
loader.save_processed_data(kaggle_df, 'kaggle', format='csv')

Output:
├─ Console: Data shape, column info, distribution
├─ File: fairxai_kaggle_processed.csv
└─ Memory: kaggle_df DataFrame ready for analysis


1.2 Load Synthetic Data (Controlled)
────────────────────────────────────

# Load XLSX file
synthetic_df = loader.load_synthetic_data("Resume_Dataset_600_Balanced (1).xlsx")

# Explore
explorer.explore_dataset(synthetic_df, "Synthetic Data")

# Save
loader.save_processed_data(synthetic_df, 'synthetic', format='csv')

Output:
├─ Console: 600 records with balanced gender + experience
├─ File: fairxai_synthetic_processed.csv
└─ Memory: synthetic_df DataFrame


1.3 Understand Data Structure
─────────────────────────────

Kaggle columns typically include:
├─ ID / Index
├─ Category (job role)
├─ Clean_resume (preprocessed text)
├─ Skills
├─ Education
├─ Experience
└─ (Gender may not be present - use synthetic for gender fairness)

Synthetic columns:
├─ ID
├─ Gender ✅ (Male/Female) - AVAILABLE
├─ Experience_Level ✅ (entry/mid/senior) - AVAILABLE
├─ Years_Experience
├─ Skills / Skill_Count
├─ Job_Title
└─ Resume_Text


═════════════════════════════════════════════════════════════════════════════

⚖️ STEP 2: FAIRNESS AUDIT ON SYNTHETIC DATA
─────────────────────────────────────────────

Why Synthetic First?
- ✅ Has gender labels (Kaggle may not)
- ✅ Balanced groups (easy to detect bias)
- ✅ Reproducible & controlled
- ✅ Good for testing interventions


2.1 Initialize Pipeline
───────────────────────

from fairxai_auditing_pipeline import FairXAIAuditingPipeline

pipeline = FairXAIAuditingPipeline(
    project_name="AI Resume Analyzer - Synthetic Fairness Audit"
)

# Assign processed data
pipeline.data = synthetic_df

# Or load if saved:
# pipeline.load_data('fairxai_synthetic_processed.csv')


2.2 STEP 1: Load Data (Already done above)
──────────────────────────────────────────

pipeline.data = synthetic_df  # Already loaded


2.3 STEP 2: Compute Fairness Metrics BEFORE Mitigation
───────────────────────────────────────────────────────

fairness_before = pipeline.compute_fairness_metrics(
    attributes={
        'gender': ('Male', 'Female'),
        'experience_level': ('senior', 'entry')
    },
    prediction_col='prediction'
)

Output saved to memory + printed:
├─ SPD for gender: [value] - Fair? [YES/NO]
├─ SPD for experience: [value] - Fair? [YES/NO]
├─ DI metrics for both attributes
├─ Statistical significance (p-values)
└─ JSON: fairness_results_before

Expected for unmitigated bias:
└─ Both SPD and DI may show bias (|SPD| > 0.10, DI < 0.80)


2.4 STEP 3: Feature Importance Analysis
────────────────────────────────────────

importance = pipeline.compute_feature_importance(method='permutation')

Output:
├─ All features ranked by importance
├─ Top feature: Most drives predictions
├─ Which features are biased? (high difference across gender groups)
└─ Interpretation: e.g., "years_experience drives bias"


2.5 STEP 4: Root Cause Analysis
────────────────────────────────

causes = pipeline.analyze_bias_causes('gender')

Output:
├─ Features correlated with gender
├─ Likely bias drivers identified
└─ Recommendations for intervention


2.6 STEP 5: Apply Mitigation Strategy
──────────────────────────────────────

# Apply threshold adjustment (easiest, most interpretable)
mitigated_predictions = pipeline.apply_mitigation(
    mitigation_type='threshold_adjustment',
    sensitive_attr='gender',
    privileged_val='Male',
    unprivileged_val='Female'
)

Output:
├─ New predictions with adjusted thresholds
├─ Female group gets lower threshold (easier to shortlist)
├─ Male group gets higher threshold
└─ Result: More balanced selection rates


2.7 STEP 6: Verify Improvements AFTER Mitigation
──────────────────────────────────────────────────

fairness_after = pipeline.verify_mitigation(
    mitigated_predictions,
    attributes={
        'gender': ('Male', 'Female'),
        'experience_level': ('senior', 'entry')
    },
    prediction_col='prediction_mitigated'
)

Output:
├─ SPD after: Should be closer to 0
├─ DI after: Should be closer to 1.0
├─ Improvement: % reduction in bias
├─ Accuracy impact: % change
└─ Expected: 50%+ bias reduction with <5% accuracy loss


2.8 STEP 7: Generate Comprehensive Report
──────────────────────────────────────────

report = pipeline.generate_audit_report('SYNTHETIC_FAIRNESS_AUDIT.txt')
pipeline.save_audit_results('./fairxai_results_synthetic')

Output files:
├─ fairxai_audit_fairness_before.json
│  ├─ SPD/DI metrics before
│  └─ Interpretation
├─ fairxai_audit_fairness_after.json
│  ├─ SPD/DI metrics after
│  └─ Improvement metrics
├─ fairxai_audit_explainability.json
│  └─ Feature importance ranking
└─ SYNTHETIC_FAIRNESS_AUDIT.txt
   ├─ Executive summary
   ├─ Detailed findings
   ├─ Feature importance
   └─ Recommendations


═════════════════════════════════════════════════════════════════════════════

🔍 STEP 3: REAL-WORLD VALIDATION WITH KAGGLE DATA
──────────────────────────────────────────────────

3.1 Initialize Pipeline for Kaggle
───────────────────────────────────

pipeline_kaggle = FairXAIAuditingPipeline(
    project_name="AI Resume Analyzer - Kaggle Validation"
)

pipeline_kaggle.data = kaggle_df


3.2 Run Same Analysis on Kaggle
───────────────────────────────

# Note: Skip gender if not in Kaggle data
fairness_kg = pipeline_kaggle.compute_fairness_metrics(
    attributes={
        # 'gender': ('Male', 'Female'),  # If available
        'experience_level': ('senior', 'entry')  # Compare to synthetic
    }
)

importance_kg = pipeline_kaggle.compute_feature_importance()
mitigated_kg = pipeline_kaggle.apply_mitigation('threshold_adjustment', 'experience_level')
fairness_after_kg = pipeline_kaggle.verify_mitigation(mitigated_kg, {...})

report_kg = pipeline_kaggle.generate_audit_report('KAGGLE_FAIRNESS_AUDIT.txt')
pipeline_kaggle.save_audit_results('./fairxai_results_kaggle')


3.3 Compare Real vs Synthetic
──────────────────────────────

import json
import pandas as pd

# Load both results
with open('./fairxai_results_synthetic/fairxai_audit_fairness_before.json') as f:
    syn_before = json.load(f)

with open('./fairxai_results_kaggle/fairxai_audit_fairness_before.json') as f:
    kg_before = json.load(f)

# Create comparison table
comparison = pd.DataFrame({
    'Attribute': ['gender', 'experience'],
    'Synthetic SPD': [-0.15, -0.22],  # Your actual values
    'Kaggle SPD': [-0.12, -0.18],     # Your actual values
    'Pattern Match': ['Yes', 'Yes']
})

print(comparison)

Interpretation:
├─ ✅ If patterns match → Synthetic data valid for testing
├─ ⚠️ If patterns differ → Investigate data differences
└─ → Use for paper: "Findings validated on real-world data"


═════════════════════════════════════════════════════════════════════════════

📊 STEP 4: COMPARATIVE ANALYSIS & RESEARCH PAPER
───────────────────────────────────────────────────

4.1 Create Tables for Paper
───────────────────────────

Table 1: Fairness Metrics Before/After (Synthetic)
┌──────────────┬────────┬──────────┬─────────┬──────────┐
│ Metric       │ Before │ Fair?    │ After   │ Fair?    │
├──────────────┼────────┼──────────┼─────────┼──────────┤
│ SPD (Gender) │ -0.150 │ ❌ NO    │ -0.020  │ ✅ YES   │
│ DI (Gender)  │ 0.750  │ ❌ NO    │ 0.980   │ ✅ YES   │
│ SPD (Exp)    │ -0.220 │ ❌ NO    │ 0.050   │ ✅ YES   │
│ DI (Exp)     │ 0.600  │ ❌ NO    │ 0.950   │ ✅ YES   │
└──────────────┴────────┴──────────┴─────────┴──────────┘


Table 2: Feature Importance (SHAP/Permutation)
┌────────────────────┬────────────┬──────────────┐
│ Feature            │ Importance │ Bias Level   │
├────────────────────┼────────────┼──────────────┤
│ Years Experience   │ 45%        │ HIGH 🚨      │
│ Job Title          │ 28%        │ MEDIUM ⚠️    │
│ Education          │ 16%        │ LOW ✓        │
│ Num Skills         │ 11%        │ LOW ✓        │
└────────────────────┴────────────┴──────────────┘


Table 3: Real vs Synthetic Validation
┌──────────────────────┬────────────┬──────────┬──────────┐
│ Attribute            │ Synthetic  │ Kaggle   │ Match?   │
├──────────────────────┼────────────┼──────────┼──────────┤
│ SPD (Experience)     │ -0.220     │ -0.180   │ ✅ Yes   │
│ DI (Experience)      │ 0.600      │ 0.620    │ ✅ Yes   │
│ Top Feature (Imp.)   │ Yrs. Exp   │ Yrs. Exp │ ✅ Yes   │
└──────────────────────┴────────────┴──────────┴──────────┘


4.2 Create Figures
──────────────────

Figure 1: Fairness Metrics Comparison
[Bar chart: Before/After for SPD and DI]

Figure 2: Feature Importance
[Horizontal bar chart: Top 5 features]

Figure 3: Real vs Synthetic Validation
[Side-by-side comparison of fairness metrics]

Figure 4: Fairness-Accuracy Tradeoff
[Plot: Accuracy vs |SPD| for different mitigation levels]


4.3 Write Results Section
────────────────────────

Template:

"We evaluated fairness using 600 synthetic resumes (balanced gender
and experience groups) and validated findings on the Kaggle resume
dataset.

Baseline Analysis:
- Synthetic data showed significant bias: SPD(gender)=-0.15, DI=0.75
- Feature analysis revealed years_experience as primary bias driver
- Kaggle data showed similar patterns (SPD=-0.12), validating findings

After Applying Threshold Adjustment:
- SPD improved to -0.02 (87% reduction)
- DI improved to 0.98 (achieving fairness)
- Accuracy dropped by 3% (acceptable tradeoff)

[INSERT TABLES 1-3 AND FIGURES 1-4]"


═════════════════════════════════════════════════════════════════════════════

🎓 RESEARCH PAPER STRUCTURE
───────────────────────────

Your paper should include:

1. INTRODUCTION
   └─ Problem: Resume analyzers perpetuate bias

2. RELATED WORK
   └─ AIF360, Fairlearn, Amazon hiring bias study

3. METHODOLOGY
   ├─ System architecture
   ├─ Datasets (Real: Kaggle, Synthetic: 600 balanced)
   ├─ Metrics (SPD, DI definitions)
   └─ Mitigation strategies

4. EXPERIMENTS
   ├─ Setup (what you ran)
   ├─ Datasets (sizes, distributions)
   └─ Evaluation protocol

5. RESULTS [← Use outputs from pipeline]
   ├─ Baseline fairness metrics
   ├─ Feature importance analysis
   ├─ Mitigation effectiveness
   └─ Real vs synthetic validation

6. DISCUSSION
   ├─ Fairness-accuracy tradeoff
   ├─ Root causes of bias
   ├─ Mitigation strategy comparison
   └─ Real-world applicability

7. CONCLUSION
   ├─ Contributions
   ├─ Limitations
   └─ Future work


═════════════════════════════════════════════════════════════════════════════
"""

# ============================================================================
# EXECUTION SCRIPT
# ============================================================================

if __name__ == "__main__":
    
    print("\n" + "="*100)
    print("FAIR-XAI COMPLETE WORKFLOW")
    print("="*100)
    print(DETAILED_WORKFLOW)
    
    # Save to file
    with open('FAIRXAI_COMPLETE_WORKFLOW.txt', 'w') as f:
        f.write(DETAILED_WORKFLOW)
    
    print("\n✅ Workflow guide saved to: FAIRXAI_COMPLETE_WORKFLOW.txt")
