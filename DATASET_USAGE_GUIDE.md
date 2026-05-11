# Dataset Usage Guide for Fair-XAI Resume Analyzer

## 📊 Dual-Dataset Strategy

Your Fair-XAI framework uses **two complementary datasets** for different purposes:

```
KAGGLE DATASET (Real-World)          SYNTHETIC DATASET (Controlled)
    ↓                                      ↓
Model Validation                    Fair-XAI Experiments
    ↓                                      ↓
Extract Features                    Compute Fairness Metrics
    ↓                                      ↓
Evaluate Realistic Behavior         Apply Explainability Methods
    ↓                                      ↓
Validate Feature Quality            Test Bias Interventions
    ↓                                      ↓
Real-World Performance              Research Paper Primary Analysis
```

---

## 🎯 PURPOSE 1: Kaggle Dataset (Real-World Validation)

### **File:** `preprocessed_resumes (1).csv`

### **What It Contains**
- Actual resumes from Kaggle
- Real-world resume features:
  - Education levels
  - Skills and experience
  - Job categories
  - Resume text (preprocessed)
- **May lack** sensitive attributes (gender, experience level)
- Natural distribution of resume quality

### **Why It Matters**
- **Validation:** Test the Resume Analyzer on authentic data
- **Realism:** Evaluate how predictions behave on real resumes
- **Robustness:** Confirm patterns from synthetic data generalize
- **Credibility:** Demonstrate research findings on actual resumes

### **What You'll Analyze**
1. **Feature Extraction**
   ```
   Extract from resume text:
   ├─ Years of experience (from employment history)
   ├─ Education level (from education section)
   ├─ Number of skills
   ├─ Job categories matched
   └─ Domain expertise indicators
   ```

2. **Model Behavior**
   ```
   Evaluate:
   ├─ How model scores real resumes
   ├─ Which features are most predictive
   ├─ Natural prediction distribution
   └─ Realistic acceptance/rejection rates
   ```

3. **Fairness Validation**
   ```
   Check:
   ├─ Does bias exist in real data?
   ├─ Do bias patterns match synthetic data?
   ├─ Are fairness metrics consistent?
   └─ Do interventions work on real data?
   ```

### **Workflow for Kaggle Data**

```python
from fairxai_data_loader import FairXAIDataLoader
from fairxai_auditing_pipeline import FairXAIAuditingPipeline

# Load real-world data
loader = FairXAIDataLoader()
kaggle_df = loader.load_kaggle_data("preprocessed_resumes (1).csv")

# Extract features from resume text
# (Data loader handles column standardization)

# Run fairness audit on REAL DATA
pipeline = FairXAIAuditingPipeline("Kaggle Validation")
pipeline.data = kaggle_df

# Analyze available attributes
# (May not have gender - focus on experience/education)
fairness_real = pipeline.compute_fairness_metrics({
    'experience_level': ('senior', 'entry')
    # 'gender': ('Male', 'Female')  # Only if available
})

# Compare to synthetic results
```

### **Expected Findings**
✓ **If patterns match synthetic:**
  - Bias exists in real data too
  - Synthetic experiments are valid
  - Findings generalize to production

⚠️ **If patterns differ:**
  - Investigate data differences
  - Adjust analysis accordingly
  - Focus on real data findings

---

## 🧪 PURPOSE 2: Synthetic Dataset (Fair-XAI Experiments)

### **File:** `Resume_Dataset_600_Balanced (1).xlsx`

### **What It Contains**
- **600 generated resumes** with controlled properties:
  - Gender: Male/Female (balanced)
  - Experience Level: Entry/Mid/Senior (balanced)
  - Years of Experience: Realistic range
  - Skills: Varied by experience
  - Education: Balanced distribution
- **Complete sensitive attributes** → No missing data
- **Reproducible** → Same structure for all analyses
- **Controlled** → Allows isolating fairness issues

### **Why It Matters**
- **Controlled Experiments:** All groups fully represented
- **Fairness Auditing:** Complete data for SPD/DI computation
- **Feature Importance:** Identify bias drivers reliably
- **Intervention Testing:** Test mitigation strategies
- **Primary Research:** Foundation of your paper's findings

### **What You'll Analyze**

1. **Fairness Metrics (PRIMARY ANALYSIS)**
   ```
   Compute:
   ├─ SPD (Statistical Parity Difference)
   │  ├─ By gender: Are males/females selected equally?
   │  └─ By experience: Are all levels selected equally?
   ├─ DI (Disparate Impact)
   │  ├─ By gender: Is selection ratio fair?
   │  └─ By experience: Is selection ratio fair?
   └─ Statistical Significance
      ├─ Confidence intervals
      ├─ P-values
      └─ Effect sizes
   ```

2. **Explainability Analysis**
   ```
   Identify:
   ├─ Which features drive predictions most?
   ├─ Which features show gender bias?
   ├─ Which features show experience bias?
   ├─ Feature importance ranking
   └─ Bias drivers for intervention
   ```

3. **Mitigation Experiments**
   ```
   Test:
   ├─ Threshold adjustment strategy
   ├─ Feature reweighting strategy
   ├─ Fairness improvement metrics
   ├─ Accuracy impact
   └─ Fairness-accuracy tradeoff
   ```

### **Workflow for Synthetic Data**

```python
from fairxai_data_loader import FairXAIDataLoader
from fairxai_auditing_pipeline import FairXAIAuditingPipeline

# Load controlled dataset
loader = FairXAIDataLoader()
synthetic_df = loader.load_synthetic_data("Resume_Dataset_600_Balanced (1).xlsx")

# Run COMPLETE fairness audit (primary analysis)
pipeline = FairXAIAuditingPipeline("Synthetic Fairness Analysis")
pipeline.data = synthetic_df

# STEP 1: Baseline fairness metrics
fairness_before = pipeline.compute_fairness_metrics({
    'gender': ('Male', 'Female'),           # Complete data available
    'experience_level': ('senior', 'entry')  # Complete data available
})

# STEP 2: Feature importance (identify bias drivers)
importance = pipeline.compute_feature_importance()

# STEP 3: Root cause analysis
causes = pipeline.analyze_bias_causes('gender')

# STEP 4: Apply mitigation
mitigated = pipeline.apply_mitigation('threshold_adjustment', 'gender')

# STEP 5: Post-mitigation fairness
fairness_after = pipeline.verify_mitigation(mitigated, {...})

# STEP 6: Generate comprehensive report
report = pipeline.generate_audit_report('SYNTHETIC_ANALYSIS.txt')
```

### **Expected Findings**
✓ **Baseline Bias:**
  - SPD values (e.g., -0.15 = 15% selection gap)
  - DI values (e.g., 0.75 = fails 80% rule)
  - Statistically significant (p < 0.05)

✓ **Feature Importance:**
  - Years of experience: 40-50%
  - Education: 20-30%
  - Skills: 15-25%
  - Other features: 5-15%

✓ **Mitigation Effectiveness:**
  - SPD improvement: 70-90%
  - Accuracy loss: 2-5%
  - DI reaches fairness threshold (0.80-1.25)

---

## 🔄 Comparative Workflow

After analyzing both datasets, compare them:

```python
import json

# Load both results
with open('fairxai_results_synthetic/fairxai_audit_fairness_before.json') as f:
    synthetic = json.load(f)

with open('fairxai_results_kaggle/fairxai_audit_fairness_before.json') as f:
    kaggle = json.load(f)

# Compare SPD metrics
print("VALIDATION CHECK:")
print(f"Synthetic SPD: {synthetic['spd_metrics'][0]['abs_spd']:.3f}")
print(f"Kaggle SPD:    {kaggle['spd_metrics'][0]['abs_spd']:.3f}")

if abs(synthetic_spd - kaggle_spd) < 0.1:
    print("✅ Patterns match - findings are robust")
else:
    print("⚠️  Patterns differ - investigate further")
```

---

## 📝 Using Datasets in Your Research Paper

### **Methodology Section**
```
3.1 Datasets
We employed two complementary datasets:

Kaggle Resume Dataset (Real-World):
- Contains XXX actual resumes from Kaggle
- Includes education, skills, job categories
- May have missing sensitive attributes
- Used for realistic behavior validation

Synthetic Resume Dataset (Controlled):
- 600 generated resumes with balanced attributes
- Gender: 50% Male, 50% Female
- Experience: Balanced entry/mid/senior
- Used for controlled fairness experiments

3.2 Experimental Protocol
Primary analysis used synthetic data (complete attributes):
- Compute Statistical Parity and Disparate Impact
- Apply SHAP/permutation importance analysis
- Test fairness mitigation strategies

Validation used real Kaggle data:
- Confirm bias patterns generalize
- Verify feature importance consistency
- Demonstrate real-world applicability
```

### **Results Section**
```
4.1 Synthetic Data Analysis (Primary Results)
[Tables and figures from synthetic data]

4.2 Real-World Validation (Kaggle Data)
[Comparable metrics from Kaggle data]

4.3 Robustness and Generalization
[Comparison showing pattern consistency]
```

### **Discussion Section**
```
5.1 Fairness-Accuracy Tradeoff
Analysis of synthetic data shows X% bias reduction 
with Y% accuracy loss, validated on real data.

5.2 Real-World Applicability
Findings from controlled experiments generalize to 
real Kaggle resumes, confirming practical relevance.

5.3 Robustness Across Datasets
Bias patterns show [percentage] consistency between 
synthetic and real data, demonstrating reliability.
```

---

## 🎯 Summary: Which Dataset for What?

| Task | Dataset | Reason |
|------|---------|--------|
| **Compute SPD/DI** | Synthetic | Complete sensitive attributes |
| **Feature Importance** | Synthetic | Controlled, reproducible |
| **Test Interventions** | Synthetic | Isolated variables, clear effects |
| **Validate Results** | Kaggle | Real-world patterns |
| **Extract Features** | Kaggle | Realistic resume parsing |
| **Model Behavior** | Kaggle | Natural distribution |
| **Primary Analysis** | Synthetic | Foundation of findings |
| **Confirmation** | Kaggle | Generalization proof |

---

## 🚀 Execution Order

```
1. Load SYNTHETIC dataset
   └─ Run complete analysis (fairness, explainability, mitigation)

2. Load KAGGLE dataset
   └─ Run validation analysis (confirm patterns)

3. Compare results
   └─ Demonstrate consistency and robustness

4. Generate reports
   └─ Use for research paper tables and discussion
```

---

## ✅ Quality Assurance Checklist

Before finalizing your analysis:

- [ ] Synthetic data shows measurable bias (|SPD| > 0.10 or DI < 0.80)
- [ ] Feature importance clearly identifies bias drivers
- [ ] Mitigation improves fairness metrics (70%+ reduction)
- [ ] Accuracy impact is acceptable (< 5% loss)
- [ ] Kaggle data shows similar bias patterns
- [ ] Findings are statistically significant (p < 0.05)
- [ ] Both datasets tell consistent story
- [ ] All results are reproducible

---

## 📞 Questions?

Refer to:
- `FAIRXAI_SETUP_GUIDE.md` - Complete usage guide
- `fairxai_data_loader.py` - Data loading implementation
- `fairxai_auditing_pipeline.py` - Analysis workflow
- `run_fairxai_workflow.py` - Automated execution

Your framework is ready! 🚀
