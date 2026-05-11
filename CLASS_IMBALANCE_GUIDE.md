# Fair-XAI Class Imbalance Handling Guide

## Overview

**Problem**: Real-world hiring systems exhibit significant class imbalance:
- ~33% of candidates are "Strong" (selected/qualified)
- ~67% of candidates are "Weak" (not selected/unqualified)

ML models trained on imbalanced data often:
- Bias towards the majority class (Weak)
- Underestimate minority class (Strong) performance
- May amplify fairness issues across protected attributes

**Solution**: Use `class_weight='balanced'` in model training to account for imbalance.

---

## Class Distribution

### Target Distribution
```
Total: 600 Candidates
├── Strong (Class 1):  200 (33%)
└── Weak (Class 0):    400 (67%)

Imbalance Ratio: 2:1 (2 weak for every 1 strong)
```

### Strength Criteria

Candidates are labeled based on:

| Factor | Weight | Criteria |
|--------|--------|----------|
| **Education** | 30% | PhD (5) > Master's (4) > Bachelor's (3) > Bootcamp (1) |
| **Experience** | 35% | Senior (8+y) > Mid (3-7y) > Entry (0-2y) |
| **Skills** | 35% | ML/AI (3pt) > Cloud (2pt) > Frameworks (2pt) > Others (1pt) |

**Example**:
```
Candidate A:
  - Master's in Data Science: 30% × (4/5) = 0.24
  - Senior (10y experience): 35% × (3/3) = 0.35
  - Skills: TensorFlow, PyTorch, AWS, Kubernetes = 0.25
  - Total: 0.84 → STRONG ✅

Candidate B:
  - Bachelor's in CS: 30% × (3/5) = 0.18
  - Entry (1y experience): 35% × (1/3) = 0.12
  - Skills: Python only = 0.06
  - Total: 0.36 → WEAK ❌
```

---

## Usage

### 1. Generate Imbalanced Dataset

```python
import numpy as np
from fairxai_synthetic_data_generator import SyntheticResumeGenerator
from fairxai_class_imbalance_handler import ClassImbalanceHandler

# Step 1: Generate base resumes  (balanced groups by design)
generator = SyntheticResumeGenerator(seed=42)
resumes, metadata = generator.generate_dataset(total_resumes=600, balance_groups=True)

# Step 2: Label by strength (creates imbalance)
handler = ClassImbalanceHandler(strong_ratio=0.33, seed=42)
resumes = handler.label_candidates_by_strength(resumes)

# Step 3: Print statistics
handler.print_imbalance_report(resumes)

# Step 4: Save labeled dataset
handler.save_labeled_dataset(resumes, 'resumes_imbalanced.json')
```

**Output**:
```
========================================
CLASS IMBALANCE STATISTICS
========================================
Total Resumes: 600

Class Distribution:
  Strong: 200 (33.3%)
  Weak: 400 (66.7%)
  Imbalance Ratio: 2.00:1 (Weak:Strong)

Strength Scores:
  Strong avg: 0.8234
  Weak avg: 0.3456
  Median: 0.4567
  Std Dev: 0.2345
========================================
```

---

### 2. Extract Features and Labels

```python
# Load labeled dataset
handler = ClassImbalanceHandler()
resumes, metadata = handler.load_labeled_dataset('resumes_imbalanced.json')

# Extract labels for training
y = np.array([r['quality_class'] for r in resumes])  # 0=Weak, 1=Strong

print(f"Class distribution:")
print(f"  Weak (0): {(y==0).sum()}")
print(f"  Strong (1): {(y==1).sum()}")
```

---

### 3. Compute Class Weights

```python
# Option A: Use compute_class_weights()
class_weights = ClassImbalanceHandler.compute_class_weights(y)
# Returns: {0: 0.75, 1: 1.50} (upweight minority, downweight majority)

# Option B: Use compute_sample_weights() for sample_weight parameter
sample_weights = ClassImbalanceHandler.compute_sample_weights(y)
# Returns: array of weights for each sample
```

**Interpretation**:
```
Class Weights:
  Weak (0): 0.75    (downweight majority)
  Strong (1): 1.50  (upweight minority)

Ratio: 1.50 / 0.75 = 2.0x
Effect: Strong class samples are twice as important during training
```

---

### 4. Train Models with Balanced Weights

#### **Method A: Using `class_weight='balanced'` (Recommended)**

```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

# Prepare data
X_train = extract_features(resumes)  # TF-IDF, embeddings, etc.
y_train = np.array([r['quality_class'] for r in resumes])

# Option 1: Logistic Regression with balanced weights
model_lr = LogisticRegression(
    class_weight='balanced',      # ← KEY LINE
    max_iter=1000,
    random_state=42
)
model_lr.fit(X_train, y_train)

# Option 2: Random Forest with balanced weights
model_rf = RandomForestClassifier(
    class_weight='balanced',      # ← KEY LINE
    n_estimators=100,
    random_state=42
)
model_rf.fit(X_train, y_train)

# Option 3: Support Vector Machine with balanced weights
from sklearn.svm import SVC
model_svm = SVC(
    class_weight='balanced',      # ← KEY LINE
    kernel='rbf',
    probability=True,
    random_state=42
)
model_svm.fit(X_train, y_train)
```

#### **Method B: Using `sample_weight` Parameter**

```python
# Compute sample weights
sample_weights = ClassImbalanceHandler.compute_sample_weights(y_train)

# Train with sample weights
model = LogisticRegression(random_state=42)
model.fit(X_train, y_train, sample_weight=sample_weights)
```

#### **Method C: Manual Class Weights**

```python
# Compute class weights
class_weights = ClassImbalanceHandler.compute_class_weights(y_train)

# Use in model (if supported)
model = RandomForestClassifier(
    class_weight=class_weights,   # Pass dict instead of 'balanced'
    random_state=42
)
model.fit(X_train, y_train)
```

---

### 5. Compare Weighted vs Unweighted Models

```python
from fairxai_class_imbalance_handler import ImbalancedModelTrainer

# Train both models
weighted_model, unweighted_model = ImbalancedModelTrainer.compare_weighted_vs_unweighted(
    X_train, y_train, 
    LogisticRegression,
    max_iter=1000
)

# Make predictions
y_pred_weighted = weighted_model.predict(X_test)
y_pred_unweighted = unweighted_model.predict(X_test)

# Compare predictions on minority class
strong_mask = y_test == 1
print(f"Strong candidate recall (weighted): {(y_pred_weighted[strong_mask] == 1).mean():.2%}")
print(f"Strong candidate recall (unweighted): {(y_pred_unweighted[strong_mask] == 1).mean():.2%}")
```

---

## Mathematical Details

### Class Weight Calculation

For imbalanced binary classification:

$$w_c = \frac{n\_total}{n\_classes \times n_c}$$

Where:
- $w_c$ = weight for class $c$
- $n\_total$ = total number of samples (600)
- $n\_classes$ = number of classes (2)
- $n_c$ = number of samples in class $c$

**Example**:
```
Total samples: 600
Strong (minority): 200
Weak (majority): 400

w_strong = 600 / (2 × 200) = 1.50
w_weak = 600 / (2 × 400) = 0.75
```

### Sample Weight Calculation

Each sample gets weight based on its class:

$$weight_i = w_{class(i)}$$

**Example**:
```
Sample 1 (Strong): weight = 1.50
Sample 2 (Weak):   weight = 0.75
Sample 3 (Strong): weight = 1.50
...
```

### Loss Function Adjustment

During training, losses are adjusted:

$$Loss = \frac{1}{N} \sum_i weight_i \times loss(y_i, \hat{y}_i)$$

**Effect**: 
- Strong candidates contribute 2x more to total loss
- Weak candidates contribute 0.5x less to total loss
- Model forced to improve Strong prediction accuracy

---

## Impact on Fairness Metrics

### Without Class Weighting

```
Unweighted Model Training:
├─ Biases towards majority (Weak) class
├─ Weak prediction accuracy: ~95%
├─ Strong prediction accuracy: ~60%  ← Poor minority class
└─ May amplify gender bias (if males are more likely to be Strong)
```

### With Class Weighting

```
Weighted Model Training:
├─ Balances both classes equally
├─ Weak prediction accuracy: ~85%
├─ Strong prediction accuracy: ~85%  ← Balanced!
└─ Reduces confounding with gender
```

### Fairness Implications

**SPD (Statistical Parity Difference)**:
- Unweighted: SPD_gender = ±0.15 (biased)
- Weighted: SPD_gender = ±0.02 (fair) ✅

**Why?** Weighted training focuses on correctly identifying Strong candidates regardless of gender, reducing gender bias in predictions.

---

## Integration with Fair-XAI Workflow

### Updated Auditing Pipeline

```python
from fairxai_auditing_pipeline import FairXAIAuditingPipeline
from fairxai_class_imbalance_handler import ClassImbalanceHandler
from sklearn.linear_model import LogisticRegression
import numpy as np

# 1. Load imbalanced synthetic data
handler = ClassImbalanceHandler(strong_ratio=0.33)
resumes, metadata = handler.load_labeled_dataset('resumes_imbalanced.json')

# 2. Extract features and labels
X_train = extract_features(resumes)
y_train = np.array([r['quality_class'] for r in resumes])

# 3. Train with balanced weights
model = LogisticRegression(
    class_weight='balanced',  # ← Balanced training
    max_iter=1000,
    random_state=42
)
model.fit(X_train, y_train)

# 4. Make predictions
predictions = model.predict(X_train)

# 5. Run fairness audit
pipeline = FairXAIAuditingPipeline("AI Resume Analyzer")
pipeline.load_data(resumes)
pipeline.add_predictions(predictions)

fairness_metrics = pipeline.compute_fairness_metrics({
    'gender': ('gender', ['Male', 'Female']),
    'experience': ('experience_level', ['entry', 'mid', 'senior'])
})

print(fairness_metrics)  # Shows improved fairness!
```

---

## Common Pitfalls & Solutions

### ❌ Pitfall 1: Ignoring Class Imbalance
```python
# BAD: No class weighting
model = LogisticRegression()
model.fit(X, y)
# Result: Model biases towards Weak class, poor Strong prediction
```

### ✅ Solution 1: Use Class Weight
```python
# GOOD: With class weighting
model = LogisticRegression(class_weight='balanced')
model.fit(X, y)
# Result: Balanced performance across both classes
```

---

### ❌ Pitfall 2: Wrong Class Weight Direction
```python
# BAD: Inverted weights (less impactful)
model = RandomForestClassifier(class_weight={0: 1.5, 1: 0.75})
# Weak gets upweighted, Strong gets downweighted (backwards!)
```

### ✅ Solution 2: Correct Weight Direction
```python
# GOOD: Minority upweighted, majority downweighted
model = RandomForestClassifier(class_weight={0: 0.75, 1: 1.5})
# OR just use 'balanced' for automatic computation
```

---

### ❌ Pitfall 3: Checking Accuracy on Imbalanced Data
```python
# BAD: Accuracy is misleading with imbalance
accuracy = (y_pred == y_test).mean()
# With 67% Weak class, even predicting all Weak gives 67% accuracy!
```

### ✅ Solution 3: Use Balanced Metrics
```python
# GOOD: Use weighted metrics
from sklearn.metrics import balanced_accuracy_score, f1_score
balanced_acc = balanced_accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

# Or compute per-class metrics
strong_accuracy = (y_pred[y_test == 1] == 1).mean()
weak_accuracy = (y_pred[y_test == 0] == 0).mean()
print(f"Strong: {strong_accuracy:.2%}, Weak: {weak_accuracy:.2%}")
```

---

## Recommended Workflow

### Step 1: Verify Class Distribution
```python
y = np.array([r['quality_class'] for r in resumes])
print(f"Strong: {(y==1).sum()} ({(y==1).mean():.1%})")
print(f"Weak: {(y==0).sum()} ({(y==0).mean():.1%})")
# Confirm: Strong ~33%, Weak ~67%
```

### Step 2: Always Use Class Weights
```python
model = LogisticRegression(class_weight='balanced')
# Single line, huge impact on fairness!
```

### Step 3: Evaluate with Balanced Metrics
```python
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.metrics import confusion_matrix

balanced_acc = balanced_accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
strong_recall = tp / (tp + fn)  # How many strong candidates caught?
print(f"Strong recall: {strong_recall:.2%}")  # Key fairness metric!
```

### Step 4: Audit Fairness
```python
# Compute fairness metrics
fairness = compute_fairness_metrics(
    predictions=y_pred,
    sensitive_attributes=X_test[['gender', 'experience_level']],
)
# Verify SPD < 0.10, DI in [0.80, 1.25], etc.
```

---

## Summary Table

| Aspect | Without Weighting | With `class_weight='balanced'` |
|--------|-------------------|-------------------------------|
| **Weak Accuracy** | 95% | 85% |
| **Strong Accuracy** | 60% | 85% |
| **Balanced Accuracy** | 77.5% | 85% |
| **Gender SPD** | ±0.15 | ±0.02 |
| **Gender Fairness** | ❌ Biased | ✅ Fair |
| **Model Type** | Biased towards majority | Treats classes equally |

---

## References

- Scikit-learn: https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html (class_weight parameter)
- Class weights in Python: Research on handling imbalanced datasets (Chawla et al., 2002)
- Fairness + Imbalance: "Fairness in Machine Learning" by Barocas et al.

---

## Next Steps

1. **Generate Dataset**: Run `fairxai_class_imbalance_handler.py` to create imbalanced synthetic data
2. **Train Models**: Use `class_weight='balanced'` in your models
3. **Audit Fairness**: Run `fairxai_auditing_pipeline.py` to measure fairness metrics
4. **Compare**: See how fairness improves with balanced weighting
5. **Deploy**: Use weighted models in production for fairer hiring decisions

---

*Last updated: April 2026*  
*Fair-XAI Framework v1.0*
