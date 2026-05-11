"""
Fair-XAI Research Paper - Implementation Details & Guide

Paper Title:
"Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework 
for Transparent and Equitable Hiring Systems"

This document provides the complete implementation framework for:
- Dataset preparation (real Kaggle + synthetic)
- Model setup and predictions
- Fairness metrics computation (SPD, DI)
- Explainability analysis using SHAP
- Mitigation strategies and effectiveness
- Statistical rigor and reproducibility
"""

# =============================================================================
# SECTION 1: INTRODUCTION & MOTIVATION
# =============================================================================

INTRODUCTION = """
INTRODUCTION

1.1 Context
Resume-screening augmented intelligence (AI) systems are widely deployed in hiring 
pipelines to automatically filter candidates at scale. However, these systems risk 
perpetuating or amplifying historical biases present in training data, leading to:

- Systematic disadvantage of underrepresented groups (e.g., women in tech)
- Unfair evaluation based on protected attributes (gender, age, experience)
- Legal liability under fair hiring laws (e.g., EEOC guidelines, US Civil Rights Act)
- Erosion of public trust in automated hiring

1.2 Problem Statement
Current resume analyzers lack:
✗ Transparent explanation of hiring decisions
✗ Auditable fairness guarantees
✗ Mechanisms to detect and mitigate bias
✗ Reproducible methodology combining real + synthetic data

1.3 Proposed Solution: FAIR-XAI Framework
We propose FAIR-XAI, combining:
- Fairness metrics (SPD, DI) for bias quantification
- Explainability (SHAP) for transparency
- Intervention strategies (threshold adjustment, feature reweighting)
- Real-world validation (Kaggle resumes) + controlled experiments (synthetic data)

1.4 Contributions
1. Novel framework combining fairness + explainability for hiring systems
2. Controlled experiments using 600 synthetic resumes with balanced sensitive attributes
3. Comparison of real vs synthetic data for bias analysis
4. Practical mitigation strategies with measured effectiveness
5. Open-source implementation for reproducibility
"""

# =============================================================================
# SECTION 2: RELATED WORK
# =============================================================================

RELATED_WORK = """
RELATED WORK

2.1 Fairness in Machine Learning
Key frameworks and toolkits:
- AIF360 (IBM): Comprehensive fairness metrics and algorithms
- Fairlearn (Microsoft): Fair machine learning algorithms
- Amazon Hiring AI (Dastin, 2018): Documented gender bias in recruiting

Key metrics:
- Statistical Parity: Equal selection rates across groups
- Equalized Odds: Equal TPR/FPR across groups
- Disparate Impact: Legal 80% rule from employment law

2.2 Explainability & Interpretability
Popular XAI approaches:
- LIME (Local Interpretable Model-Agnostic Explanations)
- SHAP (SHapley Additive exPlanations) - Game theory based
- Feature Importance: Permutation, MDI, gradient-based

Why SHAP for our work:
✓ Theoretically grounded (shapley values)
✓ Consistent and locally accurate
✓ Can identify which features contribute to bias

2.3 Hiring Bias Literature
- Gender bias in tech hiring (Reuben et al., 2014)
- Racial bias in resume screening (Quillian et al., 2019)
- Experience-based discrimination
- Resume parser accuracy issues

2.4 Synthetic Data for Fairness
Limited prior work on synthetic resume generation for fairness testing:
- Controlled attribute manipulation
- Testing interventions without harming real candidates
- Reproducible experimentation at scale

2.5 Positioning Our Work
Our contribution:
✓ Combines fairness + explainability (most prior work tackles separately)
✓ Uses controlled synthetic data (600 resumes) + real data validation
✓ Practical mitigation strategies with effectiveness measurement
✓ Complete end-to-end auditing pipeline
"""

# =============================================================================
# SECTION 3: METHODOLOGY
# =============================================================================

METHODOLOGY = """
METHODOLOGY

3.1 System Architecture

┌────────────────────────────────────────────────┐
│         AI RESUME ANALYZER PIPELINE             │
├────────────────────────────────────────────────┤
│                                                 │
│  INPUT: Resume (PDF/Text)                      │
│    ↓                                           │
│  [1] PREPROCESSING & FEATURE EXTRACTION        │
│    • Resume parsing (education, skills, etc)   │
│    • Embedding generation (BERT, SentenceTransformers)
│    • Clean text preparation                    │
│    ↓                                           │
│  [2] PREDICTION & SCORING                      │
│    • Semantic matching (resume vs job desc)    │
│    • Binary prediction: shortlist (1) or reject (0)
│    • Continuous score: 0.0 - 1.0               │
│    ↓                                           │
│  [3] FAIRNESS AUDITING                         │
│    • Compute SPD, DI by gender & experience    │
│    • Statistical significance testing          │
│    ↓                                           │
│  [4] EXPLAINABILITY ANALYSIS                   │
│    • SHAP feature importance                   │
│    • Identify which features drive decisions   │
│    ↓                                           │
│  [5] BIAS MITIGATION                           │
│    • Threshold adjustment per group            │
│    • Feature reweighting                       │
│    ↓                                           │
│  OUTPUT: Fair, Explainable Hiring Decision     │
│                                                 │
└────────────────────────────────────────────────┘

3.2 Datasets

A. Real-World Data (Kaggle Resume Dataset)
   - Source: Kaggle Resumes Dataset
   - Size: 50-100+ actual resumes
   - Purpose: Real-world validation
   - Contains: Text embeddings, parsed features
   - Missing: Sensitive attributes (estimated from names/context)
   - Use: Validate metrics on authentic data

B. Synthetic Data (Controlled Experiments)
   - Generated: 600 synthetic resumes
   - Strategy: Balanced gender (Male/Female) × experience (entry/mid/senior)
   - Distribution: 100 resumes per group
   - Attributes:
     * Gender (SENSITIVE): Male, Female
     * Experience level (SENSITIVE): entry (0-2yr), mid (3-7yr), senior (8-15yr)
     * Years of experience, education, skills, job history
   - Purpose: Controlled fairness testing
   - Advantage: Known sensitive attributes, reproducible

3.3 Feature Engineering

Categorical Features (extracted from resume text):
- Gender (Male/Female) - SENSITIVE
- Experience level - SENSITIVE
- Education level (Bachelor's, Master's, PhD)
- Job category (Software Engineer, Data Scientist, etc)

Numerical Features:
- Years of total experience
- Number of technical skills
- Education score (0-100)
- Previous companies count

Text Features (Embedded):
- Resume clean text → BERT embedding (768-dim)
- Job description → BERT embedding
- Semantic similarity (cosine distance)

3.4 Fairness Metrics Definitions

A. Statistical Parity Difference (SPD)

SPD = P(Ŷ=1|unprivileged) - P(Ŷ=1|privileged)

Where:
- Ŷ=1: Positive prediction (shortlisted)
- Unprivileged: Female group or entry-level
- Privileged: Male group or senior-level

Interpretation:
- SPD = 0: Perfect fairness (equal selection rates)
- |SPD| < 0.10: Fair (≤10% difference)
- |SPD| ≥ 0.10: Biased

Fair Threshold: |SPD| < 0.10

B. Disparate Impact (DI)

DI = P(Ŷ=1|unprivileged) / P(Ŷ=1|privileged)

Interpretation:
- DI = 1.0: Perfect fairness
- 0.80 ≤ DI ≤ 1.25: Fair (80% rule+)
- DI < 0.80: Adverse impact on unprivileged

Fair Threshold: 0.80 ≤ DI ≤ 1.25

C. Statistical Significance

- Method: Chi-square test (binary predictions)
- Null hypothesis: Selection rates are independent of group
- p-value < 0.05: Significant difference (reject H0, bias present)

3.5 Explainability Method: SHAP

Algorithm:
1. Compute Shapley values for each feature
2. Measure marginal contribution of each feature
3. Average across all possible feature orderings
4. Generate feature importance ranking

Output:
- Global importance: Which features matter overall
- Local importance: Why specific predictions were made
- Feature interactions: Which features combine to cause bias

3.6 Mitigation Strategies

A. Threshold Adjustment (Post-processing)
   
   Strategy: Apply group-specific decision thresholds
   
   Process:
   1. For each group, find threshold that yields target selection rate
   2. Grid search: threshold ∈ [0.0, 1.0] with 0.05 steps
   3. Objective: Minimize |SPD - target_SPD|
   4. Apply thresholds at inference time
   
   Advantages: Model-agnostic, no retraining
   Disadvantages: May reduce accuracy, requires fairness-accuracy tradeoff analysis

B. Feature Reweighting (Algorithmic)
   
   Strategy: Reduce weight of biased features
   
   Process:
   1. Identify biased features via SHAP (high difference across groups)
   2. Compute reweighting factors: weight_i = 1 - (bias_score_i * scaling)
   3. Scale feature values before model
   4. Retrain or adjust scoring
   
   Advantages: Interpretable, maintains explainability
   Disadvantages: Requires model retraining, may reduce predictive power

C. Equalized Odds (Post-processing)
   
   Strategy: Ensure equal TPR and FPR across groups
   
   Process:
   1. Compute confusion matrices per group
   2. Find adjustment matrix minimizing unfairness
   3. Apply adjustment to posteriors
   
   Advantages: Balances false positives and false negatives
   Disadvantages: Computationally complex

3.7 Experimental Protocol

Phase 1: Baseline Assessment
├─ Load Kaggle + synthetic data
├─ Generate model predictions
├─ Compute SPD/DI metrics
├─ Conduct SHAP analysis
└─ Document bias findings

Phase 2: Intervention
├─ Apply mitigation strategy
├─ Adjust thresholds/reweight features
├─ Generate new predictions
└─ Verify fairness improvements

Phase 3: Statistical Analysis
├─ Compute confidence intervals for metrics
├─ Conduct hypothesis testing
├─ Report effect sizes
└─ Compare across strategies

Phase 4: Validation
├─ Test on held-out real data (Kaggle)
├─ Compare synthetic vs real fairness metrics
├─ Assess generalization
└─ Document limitations

3.8 Statistical Rigor

Confidence Intervals:
- Wilson score interval for selection rates (proportion)
- Handles small sample sizes better than normal approximation
- 95% confidence level (α = 0.05)

Hypothesis Testing:
- Chi-square test for independence (binary predictions)
- Two-sample t-test for continuous scores
- p-value threshold: 0.05

Power Analysis:
- Minimum sample size needed to detect fairness violations
- Conduct sensitivity analysis
- Report achieved power for reported effects

Reproducibility:
- Fixed random seeds (42)
- Document all hyperparameters
- Provide code + datasets
- Open-source implementation
"""

# =============================================================================
# SECTION 4: IMPLEMENTATION DETAILS
# =============================================================================

IMPLEMENTATION_DETAILS = """
IMPLEMENTATION DETAILS

4.1 Software Architecture

Module 1: fairxai_synthetic_data_generator.py
Purpose: Generate 600 controlled synthetic resumes
Key Classes:
  - SyntheticResumeGenerator: Main generator class
Methods:
  - generate_resume(): Create single resume with attributes
  - generate_dataset(): Create full dataset (balanced)
  - save_dataset(): Export to JSON file
Output: fairxai_synthetic_resumes_600.json

Module 2: fairxai_fairness_metrics.py
Purpose: Compute fairness metrics (SPD, DI)
Key Classes:
  - FairnessMetricsCalculator: All fairness computations
Methods:
  - compute_spd(): Statistical Parity Difference
  - compute_di(): Disparate Impact ratio
  - analyze_fairness(): Comprehensive analysis
  - generate_fairness_report(): Human-readable output
Output: fairxai_fairness_results.json + .txt report

Module 3: fairxai_explainability.py
Purpose: Explain predictions using SHAP
Key Classes:
  - ExplainabilityAnalyzer: SHAP-based analysis
  - PermutationImportanceAnalyzer: Alternative method
Methods:
  - initialize_shap_explainer(): Setup SHAP explainer
  - compute_shap_values(): Generate SHAP values
  - get_feature_importance(): Rank features
  - analyze_bias_by_attribute(): Group-specific analysis
Output: Feature importance rankings + visualizations

Module 4: fairxai_mitigation_strategies.py
Purpose: Apply fairness interventions
Key Classes:
  - ThresholdAdjustmentMitigation: Group-specific thresholds
  - FeatureReweightingMitigation: Reduce biased feature weights
  - EqualizedOddsMitigation: Equalized opportunity
  - MitigationReport: Compare before/after
Methods:
  - find_optimal_thresholds(): Search fairness-optimal thresholds
  - apply_thresholds(): Apply to new data
  - identify_biased_features(): SHAP-based identification
Output: Mitigated predictions + effectiveness metrics

Module 5: fairxai_auditing_pipeline.py
Purpose: End-to-end auditing workflow
Key Classes:
  - FairXAIAuditingPipeline: Complete pipeline
Workflow (7 steps):
  1. load_data() - Load dataset
  2. compute_fairness_metrics() - Baseline metrics
  3. compute_feature_importance() - Explainability
  4. analyze_bias_causes() - Root cause analysis
  5. apply_mitigation() - Apply intervention
  6. verify_mitigation() - Post-mitigation metrics
  7. generate_audit_report() - Final report
Output: Comprehensive audit report + all intermediate results

4.2 Key Hyperparameters & Tuning

Fairness Metrics:
- SPD_THRESHOLD = 0.10 (acceptable difference)
- DI_LOWER_THRESHOLD = 0.80, DI_UPPER_THRESHOLD = 1.25
- Confidence level = 0.95 (α = 0.05)

Threshold Adjustment:
- Grid search resolution: 0.05 increments (21 values per threshold)
- Target SPD: 0.0 (perfect parity)
- Can be tuned based on organizational requirements

Feature Reweighting:
- Bias threshold (SHAP): 0.05
- Weight reduction scaling: 2x bias score (configurable)
- Can be fine-tuned based on domain knowledge

Synthetic Data Generation:
- Total: 600 resumes
- Balanced groups: 100 per gender-experience combination
- Random seed: 42 (reproducibility)
- Can scale to larger N if needed

4.3 Model Selection

For Resume Matching (Base Model):
Option A: Sentence Transformers (Recommended)
  Model: all-MiniLM-L6-v2
  Embedding dim: 384
  Speed: Fast
  Size: 22 MB
  
  Similarities: Cosine distance
  Prediction: sin(cosine_distance)

Option B: BERT (More Accurate)
  Model: bert-base-uncased
  Embedding dim: 768
  Speed: Slower
  Size: 440 MB
  
  Fine-tuning possible if labeled data available

Fairness-Aware Models:
- Inherently Fair Representations (IFR)
- Adversarial Debiasing
- Fair PCA

For this research: Use pre-trained embedding + fairness post-processing
(Threshold adjustment, feature reweighting)

4.4 Data Processing Pipeline

Step 1: Resume Parsing
Input: PDF/DOCX/TXT resume file
Process:
  - Extract text, contact info
  - Parse sections: education, skills, experience
  - Identify job title, years of experience
  - Associate gender (from name + context) [synthetic only]
Output: Structured resume dict

Step 2: Feature Extraction
Process:
  - Convert text to embeddings (BERT/SentenceTransformers)
  - Encode categorical features (education level, role category)
  - Normalize numerical features (years, skill count)
  - Create clean_text (remove names for bias reduction)
Output: Feature vectors

Step 3: Job Description Matching
Input: Job description text
Process:
  - Parse job requirements
  - Generate embeddings
  - Compute semantic similarity
  - Generate match score (0-1)
Output: Prediction score per resume-job pair

Step 4: Binary Decision
Process:
  - Apply threshold (default: 0.5)
  - Or use group-specific thresholds (post-mitigation)
Output: Binary prediction (0=reject, 1=shortlist)

4.5 Validation & Testing

Unit Tests:
- Test SPD/DI computation accuracy
- Test SHAP value generation
- Test threshold adjustment logic

Integration Tests:
- End-to-end pipeline with sample data
- Fairness metric correlation checks
- Before/after mitigation comparisons

Cross-Validation:
- k-fold on synthetic data (k=5)
- Train/test split on Kaggle data (80/20)
- Evaluate metric stability across folds

Reproduction:
- Fixed seed (42) for all randomness
- Document exact library versions
- Provide sample test data
- Include expected outputs

4.6 Dependency & Environment Setup

Required Libraries:
```
Core:
  - pandas==2.2.2
  - numpy==1.26.4
  - scikit-learn==1.5.1

NLP & Embedding:
  - transformers==4.42.4
  - sentence-transformers==3.0.1
  - torch==2.3.1

Explainability:
  - shap>=0.14.0
  - lime>=0.2.0

Fairness (optional):
  - aif360>=0.6.0
  - fairlearn>=0.10.0

Visualization:
  - matplotlib>=3.8.0
  - seaborn>=0.13.0

Statistical:
  - scipy>=1.14.0
  - statsmodels>=0.14.0

Database (if using):
  - sqlalchemy==3.1.1
  - flask-sqlalchemy==3.1.1
```

Installation:
```bash
pip install -r fairxai_requirements.txt
# Or install individually as shown above
```

4.7 Configuration Management

Create fairxai_config.py or YAML:
```python
# Dataset paths
DATA_DIR = './data'
SYNTHETIC_DATA_FILE = 'fairxai_synthetic_resumes_600.json'
KAGGLE_DATA_FILE = 'kaggle_resumes.csv'

# Model configuration
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
EMBEDDING_DIM = 384
SIMILARITY_METRIC = 'cosine'
PREDICTION_THRESHOLD = 0.5

# Fairness settings
SPD_THRESHOLD = 0.10
DI_LOWER = 0.80
DI_UPPER = 1.25

# Mitigation settings
TARGET_SPD = 0.0
TARGET_DI = 1.0
REWEIGHTING_SCALING = 2.0

# Output settings
OUTPUT_DIR = './fairxai_results'
REPORT_FORMAT = 'txt'  # 'txt' or 'html' or 'pdf'
```

4.8 Reproducibility Checklist

✓ Fixed random seeds (numpy, sklearn, torch)
✓ Documented all hyperparameters
✓ Provided dataset versions/sources
✓ Specified library versions (requirements.txt)
✓ Code comments explaining key logic
✓ Example usage in __main__ blocks
✓ Sample data for testing
✓ Expected outputs documented
✓ Open-source license (MIT/Apache)
✓ GitHub repository with CI/CD

Implementation Status:
✅ fairxai_fairness_metrics.py - Complete
✅ fairxai_explainability.py - Complete (with/without SHAP)
✅ fairxai_mitigation_strategies.py - Complete
✅ fairxai_auditing_pipeline.py - Complete
✅ fairxai_synthetic_data_generator.py - Complete (optional)
❌ fairxai_shap_visualization.py - Future work
❌ fairxai_aif360_integration.py - Future work
"""

# =============================================================================
# SECTION 5: EXPECTED RESULTS & DISCUSSION
# =============================================================================

EXPECTED_RESULTS = """
EXPECTED RESULTS & INTERPRETATION

5.1 Baseline Fairness Metrics (Before Mitigation)

Synthetic Data:
┌─────────────────┬──────────┬──────────────┬──────────┐
│ Attribute       │ SPD      │ Fair (SPD)   │ DI       │
├─────────────────┼──────────┼──────────────┼──────────┤
│ Gender (F vs M) │ -0.15    │ ❌ NO        │ 0.75     │
│ Experience      │ -0.22    │ ❌ NO        │ 0.60     │
└─────────────────┴──────────┴──────────────┴──────────┘

Interpretation:
- Females shortlisted at 15% LOWER rate than males (SPD = -0.15)
- Entry-level shortlisted at 22% LOWER rate than senior (SPD = -0.22)
- System shows BIAS against unprivileged groups

Kaggle Data:
- Real data likely shows similar or greater disparities
- Validates synthetic data findings

5.2 Feature Importance Analysis (SHAP)

Top biased features (high SHAP difference across groups):
┌────────────┬────────────┬──────────────┐
│ Feature    │ Male SHAP  │ Female SHAP  │ Difference
├────────────┼────────────┼──────────────┤
│ years_exp  │ 0.180      │ 0.045        │ 0.135 🚨
│ job_title  │ 0.150      │ 0.085        │ 0.065 ⚠️
│ education  │ 0.095      │ 0.089        │ 0.006 ✓
│ skills_cnt │ 0.078      │ 0.072        │ 0.006 ✓
└────────────┴────────────┴──────────────┴──────────┘

Key Finding: Years of experience is most biased feature
- Likely because females have lower avg experience (artifact of data)
- Or: Model overweights experience, unreasonably penalizing junior females

5.3 Post-Mitigation Results (After Threshold Adjustment)

Synthetic Data:
┌─────────────────┬──────────┬──────────────┬──────────┐
│ Attribute       │ SPD      │ Fair (SPD)   │ DI       │
├─────────────────┼──────────┼──────────────┼──────────┤
│ Gender (F vs M) │ -0.02    │ ✅ YES       │ 0.98     │
│ Experience      │ 0.05     │ ✅ YES       │ 0.95     │
└─────────────────┴──────────┴──────────────┴──────────┘

Interpretation:
- Threshold adjustment brings metrics within fairness thresholds
- SPD improved from -0.15 to -0.02 (86.7% improvement)
- DI improved from 0.75 to 0.98 (30% improvement toward parity)

5.4 Fairness-Accuracy Tradeoff

Expected:
- Some reduction in overall accuracy (1-5% typical)
- Accuracy more important than fairness? No - legal/ethical imperative

Accuracy Before: 0.75
Accuracy After:  0.72
Loss: 4% (acceptable)

5.5 Dataset Comparison (Real vs Synthetic)

Kaggle Data:
├─ Size: 50-100 resumes
├─ Real-world distribution
├─ Authentic writing styles
├─ Natural bias patterns
└─ Use: Validate findings generalize

Synthetic Data:
├─ Size: 600 resumes
├─ Controlled/balanced distribution
├─ Programmatic generation
├─ Reproducible fairness gaps
└─ Use: Controlled experiments, hypothesis testing

Validation Approach:
1. Measure fairness metrics on BOTH datasets
2. Compare: Do synthetic results match real data trends?
3. If yes: Synthetic data validates findings
4. If no: Investigate why (data distribution, etc)

Expected outcome:
✅ Fairness improvements on synthetic should generalize to real data
"""

# =============================================================================
# SECTION 6: RUNNING THE COMPLETE PIPELINE
# =============================================================================

USAGE_GUIDE = """
USAGE GUIDE: HOW TO RUN FAIR-XAI FRAMEWORK

OPTION 1: Quick Demo (All-in-One Script)
──────────────────────────────────────────

from fairxai_auditing_pipeline import FairXAIAuditingPipeline
import pandas as pd

# Initialize pipeline
pipeline = FairXAIAuditingPipeline(project_name="My AI Analyzer")

# Load your dataset (CSV or JSON)
pipeline.load_data('my_dataset.csv', 
                  sensitive_attributes=['gender', 'experience_level'])

# STEP 1: Compute fairness metrics (BEFORE mitigation)
fairness_before = pipeline.compute_fairness_metrics(
    attributes={
        'gender': ('Male', 'Female'),
        'experience_level': ('senior', 'entry')
    }
)

# STEP 2: Explainability analysis
importance = pipeline.compute_feature_importance(method='permutation')

# STEP 3: Root cause analysis
causes = pipeline.analyze_bias_causes('gender')

# STEP 4: Apply mitigation
mitigated_predictions = pipeline.apply_mitigation(
    mitigation_type='threshold_adjustment',
    sensitive_attr='gender'
)

# STEP 5: Verify improvements (AFTER mitigation)
fairness_after = pipeline.verify_mitigation(
    mitigated_predictions,
    attributes={'gender': ('Male', 'Female')}
)

# STEP 6 & 7: Generate report
report = pipeline.generate_audit_report('audit_report.txt')
pipeline.save_audit_results('./fairxai_results')

Output:
✅ fairxai_audit_fairness_before.json
✅ fairxai_audit_fairness_after.json
✅ fairxai_audit_explainability.json
✅ audit_report.txt


OPTION 2: Component-Based Analysis
────────────────────────────────────

# Use individual modules for more control

# A. Fairness analysis only
from fairxai_fairness_metrics import FairnessMetricsCalculator
import pandas as pd

df = pd.read_csv('my_resumes.csv')  # Must have: 'prediction', 'gender', 'experience_level'

calculator = FairnessMetricsCalculator(df)
results = calculator.analyze_fairness({
    'gender': ('Male', 'Female')
})

calculator.save_results(results, 'fairness_results.json')
report = calculator.generate_fairness_report(results)
print(report)


# B. Explainability only
from fairxai_explainability import PermutationImportanceAnalyzer
from sklearn.ensemble import RandomForestClassifier

X = df[numeric_features]
y = df['prediction']

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# Analyze importance
analyzer = PermutationImportanceAnalyzer(model, X, y, metric='accuracy')
importance = analyzer.compute_importance(n_repeats=10)
# Returns: {'features': [...], 'importance_scores': [...]}


# C. Threshold mitigation only
from fairxai_mitigation_strategies import ThresholdAdjustmentMitigation

df['prediction_score'] = ...  # Your continuous scores

mitigator = ThresholdAdjustmentMitigation(target_spd=0.0)

# Find optimal thresholds per group
thresholds = mitigator.find_optimal_thresholds(
    df,
    sensitive_attr='gender',
    score_col='prediction_score',
    privileged_val='Male',
    unprivileged_val='Female'
)

# Apply thresholds
mitigated = mitigator.apply_thresholds(df, 'gender', 'prediction_score')


OPTION 3: With Pre-trained Model (SHAP Support)
────────────────────────────────────────────────

from fairxai_explainability import ExplainabilityAnalyzer
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Prepare data
X_train = pd.read_csv('train_features.csv')
X_test = pd.read_csv('test_features.csv')

# Train model (or load pre-trained)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Initialize SHAP analyzer
analyzer = ExplainabilityAnalyzer(model, X_train)  # Use small train set for background

# Compute SHAP values
analyzer.initialize_shap_explainer(explainer_type='tree')
shap_values = analyzer.compute_shap_values(X_test, max_samples=100)

# Get global importance
importance = analyzer.get_feature_importance(feature_names=X_test.columns)

# Analyze group-wise bias
bias_analysis = analyzer.analyze_bias_by_attribute(
    X_test,
    sensitive_attribute='gender',
    shap_values=shap_values
)

# Create visualizations
analyzer.plot_shap_summary(filename='shap_summary.png')


INPUT FILE FORMAT REQUIREMENTS
──────────────────────────────

CSV Format (recommended):
┌──────┬────────┬────────┬─────────────────┬──────────────┐
│ id   │ gender │ exp_level │ years_exp   │ prediction   │
├──────┼────────┼────────┼─────────────────┼──────────────┤
│ 1    │ Male   │ senior │ 10              │ 1            │
│ 2    │ Female │ entry  │ 1               │ 0            │
│ 3    │ Male   │ mid    │ 5               │ 1            │
│ ...  │ ...    │  ...   │ ...             │ ...          │
└──────┴────────┴────────┴─────────────────┴──────────────┘

Required columns:
✓ Unique identifier (id)
✓ Prediction (prediction or prediction_score)
✓ Sensitive attribute (gender, experience_level, etc)
✓ Features (years_exp, education, num_skills, etc)

JSON Format:
{
  "resumes": [
    {
      "id": 1,
      "gender": "Male",
      "years_experience": 10,
      "experience_level": "senior",
      "prediction": 1,
      ...
    },
    ...
  ],
  "metadata": {...}
}


OUTPUT FILES GENERATED
──────────────────────

After running pipeline:

fairxai_audit_fairness_before.json
├─ spd_metrics: [
│    ├─ attribute: "gender"
│    ├─ spd_value, is_fair, p_value, interpretation
│    └─ ...
│  ]
├─ di_metrics: [...]
└─ summary: {overall_system_fair, fair_attributes}

fairxai_audit_fairness_after.json
└─ Same structure as "before"

fairxai_audit_explainability.json
├─ method: "shap" or "permutation"
├─ features: [...]
├─ importance_scores: [...]
└─ relative_importance: [...]

audit_report.txt
├─ Executive Summary
├─ Detailed Findings (SPD/DI/Feature Importance)
├─ Root Cause Analysis
└─ Recommendations


INTERPRETING RESULTS
────────────────────

Is SPD Fair?
└─ |SPD| < 0.10 → ✅ FAIR
└─ |SPD| ≥ 0.10 → ❌ BIASED

Is DI Fair?
└─ 0.80 ≤ DI ≤ 1.25 → ✅ FAIR (conservative: 0.85 ≤ DI ≤ 1.0)
└─ DI < 0.80 → ❌ Adverse impact on unprivileged

Is p-value significant?
└─ p < 0.05 → ✅ Statistically significant difference
└─ p ≥ 0.05 → ❌ Not significant (could be random variation)

Which features cause bias?
└─ Look at "relative_importance" ranking
└─ High SHAP difference across groups = likely bias driver
└─ Consider domain knowledge: Is this feature valid for hiring?
"""

# =============================================================================
# PRINT ALL SECTIONS
# =============================================================================

if __name__ == "__main__":
    
    sections = {
        "1. INTRODUCTION": INTRODUCTION,
        "2. RELATED WORK": RELATED_WORK,
        "3. METHODOLOGY": METHODOLOGY,
        "4. IMPLEMENTATION DETAILS": IMPLEMENTATION_DETAILS,
        "5. EXPECTED RESULTS": EXPECTED_RESULTS,
        "6. USAGE GUIDE": USAGE_GUIDE
    }
    
    for title, content in sections.items():
        print("\n" + "="*100)
        print(title)
        print("="*100)
        print(content)
    
    # Save to file
    with open('FAIRXAI_IMPLEMENTATION_GUIDE.md', 'w') as f:
        for title, content in sections.items():
            f.write("\n" + "="*100 + "\n")
            f.write(title + "\n")
            f.write("="*100 + "\n")
            f.write(content + "\n")
    
    print("\n" + "="*100)
    print("✅ GUIDE SAVED TO: FAIRXAI_IMPLEMENTATION_GUIDE.md")
    print("="*100)
