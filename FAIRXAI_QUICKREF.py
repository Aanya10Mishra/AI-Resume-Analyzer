"""
FAIR-XAI FRAMEWORK - QUICK REFERENCE CARD

Your Research Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: 
A FAIR-XAI Framework for Transparent and Equitable Hiring Systems"
"""

# ============================================================================
# FILE SUMMARY TABLE
# ============================================================================

import pandas as pd

FILES_SUMMARY = """
┌──────────────────────────────┬────────────────────────────────────────────────┐
│ FILE                         │ PURPOSE & KEY FUNCTIONS                        │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ fairxai_fairness_metrics.py  │ Compute fairness metrics (SPD, DI)              │
│                              │ - compute_spd(): Statistical Parity Difference  │
│                              │ - compute_di(): Disparate Impact ratio          │
│                              │ - analyze_fairness(): Complete analysis         │
│                              │ - generate_fairness_report(): Human-readable    │
│                              │ INPUT: DataFrame with predictions + attributes  │
│                              │ OUTPUT: JSON metrics + CSV report               │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ fairxai_explainability.py    │ Explain predictions using SHAP or permutation  │
│                              │ - ExplainabilityAnalyzer: SHAP-based (optional)│
│                              │ - PermutationImportanceAnalyzer: Universal     │
│                              │ - get_feature_importance(): Rank features      │
│                              │ - analyze_bias_by_attribute(): Group analysis  │
│                              │ INPUT: Model + feature data                    │
│                              │ OUTPUT: Feature importance ranking              │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ fairxai_mitigation_strat.py  │ Apply fairness mitigation techniques           │
│                              │ - ThresholdAdjustmentMitigation: Post-proc     │
│                              │ - FeatureReweightingMitigation: Feature-level  │
│                              │ - EqualizedOddsMitigation: Equal TPR/FPR       │
│                              │ INPUT: Predictions + sensitive attributes      │
│                              │ OUTPUT: Mitigated predictions                   │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ fairxai_auditing_pipeline.py │ End-to-end 7-step audit workflow               │
│                              │ Step 1: Load data                              │
│                              │ Step 2: Fairness metrics (BEFORE)              │
│                              │ Step 3: Feature importance analysis            │
│                              │ Step 4: Root cause analysis                    │
│                              │ Step 5: Apply mitigation                       │
│                              │ Step 6: Fairness metrics (AFTER)               │
│                              │ Step 7: Generate report                        │
│                              │ INPUT: CSV/JSON with data + predictions        │
│                              │ OUTPUT: Complete audit report + metrics        │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ FAIRXAI_IMPLEMENTATION_       │ Research paper guide (6 sections)              │
│ GUIDE.py                     │ Run: python FAIRXAI_IMPLEMENTATION_GUIDE.py    │
│                              │ Outputs: FAIRXAI_IMPLEMENTATION_GUIDE.md       │
│                              │ - Introduction & motivation                    │
│                              │ - Related work (AIF360, Fairlearn, etc)       │
│                              │ - Methodology & system architecture            │
│                              │ - Implementation details & code structure      │
│                              │ - Expected results & interpretation            │
│                              │ - Usage guide & input/output formats           │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ fairxai_synthetic_data_       │ Generate 600 synthetic controlled resumes      │
│ generator.py (OPTIONAL)      │ - SyntheticResumeGenerator: Main class         │
│                              │ - generate_dataset(): Create dataset            │
│                              │ Use if: You don't have labeled synthetic data   │
│                              │ OUTPUT: fairxai_synthetic_resumes_600.json     │
├──────────────────────────────┼────────────────────────────────────────────────┤
│ FAIRXAI_README.md            │ Complete framework guide                       │
│                              │ - What each file does                          │
│                              │ - Quick start examples                         │
│                              │ - Data input requirements                      │
│                              │ - Expected outputs                             │
│                              │ - Integration with existing code               │
│                              │ - Paper structure guidance                     │
└──────────────────────────────┴────────────────────────────────────────────────┘
"""

# ============================================================================
# ONE-MINUTE WORKFLOW
# ============================================================================

QUICK_WORKFLOW = """
STEP-BY-STEP (Copy & Paste Ready)
═════════════════════════════════════════════════════════════════════════════

# 1. Prepare your dataset (CSV format)
#    Required columns: id, prediction (0/1), gender, experience_level, 
#                      years_experience, num_skills, etc.

# 2. Run complete audit:

from fairxai_auditing_pipeline import FairXAIAuditingPipeline
import pandas as pd

# ─ A. Load data
pipeline = FairXAIAuditingPipeline(project_name="AI Resume Analyzer")
pipeline.load_data('your_resumes.csv', 
                  sensitive_attributes=['gender', 'experience_level'])

# ─ B. STEP 2: Fairness metrics BEFORE mitigation
fairness_before = pipeline.compute_fairness_metrics({
    'gender': ('Male', 'Female'),
    'experience_level': ('senior', 'entry')
})

# ─ C. STEP 3: Feature importance analysis
importance = pipeline.compute_feature_importance(method='permutation')

# ─ D. STEP 4: Root cause analysis
causes = pipeline.analyze_bias_causes('gender')

# ─ E. STEP 5: Apply mitigation
mitigated_preds = pipeline.apply_mitigation(
    mitigation_type='threshold_adjustment',
    sensitive_attr='gender'
)

# ─ F. STEP 6: Fairness metrics AFTER mitigation
fairness_after = pipeline.verify_mitigation(
    mitigated_preds,
    attributes={'gender': ('Male', 'Female')}
)

# ─ G. STEP 7: Generate report
report = pipeline.generate_audit_report('FAIRNESS_AUDIT.txt')
pipeline.save_audit_results('./fairxai_results')

# 3. Check outputs:
#    - fairxai_audit_fairness_before.json
#    - fairxai_audit_fairness_after.json
#    - fairxai_audit_explainability.json
#    - FAIRNESS_AUDIT.txt
"""

# ============================================================================
# KEY METRICS INTERPRETATION
# ============================================================================

METRICS_GUIDE = """
FAIRNESS METRICS AT A GLANCE
═════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────┐
│ METRIC: Statistical Parity Difference (SPD)                             │
├─────────────────────────────────────────────────────────────────────────┤
│ Definition:  SPD = P(Ŷ=1|unprivileged) - P(Ŷ=1|privileged)             │
│ Translation: Difference in positive prediction rates between groups     │
│ Fair:        |SPD| < 0.10  (≤10% difference acceptable)                │
│ Example:     SPD = -0.15   means females get 15% FEWER positive pred's │
│ If Unfair:   → Apply threshold adjustment or reweighting               │
├─────────────────────────────────────────────────────────────────────────┤
│ METRIC: Disparate Impact (DI)                                           │
├─────────────────────────────────────────────────────────────────────────┤
│ Definition:  DI = P(Ŷ=1|unprivileged) / P(Ŷ=1|privileged)              │
│ Translation: Ratio of positive prediction rates between groups         │
│ Fair:        0.80 ≤ DI ≤ 1.25  (80% rule from employment law)         │
│ Example:     DI = 0.75   means unprivileged group selected at 75%      │
│              relative to privileged (BELOW 80% threshold)              │
│ If Unfair:   → Apply mitigation strategies                              │
├─────────────────────────────────────────────────────────────────────────┤
│ METRIC: p-value (Statistical Significance)                             │
├─────────────────────────────────────────────────────────────────────────┤
│ Definition:  Probability that observed difference is due to chance     │
│ Significant: p < 0.05  (difference likely real, not random)            │
│ Not Signif:  p ≥ 0.05  (could be random variation)                     │
│ Use:         Validates that fairness gaps are statistically real       │
└─────────────────────────────────────────────────────────────────────────┘

QUICK FAIRNESS CHECK
────────────────────

Is |SPD| < 0.10?  YES ✅ FAIR        NO ❌ BIASED
Is 0.80 ≤ DI ≤ 1.25? YES ✅ FAIR    NO ❌ BIASED
Is p < 0.05?      YES ✅ SIGNIFICANT NO ❌ RANDOM

ALL THREE YES → ✅ System is FAIR
ANY NO → ❌ System is BIASED (needs mitigation)
"""

# ============================================================================
# PAPER WRITING TEMPLATES
# ============================================================================

PAPER_TEMPLATES = """
PAPER SECTIONS - FILL IN WITH YOUR RESULTS
═════════════════════════════════════════════════════════════════════════════

SECTION 3.4: FAIRNESS METRICS
──────────────────────────────
We computed two primary fairness metrics on [YOUR DATASET]:

1. Statistical Parity Difference (SPD): [INSERT TABLE FROM RESULTS]
   Our findings show [INTERPRETATION FROM fairxai_fairness_results.json]

2. Disparate Impact Ratio (DI): [INSERT TABLE FROM RESULTS]
   The [ATTRIBUTE] groups show [LEVEL OF BIAS]

Statistical significance was assessed using chi-square tests (p < 0.05).


SECTION 4: RESULTS
──────────────────

4.1 Baseline Fairness Assessment
[INSERT TABLE: fairxai_audit_fairness_before.json]

The initial model shows significant bias:
- SPD for gender: [VALUE] (Fair: [YES/NO])
- DI for experience: [VALUE] (Fair: [YES/NO])

4.2 Feature Importance Analysis
[INSERT: fairxai_audit_explainability.json]

Top features driving predictions:
1. [FEATURE] - [IMPORTANCE]%
2. [FEATURE] - [IMPORTANCE]%
3. [FEATURE] - [IMPORTANCE]%

Notably, [FEATURE] shows HIGH BIAS across gender groups, suggesting...


4.3 Mitigation Results
[INSERT TABLE: fairxai_audit_fairness_after.json]

After applying [MITIGATION STRATEGY]:
- SPD improvement: [BEFORE] → [AFTER] ([X]% improvement)
- DI improvement: [BEFORE] → [AFTER]
- Accuracy change: [VALUE]% (acceptable tradeoff)

System now achieves fairness across [X] of [Y] attributes.


SECTION 5: DISCUSSION
─────────────────────

5.1 Fairness-Accuracy Tradeoff
[DESCRIBE PERFORMANCE LOSS FROM fairxai_audit_[*].json]

5.2 Real vs Synthetic Data Validation
[COMPARE METRICS: if using both Kaggle + synthetic]

5.3 Practical Implications
[DEPLOYMENT RECOMMENDATIONS FROM ROOT CAUSE ANALYSIS]
"""

# ============================================================================
# COMMON ISSUES & SOLUTIONS
# ============================================================================

TROUBLESHOOTING = """
COMMON ISSUES & SOLUTIONS
═════════════════════════════════════════════════════════════════════════════

❌ ERROR: "KeyError: 'gender'"
───────────────────────────────
CAUSE: Required column 'gender' not found in dataset
FIX:   Make sure your CSV has 'gender' column (case-sensitive)
       Rename if needed: df.rename(columns={'Gender': 'gender'})

❌ ERROR: "No SHAP values available"
────────────────────────────────────
CAUSE: SHAP not installed or not using SHAP explainer
FIX:   Use PermutationImportanceAnalyzer instead (no SHAP needed)
       Or install: pip install shap

❌ ERROR: "ValueError: sample_size must match"
──────────────────────────────────────────────
CAUSE: Predictions array doesn't match dataset length
FIX:   Ensure: len(predictions) == len(dataframe)
       Check for mismatched indexing

❌ ERROR: "All positive predictions (or all negative)"
────────────────────────────────────────────────────
CAUSE: Bad predictions or model not properly trained
FIX:   Verify model outputs range [0,1]
       Check prediction computation logic

❌ RESULTS: SPD/DI looks suspiciously good after mitigation
──────────────────────────────────────────────────────────
CAUSE: Might be overfitting fairness at cost of accuracy
FIX:   Check accuracy drop (should be <5%)
       Use feature reweighting instead of threshold adjustment
       Consider real data validation

✅ SUCCESS INDICATORS
────────────────────
✓ Fairness metrics computed successfully
✓ p-values < 0.05 indicate real (not random) bias
✓ Feature importance shows interpretable drivers
✓ Mitigation reduces bias by 50%+ 
✓ Accuracy drop < 5%
✓ Results replicate on real data
"""

# ============================================================================
# REFERENCE: SKLEARN INTEGRATION (IF USING YOUR OWN MODEL)
# ============================================================================

SKLEARN_INTEGRATION = """
INTEGRATING WITH YOUR EXISTING MODEL
═════════════════════════════════════════════════════════════════════════════

If you have a trained sklearn model, integrate with Fair-XAI:

from fairxai_explainability import PermutationImportanceAnalyzer
from fairxai_auditing_pipeline import FairXAIAuditingPipeline
import pandas as pd

# Your model
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier()
model.fit(X_train, y_train)

# Get predictions
y_pred = model.predict(X)
y_pred_proba = model.predict_proba(X)[:, 1]  # For continuous scores

# Create DataFrame
df = pd.DataFrame({
    'id': range(len(X)),
    'gender': gender_labels,
    'experience_level': exp_labels,
    'prediction': y_pred,
    'prediction_score': y_pred_proba,
    # ... add other features
})

# Run fairness audit
pipeline = FairXAIAuditingPipeline()
pipeline.data = df

fairness = pipeline.compute_fairness_metrics({'gender': ('Male', 'Female')})
importance = pipeline.compute_feature_importance()

# For explainability with SHAP
from fairxai_explainability import ExplainabilityAnalyzer
analyzer = ExplainabilityAnalyzer(model, X_train[:100])  # Use subset for speed
analyzer.initialize_shap_explainer()
shap_values = analyzer.compute_shap_values(X[:100])
"""

# ============================================================================
# PRINT ALL SECTIONS
# ============================================================================

if __name__ == "__main__":
    sections = {
        "FILES SUMMARY": FILES_SUMMARY,
        "ONE-MINUTE WORKFLOW": QUICK_WORKFLOW,
        "METRICS INTERPRETATION": METRICS_GUIDE,
        "PAPER TEMPLATES": PAPER_TEMPLATES,
        "TROUBLESHOOTING": TROUBLESHOOTING,
        "SKLEARN INTEGRATION": SKLEARN_INTEGRATION
    }
    
    for title, content in sections.items():
        print("\n" + "="*100)
        print(f"  {title}")
        print("="*100)
        print(content)
    
    # Save to file
    with open('FAIRXAI_QUICKREF.txt', 'w', encoding='utf-8') as f:
        for title, content in sections.items():
            f.write("\n" + "="*100 + "\n")
            f.write(f"  {title}\n")
            f.write("="*100 + "\n")
            f.write(content + "\n")
    
    print("\n" + "="*100)
    print("✅ QUICK REFERENCE SAVED TO: FAIRXAI_QUICKREF.txt")
    print("="*100)
