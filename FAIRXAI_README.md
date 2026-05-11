# Fair-XAI Framework for Resume Analyzer Research Paper

## 📋 Overview

This framework provides a complete implementation for your research paper:

**"Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework for Transparent and Equitable Hiring Systems"**

All files are **separate from your original project** - no modifications to existing code.

---

## 📁 New Files Created

### 1. **fairxai_fairness_metrics.py** ⚖️
**Computes fairness metrics (SPD, DI) on your dataset**

```python
from fairxai_fairness_metrics import FairnessMetricsCalculator
import pandas as pd

df = pd.read_csv('your_dataset.csv')  # Must have: 'prediction', 'gender', 'experience_level'

calculator = FairnessMetricsCalculator(df)
results = calculator.analyze_fairness({
    'gender': ('Male', 'Female'),
    'experience_level': ('senior', 'entry')
})

calculator.save_results(results, 'fairness_results.json')
report = calculator.generate_fairness_report(results)
```

**Metrics computed:**
- ✅ Statistical Parity Difference (SPD) with p-values
- ✅ Disparate Impact (DI) with confidence intervals
- ✅ Statistical significance testing
- ✅ Effect sizes (Cohen's d, Cramér's V)
- ✅ Human-readable reports

**Output:** `fairxai_fairness_results.json` + `.txt` report

---

### 2. **fairxai_explainability.py** 🔍
**Explains model predictions using SHAP or permutation importance**

```python
from fairxai_explainability import ExplainabilityAnalyzer, PermutationImportanceAnalyzer

# Option A: With SHAP (requires shap library)
analyzer = ExplainabilityAnalyzer(model, X_train)
analyzer.initialize_shap_explainer()
analyzer.compute_shap_values(X_test)
importance = analyzer.get_feature_importance()

# Option B: Without SHAP (permutation-based, works with any model)
analyzer = PermutationImportanceAnalyzer(model, X_train, y_train)
importance = analyzer.compute_importance(n_repeats=10)
```

**Features:**
- ✅ SHAP value computation
- ✅ Global feature importance ranking
- ✅ Bias detection across groups
- ✅ Visualization support
- ✅ Works with any model type

**Output:** Feature importance rankings + group-wise bias analysis

---

### 3. **fairxai_mitigation_strategies.py** 🛡️
**Implements 3 bias mitigation techniques**

```python
from fairxai_mitigation_strategies import (
    ThresholdAdjustmentMitigation,
    FeatureReweightingMitigation,
    EqualizedOddsMitigation
)

# Threshold Adjustment (Easiest)
mitigator = ThresholdAdjustmentMitigation(target_spd=0.0)
thresholds = mitigator.find_optimal_thresholds(df, 'gender')
mitigated_preds = mitigator.apply_thresholds(df, 'gender')

# Feature Reweighting (Advanced)
shap_by_group = {...}  # From SHAP analysis
reweighter = FeatureReweightingMitigation(bias_threshold=0.05)
biased_features = reweighter.identify_biased_features(shap_by_group, feature_names)
weights = reweighter.compute_feature_weights(biased_features, n_features)
```

**Strategies included:**
- ✅ Threshold Adjustment: Group-specific decision thresholds
- ✅ Feature Reweighting: Reduce weight of biased features
- ✅ Equalized Odds: Equal TPR/FPR across groups
- ✅ Before/after fairness comparison

**Output:** Mitigated predictions + effectiveness metrics

---

### 4. **fairxai_auditing_pipeline.py** 🔗
**End-to-end pipeline integrating all components**

```python
from fairxai_auditing_pipeline import FairXAIAuditingPipeline

pipeline = FairXAIAuditingPipeline(project_name="AI Resume Analyzer")

# 1. Load your dataset
pipeline.load_data('your_data.csv', sensitive_attributes=['gender', 'experience_level'])

# 2. Compute fairness metrics (BEFORE)
fairness_before = pipeline.compute_fairness_metrics({
    'gender': ('Male', 'Female'),
    'experience_level': ('senior', 'entry')
})

# 3. Explainability analysis
importance = pipeline.compute_feature_importance(method='permutation')

# 4. Root cause analysis
causes = pipeline.analyze_bias_causes('gender')

# 5. Apply mitigation
mitigated = pipeline.apply_mitigation(
    mitigation_type='threshold_adjustment',
    sensitive_attr='gender'
)

# 6. Verify improvements (AFTER)
fairness_after = pipeline.verify_mitigation(mitigated, {...})

# 7. Generate comprehensive report
report = pipeline.generate_audit_report('audit_report.txt')
pipeline.save_audit_results('./results')
```

**Workflow (7 Steps):**
1. Data loading & validation
2. Fairness metrics (baseline)
3. Feature importance & explainability
4. Root cause analysis
5. Bias mitigation
6. Verification & improvement measurement
7. Comprehensive report generation

**Output:** 
- `fairxai_audit_fairness_before.json`
- `fairxai_audit_fairness_after.json`
- `fairxai_audit_explainability.json`
- `audit_report.txt` (human-readable)

---

### 5. **FAIRXAI_IMPLEMENTATION_GUIDE.py** 📖
**Complete research paper guide (6 sections)**

Executable = generates detailed markdown guide

```bash
python FAIRXAI_IMPLEMENTATION_GUIDE.py
# Generates: FAIRXAI_IMPLEMENTATION_GUIDE.md
```

**Sections:**
1. **Introduction** - Problem motivation, contributions
2. **Related Work** - Literature review (AIF360, Fairlearn, Amazon hiring bias)
3. **Methodology** - System architecture, datasets (real + synthetic), metrics definitions
4. **Implementation Details** - Code structure, hyperparameters, setup, validation
5. **Expected Results** - Fairness metrics before/after, accuracy tradeoff
6. **Usage Guide** - How to run each component, input/output formats

---

## 🚀 Quick Start

### Setup Dependencies
```bash
pip install pandas numpy scikit-learn scipy matplotlib seaborn
# Optional (for SHAP):
pip install shap
```

### Run Complete Audit (5 minutes)
```python
from fairxai_auditing_pipeline import FairXAIAuditingPipeline
import pandas as pd

# Load YOUR existing dataset
df = pd.read_csv('your_resumes.csv')

# Ensure columns exist:
# - 'prediction' (binary 0/1)
# - 'gender' (male/female)
# - 'experience_level' (entry/mid/senior)
# - Other numeric features for importance analysis

pipeline = FairXAIAuditingPipeline("My Analyzer")
pipeline.data = df  # Or use pipeline.load_data()

# Run 7-step pipeline
fairness_before = pipeline.compute_fairness_metrics({
    'gender': ('Male', 'Female'),
    'experience_level': ('senior', 'entry')
})

importance = pipeline.compute_feature_importance()
mitigated = pipeline.apply_mitigation('threshold_adjustment', 'gender')
fairness_after = pipeline.verify_mitigation(mitigated, {'gender': ('Male', 'Female')})

report = pipeline.generate_audit_report('REPORT.txt')
pipeline.save_audit_results('./fairxai_results')
```

---

## 📊 Data Input Requirements

Your dataset must have:

```csv
id,name,gender,years_experience,experience_level,education,num_skills,prediction,prediction_score
1,John Smith,Male,10,senior,Bachelor's,15,1,0.92
2,Jane Doe,Female,2,entry,Master's,8,0,0.35
3,Mike Johnson,Male,5,mid,Bachelor's,12,1,0.78
```

**Required columns:**
- `prediction` (0 or 1) - Binary prediction
- `gender` (Male/Female) - Sensitive attribute
- `experience_level` (entry/mid/senior) - Sensitive attribute
- Plus numeric features for importance analysis

---

## 📈 Expected Outputs

### 1. Fairness Metrics Report
```
EXECUTIVE SUMMARY
Overall System Fair: ❌ NO
Fair Attributes: 0/2

STATISTICAL PARITY DIFFERENCE (SPD)
Gender: SPD = -0.15 (Biased, people.Female get 15% fewer positive predictions)
Experience: SPD = -0.22 (Biased)

DISPARATE IMPACT (DI)
Gender: DI = 0.75 (Fails 80% rule)
Experience: DI = 0.60 (Fails 80% rule)

RECOMMENDATIONS
1. Identify biased features
2. Apply threshold adjustment or reweighting
3. Verify fairness improvements
```

### 2. Feature Importance
```
Top Biased Features (driving predictions unfairly):
1. years_experience - HIGH bias
2. job_title - MEDIUM bias
3. education - LOW bias
```

### 3. Mitigation Effectiveness
```
BEFORE: SPD = -0.15, DI = 0.75 ❌ Biased
AFTER:  SPD = -0.02, DI = 0.98 ✅ Fair
Improvement: 87% reduction in bias
Accuracy drop: 3% (acceptable)
```

---

## 🔄 Integration with Your Existing Project

These files are **completely independent**. You can:

1. **Use standalone** - Import modules independently
2. **Integrate with your backend** - Add endpoints that call pipeline
3. **Extend functionality** - Build custom mitigation strategies

### Integration Example
```python
# In your backend (app.py or ai_routes.py)
from fairxai_auditing_pipeline import FairXAIAuditingPipeline

@app.route('/api/fairness-audit', methods=['POST'])
def audit_fairness():
    """API endpoint for fairness auditing"""
    data = request.json  # {'resume_ids': [...], 'job_ids': [...]}
    
    # Load predictions from your DB
    df = load_predictions_from_db(data)
    
    # Run audit
    pipeline = FairXAIAuditingPipeline("API Audit")
    pipeline.data = df
    
    fairness = pipeline.compute_fairness_metrics({'gender': ('Male', 'Female')})
    report = pipeline.generate_audit_report()
    
    return {
        'is_fair': fairness['summary']['overall_system_fair'],
        'metrics': fairness,
        'report': report
    }
```

---

## 📝 Research Paper Structure

Use the framework to structure your paper:

```
1. INTRODUCTION
   └─ Motivation from FAIRXAI_IMPLEMENTATION_GUIDE.py

2. RELATED WORK
   └─ AIF360, Fairlearn, Amazon hiring bias (section 2)

3. PROPOSED FAIR-XAI FRAMEWORK
   ├─ Architecture diagram (section 3.1)
   ├─ Datasets: Real (Kaggle) + Synthetic (600 resumes)
   ├─ Fairness metrics definitions (SPD, DI)
   └─ Explainability via SHAP

4. EXPERIMENTAL SETUP
   └─ 7-step auditing pipeline workflow

5. RESULTS
   ├─ Fairness metrics (tables from JSON outputs)
   ├─ Feature importance ranking
   ├─ Mitigation effectiveness
   └─ Before/after comparison

6. DISCUSSION
   ├─ Fairness-accuracy tradeoff
   ├─ Real data validation
   └─ Practical deployment recommendations

7. CONCLUSION
   └─ Contributions, limitations, future work
```

---

## 🎯 Paper Contributions to Emphasize

1. **Novel Framework** - Combines fairness + explainability (most prior work addresses separately)
2. **Dual Dataset Approach** - Real Kaggle data + controlled 600 synthetic resumes
3. **Complete Auditing Pipeline** - End-to-end workflow (metrics → explainability → mitigation → verification)
4. **Practical Mitigation** - 3 techniques with measured effectiveness
5. **Statistical Rigor** - Significance tests, confidence intervals, effect sizes
6. **Reproducibility** - Open-source, fixed seeds, documented hyperparameters

---

## ✅ Checklist for Research Paper

- [ ] Use fairness metrics from `fairxai_fairness_metrics.py`
- [ ] Generate feature importance from `fairxai_explainability.py`
- [ ] Show before/after using `fairxai_mitigation_strategies.py`
- [ ] Run complete pipeline from `fairxai_auditing_pipeline.py`
- [ ] Document implementation using `FAIRXAI_IMPLEMENTATION_GUIDE.py`
- [ ] Create tables/figures from JSON outputs
- [ ] Validate on real Kaggle data
- [ ] Compare with baseline (no mitigation)
- [ ] Report confidence intervals + p-values
- [ ] Include fairness-accuracy tradeoff analysis
- [ ] Discuss limitations & future work
- [ ] Provide GitHub with reproducible code

---

## 🔗 File Relationships

```
Your Dataset
    ↓
fairxai_fairness_metrics.py ─→ BEFORE fairness metrics
    ↓
fairxai_explainability.py ───→ Feature importance analysis
    ↓
fairxai_mitigation_strategies.py → Bias correction
    ↓
fairxai_auditing_pipeline.py ──→ AFTER fairness metrics
    ↓
Final Report (tables, figures, recommendations)
```

---

## 📚 Reference Materials Included

- **Section 3**: System architecture & data flow
- **Section 4**: Implementation details (modules, hyperparameters, setup)
- **Section 5**: Expected results & interpretation guide
- **Section 6**: Usage examples for each module

---

## 🎓 Research Impact

This framework enables you to:

✅ **Demonstrate fairness** - Quantify bias in hiring systems
✅ **Provide transparency** - Explain which features drive decisions  
✅ **Show solutions** - Measure mitigation effectiveness
✅ **Ensure rigor** - Statistical testing + reproducibility
✅ **Create impact** - Practical tool for real hiring systems

---

## 💡 Next Steps

1. **Prepare your dataset** (CSV with predictions + demographics)
2. **Run the pipeline** (5 minutes for complete audit)
3. **Generate tables** (fairness metrics before/after)
4. **Create figures** (feature importance, fairness comparison)
5. **Write paper sections** (use framework as structure)
6. **Validate findings** (compare real vs synthetic data)
7. **Document code** (use provided comments as baseline)

---

## ❓ FAQ

**Q: Do I need SHAP?**
A: No. Framework provides `PermutationImportanceAnalyzer` as fallback. SHAP is optional for better explanations.

**Q: Can I use my existing model?**
A: Yes. Just provide predictions - framework doesn't care about the model. Works with any sklearn/tf/torch model.

**Q: How do I handle missing sensitive attributes?**
A: Framework can estimate (name-to-gender libraries) or you can use `fairxai_synthetic_data_generator.py` for controlled testing.

**Q: What if my dataset is unbalanced?**
A: Framework handles imbalance automatically. Results will show the bias.

**Q: Can I add custom mitigation strategies?**
A: Yes. Extend `fairxai_mitigation_strategies.py` with your own classes.

---

## 📞 Support Files & Documentation

- `FAIRXAI_IMPLEMENTATION_GUIDE.py` - Run to generate full markdown guide
- Each `.py` file has detailed docstrings and example usage in `__main__`
- Comments explain key concepts (fairness, SHAP, bias mitigation)

---

**Ready to audit fairness in your AI Resume Analyzer! 🚀**
