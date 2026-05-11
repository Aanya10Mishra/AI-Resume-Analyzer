# Institutional Bias Analysis - Quick Reference

## 📊 Key Results Summary

### Overall Status: ✅ **FAIR - NO INSTITUTIONAL BIAS**

All fairness metrics pass compliance thresholds:
- **SPD:** All values < 0.10 (fair) ✅
- **DI:** All values 0.80-1.25 (80% rule) ✅

---

## 📁 Files Generated

### Core Analysis Results
```
fairxai_institutional_bias_synthetic.json          # Complete analysis results
fairxai_institutional_bias_explainability.json     # Feature importance & drivers
fairxai_institutional_bias_report_detailed.json    # Summary for APIs
institutional_bias_report.html                     # Interactive dashboard
```

### Python Modules
```
fairxai_institutional_bias_analyzer.py             # SPD/DI computation
fairxai_institutional_bias_explainability.py       # Feature analysis
fairxai_institutional_bias_visualizer.py           # Reports & visualization
enhance_synthetic_with_institutions.py             # Data enhancement
```

### Enhanced Dataset
```
fairxai_synthetic_resumes_enhanced_institutional.json # 600 resumes with institutions
```

---

## 🚀 Quick Start

### 1. View Interactive Report
```bash
# Open in web browser
institutional_bias_report.html
```

### 2. Run Full Analysis Pipeline
```bash
# One-time: Enhance dataset
python enhance_synthetic_with_institutions.py

# Full analysis
python fairxai_institutional_bias_analyzer.py
python fairxai_institutional_bias_explainability.py
python fairxai_institutional_bias_visualizer.py
```

### 3. Access Results Programmatically
```python
import json

with open('fairxai_institutional_bias_synthetic.json', 'r') as f:
    results = json.load(f)

# Key metrics
spd_metrics = results['spd_metrics']      # Statistical Parity
di_metrics = results['di_metrics']        # Disparate Impact
distribution = results['distribution']    # Score distributions
```

---

## 📈 Key Findings at a Glance

### Institution Distribution
- **Tier-1 (Prestigious):** 123 (20.5%)
- **Tier-2 (Strong Regional):** 232 (38.7%)
- **Tier-3 (Other):** 245 (40.8%)

### Fairness Metrics
| Metric | Value | Status |
|--------|-------|--------|
| SPD (T1 vs T2) | 0.0182 | ✅ FAIR |
| SPD (T1 vs T3) | 0.0014 | ✅ FAIR |
| SPD (T2 vs T3) | -0.0168 | ✅ FAIR |
| DI (T1 vs T2) | 1.0890 | ✅ FAIR |
| DI (T1 vs T3) | 0.9769 | ✅ FAIR |
| DI (T2 vs T3) | 0.8971 | ✅ FAIR |

### Mean Prediction Scores
- **Tier-1:** 0.5376
- **Tier-2:** 0.5558 (highest)
- **Tier-3:** 0.5390
- **Difference:** 1.8% (not significant)

---

## 🔍 Fairness Thresholds

### SPD (Statistical Parity Difference)
```
Fair if:     |SPD| < 0.10 (10% difference)
Current:     All metrics < 0.02 ✅ EXCELLENT
```

### DI (Disparate Impact)
```
Fair if:     0.80 ≤ DI ≤ 1.25 (80% rule)
Current:     All metrics 0.90-1.09 ✅ EXCELLENT
```

---

## 💡 Key Insights

✅ **No Systematic Bias:** Prediction scores are consistent across institution tiers
✅ **Fair Selection:** All fairness metrics within acceptable ranges
✅ **Feature Neutrality:** Weak correlations between features and institution tier
⚠️ **Monitor Tier-2:** Slight advantage (+1.94%) but not statistically significant

---

## 🛠️ Integration Examples

### Flask API Integration
```python
@app.route('/api/fairness/institutional-bias')
def institutional_bias():
    with open('fairxai_institutional_bias_synthetic.json', 'r') as f:
        results = json.load(f)
    
    all_fair = all(m['is_fair'] for m in results['spd_metrics'] + results['di_metrics'])
    
    return jsonify({
        'status': 'fair' if all_fair else 'biased',
        'metrics': results,
        'summary': {
            'total_records': results['total_records'],
            'institution_distribution': results['institution_distribution']
        }
    })
```

### Dashboard Display
```javascript
// Load and display metrics
const results = require('./fairxai_institutional_bias_synthetic.json');
const spdMetrics = results.spd_metrics;
const diMetrics = results.di_metrics;

// Create visualization
chartData = {
    labels: spdMetrics.map(m => `${m.privileged_group} vs ${m.unprivileged_group}`),
    datasets: [{
        label: 'SPD Values',
        data: spdMetrics.map(m => m.spd_value),
        backgroundColor: spdMetrics.map(m => m.is_fair ? '#28a745' : '#dc3545')
    }]
};
```

---

## 📊 Report File Descriptions

### `fairxai_institutional_bias_synthetic.json`
Complete analysis results including:
- Institution tier distribution
- SPD metrics with p-values and effect sizes
- DI metrics with confidence intervals
- Prediction score distributions
- Timestamp and metadata

### `fairxai_institutional_bias_explainability.json`
Feature importance and drivers:
- Feature-institution correlations
- Feature importance by tier
- Bias drivers (identified risk factors)
- Prediction variance analysis
- Institutional advantage/disadvantage metrics

### `fairxai_institutional_bias_report_detailed.json`
Streamlined summary for APIs:
- Dataset information
- Institution distribution
- Metric counts
- Fairness status flags

---

## ⚙️ Institution Tier Categories

### Tier-1: Prestigious Universities (15%)
Harvard, Yale, Princeton, Stanford, MIT, Columbia, Penn, Caltech, Northwestern, Duke, University of Chicago, Cornell, Carnegie Mellon

### Tier-2: Strong Regional (35%)
UC Berkeley, Michigan, Texas, Georgia Tech, Illinois, Wisconsin, Minnesota, Purdue, NYU, Boston University, Penn State, USC

### Tier-3: Other Institutions (50%)
Regional universities, smaller colleges, specialized institutions

---

## 🔧 Customization

### Add New Institution Tier
```python
# Edit fairxai_institutional_bias_analyzer.py
TIER_1_INSTITUTIONS.add('new_university')
TIER_2_INSTITUTIONS.add('regional_university')
```

### Change Fairness Threshold
```python
# Edit class definition
SPD_THRESHOLD = 0.15  # Change from 0.10
DI_LOWER_THRESHOLD = 0.75  # Change from 0.80
```

### Analyze Different Features
```python
results = analyzer.compute_feature_importance_by_tier(target_col='your_column')
```

---

## 📞 Support & Next Steps

1. **Open HTML Report:** `institutional_bias_report.html`
2. **Read Full Guide:** `INSTITUTIONAL_BIAS_ANALYSIS.md`
3. **Check Source Code:** Python modules have detailed docstrings
4. **API Integration:** Use JSON files in your backend

---

**Last Updated:** April 9, 2026  
**Status:** ✅ Production Ready
