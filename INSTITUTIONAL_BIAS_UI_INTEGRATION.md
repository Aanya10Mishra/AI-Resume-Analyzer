# Institutional Bias Analysis - Frontend Integration Guide

## Overview

This guide explains how to integrate institutional bias analysis results into your frontend UI/dashboard.

---

## 1. Data Sources

### JSON Report Files
```
Backend Directory: c:\Users\Manvi\Documents\AI Resume Analyzer\
Files to serve:
  - fairxai_institutional_bias_synthetic.json      (Complete results)
  - fairxai_institutional_bias_report_detailed.json (API summary)
  - fairxai_institutional_bias_explainability.json (Feature analysis)
  - institutional_bias_report.html                  (Standalone report)
```

---

## 2. API Endpoints (Flask)

### Add these routes to backend

```python
# backend/routes/fairness_routes.py

from flask import Blueprint, jsonify
import json

fairness_bp = Blueprint('fairness', __name__, url_prefix='/api/fairness')

@fairness_bp.route('/institutional-bias/summary')
def institutional_bias_summary():
    """Get institutional bias summary for dashboard"""
    try:
        with open('fairxai_institutional_bias_report_detailed.json', 'r') as f:
            data = json.load(f)
        
        return jsonify({
            'status': 'success',
            'data': {
                'dataset': data.get('dataset'),
                'total_records': data.get('total_records'),
                'institution_distribution': data.get('institution_distribution'),
                'overall_fairness': {
                    'spd_all_fair': all(m['is_fair'] for m in data.get('spd_metrics', [])),
                    'di_all_fair': all(m['is_fair'] for m in data.get('di_metrics', []))
                }
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@fairness_bp.route('/institutional-bias/detailed')
def institutional_bias_detailed():
    """Get complete institutional bias analysis"""
    try:
        with open('fairxai_institutional_bias_synthetic.json', 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@fairness_bp.route('/institutional-bias/explainability')
def institutional_bias_explainability():
    """Get feature importance and bias drivers"""
    try:
        with open('fairxai_institutional_bias_explainability.json', 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Register in app.py
app.register_blueprint(fairness_bp)
```

---

## 3. Frontend Components

### 3.1 Summary Card Component

```html
<!-- components/InstitutionalBiasSummary.html -->

<div class="bias-card">
    <h3>🏫 Institutional Bias Analysis</h3>
    <div class="metric-box">
        <span class="label">Status:</span>
        <span class="value fair-badge" id="bias-status">FAIR</span>
    </div>
    <div class="metric-box">
        <span class="label">Total Records:</span>
        <span class="value" id="total-records">600</span>
    </div>
    <div class="metric-box">
        <span class="label">SPD Fairness:</span>
        <span class="value fair-badge" id="spd-status">✅ PASS</span>
    </div>
    <div class="metric-box">
        <span class="label">DI Fairness:</span>
        <span class="value fair-badge" id="di-status">✅ PASS</span>
    </div>
</div>
```

### 3.2 Institution Distribution Chart

```html
<!-- components/InstitutionDistribution.html -->

<div class="chart-container">
    <h4>Institution Tier Distribution</h4>
    <canvas id="institutionChart"></canvas>
</div>

<script>
async function loadInstitutionChart() {
    const response = await fetch('/api/fairness/institutional-bias/summary');
    const result = await response.json();
    const dist = result.data.institution_distribution;
    
    const ctx = document.getElementById('institutionChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Tier-1', 'Tier-2', 'Tier-3'],
            datasets: [{
                data: [
                    dist['Tier-1'] || 0,
                    dist['Tier-2'] || 0,
                    dist['Tier-3'] || 0
                ],
                backgroundColor: ['#667eea', '#764ba2', '#b5a7d6']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.raw / total) * 100).toFixed(1);
                            return `${context.label}: ${context.raw} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

loadInstitutionChart();
</script>
```

### 3.3 SPD Metrics Table

```html
<!-- components/SPDMetrics.html -->

<table class="metrics-table">
    <thead>
        <tr>
            <th>Comparison</th>
            <th>SPD Value</th>
            <th>P-Value</th>
            <th>Status</th>
            <th>Interpretation</th>
        </tr>
    </thead>
    <tbody id="spd-table-body">
    </tbody>
</table>

<script>
async function loadSPDMetrics() {
    const response = await fetch('/api/fairness/institutional-bias/detailed');
    const result = await response.json();
    const tbody = document.getElementById('spd-table-body');
    
    result.spd_metrics.forEach(metric => {
        const row = `
            <tr>
                <td>${metric.privileged_group} vs ${metric.unprivileged_group}</td>
                <td><strong>${metric.spd_value.toFixed(4)}</strong></td>
                <td>${metric.p_value.toFixed(4)}</td>
                <td>${metric.is_fair ? '✅ FAIR' : '❌ BIASED'}</td>
                <td>${metric.interpretation}</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}

loadSPDMetrics();
</script>
```

### 3.4 DI Metrics Visualization

```html
<!-- components/DIMetrics.html -->

<div class="chart-container">
    <h4>Disparate Impact Analysis</h4>
    <canvas id="diChart"></canvas>
</div>

<script>
async function loadDIChart() {
    const response = await fetch('/api/fairness/institutional-bias/detailed');
    const result = await response.json();
    const diMetrics = result.di_metrics;
    
    const labels = diMetrics.map(m => `${m.privileged_group} vs ${m.unprivileged_group}`);
    const values = diMetrics.map(m => m.di_value);
    
    const ctx = document.getElementById('diChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'DI Value',
                data: values,
                backgroundColor: diMetrics.map(m => m.is_fair ? '#28a745' : '#dc3545'),
                borderRadius: 5
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    min: 0.5,
                    max: 1.5,
                    ticks: {
                        callback: v => v.toFixed(2)
                    }
                }
            }
        }
    });
}

loadDIChart();
</script>
```

### 3.5 Bias Drivers Panel

```html
<!-- components/BiasDrivers.html -->

<div class="bias-drivers-panel">
    <h4>🎯 Identified Bias Drivers</h4>
    <div id="bias-drivers-list"></div>
</div>

<script>
async function loadBiasDrivers() {
    const response = await fetch('/api/fairness/institutional-bias/explainability');
    const result = await response.json();
    const drivers = result.bias_drivers || {};
    
    const container = document.getElementById('bias-drivers-list');
    
    if (Object.keys(drivers).length === 0) {
        container.innerHTML = '<p style="color: green;">✅ <strong>No bias drivers detected</strong></p>';
    } else {
        Object.entries(drivers).forEach(([feature, info]) => {
            const html = `
                <div class="driver-card">
                    <h5>${feature}</h5>
                    <p><strong>Risk Level:</strong> <span class="${info.risk_level.toLowerCase()}">${info.risk_level}</span></p>
                    <p><strong>Correlation:</strong> ${info.correlation_with_tier.toFixed(4)}</p>
                    <p><strong>Difference Score:</strong> ${info.mean_difference_score.toFixed(4)}</p>
                </div>
            `;
            container.innerHTML += html;
        });
    }
}

loadBiasDrivers();
</script>
```

---

## 4. Complete Dashboard Widget

```html
<!-- components/InstitutionalBiasDashboard.html -->

<div class="institutional-bias-dashboard">
    <header>
        <h2>🏫 Institutional Bias Analysis Dashboard</h2>
        <p>Fair-XAI Framework - Educational Institution Diversity in Hiring</p>
    </header>
    
    <!-- Overview Section -->
    <section class="section">
        <h3>📊 Overview</h3>
        <div class="overview-cards">
            <div class="card">
                <h4>Overall Status</h4>
                <div id="overall-status" class="large-text">Loading...</div>
            </div>
            <div class="card">
                <h4>Total Records</h4>
                <div id="record-count" class="large-text">600</div>
            </div>
            <div class="card">
                <h4>SPD Fairness</h4>
                <div id="spd-fairness" class="large-text">Loading...</div>
            </div>
            <div class="card">
                <h4>DI Fairness</h4>
                <div id="di-fairness" class="large-text">Loading...</div>
            </div>
        </div>
    </section>
    
    <!-- Institution Distribution -->
    <section class="section">
        <h3>📈 Institution Distribution</h3>
        <div class="chart-container">
            <canvas id="institutionChart"></canvas>
        </div>
    </section>
    
    <!-- Metrics Tables -->
    <section class="section">
        <h3>📊 Fairness Metrics</h3>
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('spd')">SPD Metrics</button>
            <button class="tab-button" onclick="switchTab('di')">DI Metrics</button>
        </div>
        <div id="spd-section" class="tab-content active">
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Comparison</th>
                        <th>Value</th>
                        <th>Threshold</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="spd-table"></tbody>
            </table>
        </div>
        <div id="di-section" class="tab-content">
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>Comparison</th>
                        <th>Value</th>
                        <th>Range</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="di-table"></tbody>
            </table>
        </div>
    </section>
    
    <!-- Bias Drivers -->
    <section class="section">
        <h3>🎯 Bias Drivers Analysis</h3>
        <div id="bias-drivers-container"></div>
    </section>
</div>

<style>
.institutional-bias-dashboard {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    padding: 30px;
}

.section {
    margin-bottom: 40px;
}

.section h3 {
    color: #667eea;
    margin-bottom: 20px;
    font-size: 1.4em;
    border-bottom: 2px solid #667eea;
    padding-bottom: 10px;
}

.overview-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
}

.card {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #667eea;
    text-align: center;
}

.large-text {
    font-size: 2em;
    font-weight: bold;
    color: #333;
    margin-top: 10px;
}

.metrics-table {
    width: 100%;
    border-collapse: collapse;
}

.metrics-table th {
    background: #667eea;
    color: white;
    padding: 12px;
    text-align: left;
}

.metrics-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #e0e0e0;
}

.metrics-table tr:hover {
    background: #f8f9fa;
}

.chart-container {
    position: relative;
    height: 400px;
    margin: 20px 0;
}

.tabs {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.tab-button {
    padding: 10px 20px;
    background: #f0f0f0;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
}

.tab-button.active {
    background: #667eea;
    color: white;
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
}

.fair-badge {
    background: #28a745;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
}

.biased-badge {
    background: #dc3545;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
}
</style>

<script>
function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`${tab}-section`).classList.add('active');
    event.target.classList.add('active');
}

async function loadDashboard() {
    // Load summary
    const summaryResponse = await fetch('/api/fairness/institutional-bias/summary');
    const summaryData = await summaryResponse.json();
    
    // Load detailed
    const detailResponse = await fetch('/api/fairness/institutional-bias/detailed');
    const detailData = await detailResponse.json();
    
    // Load explainability
    const explainResponse = await fetch('/api/fairness/institutional-bias/explainability');
    const explainData = await explainResponse.json();
    
    // Update summary
    const summaryInfo = summaryData.data;
    document.getElementById('overall-status').textContent = 
        (summaryInfo.overall_fairness.spd_all_fair && summaryInfo.overall_fairness.di_all_fair) 
        ? '✅ FAIR' 
        : '❌ BIASED';
    document.getElementById('spd-fairness').textContent = summaryInfo.overall_fairness.spd_all_fair ? '✅ PASS' : '❌ FAIL';
    document.getElementById('di-fairness').textContent = summaryInfo.overall_fairness.di_all_fair ? '✅ PASS' : '❌ FAIL';
    
    // SPD Table
    const spdTable = document.getElementById('spd-table');
    detailData.spd_metrics.forEach(m => {
        spdTable.innerHTML += `
            <tr>
                <td>${m.privileged_group} vs ${m.unprivileged_group}</td>
                <td>${m.spd_value.toFixed(4)}</td>
                <td>&lt; 0.10</td>
                <td>${m.is_fair ? '<span class="fair-badge">FAIR</span>' : '<span class="biased-badge">BIASED</span>'}</td>
            </tr>
        `;
    });
    
    // DI Table
    const diTable = document.getElementById('di-table');
    detailData.di_metrics.forEach(m => {
        diTable.innerHTML += `
            <tr>
                <td>${m.privileged_group} vs ${m.unprivileged_group}</td>
                <td>${m.di_value.toFixed(4)}</td>
                <td>0.80 - 1.25</td>
                <td>${m.is_fair ? '<span class="fair-badge">FAIR</span>' : '<span class="biased-badge">BIASED</span>'}</td>
            </tr>
        `;
    });
    
    // Bias Drivers
    const driversContainer = document.getElementById('bias-drivers-container');
    const drivers = explainData.bias_drivers || {};
    if (Object.keys(drivers).length === 0) {
        driversContainer.innerHTML = '<p style="color: green;">✅ <strong>No significant bias drivers detected</strong></p>';
    } else {
        Object.entries(drivers).forEach(([feature, info]) => {
            driversContainer.innerHTML += `
                <div style="padding: 15px; background: #fff3cd; border-radius: 5px; margin: 10px 0;">
                    <h5>${feature}</h5>
                    <p><strong>Risk Level:</strong> ${info.risk_level}</p>
                    <p><strong>Mean Difference Score:</strong> ${info.mean_difference_score.toFixed(4)}</p>
                </div>
            `;
        });
    }
}

// Load on page ready
document.addEventListener('DOMContentLoaded', loadDashboard);
</script>
```

---

## 5. CSS Styling

```css
/* styles/institutional-bias.css */

.institutional-bias-dashboard {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    padding: 20px;
}

.section {
    background: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.fair-badge {
    background: #28a745;
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 0.9em;
    font-weight: 600;
}

.biased-badge {
    background: #dc3545;
    color: white;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 0.9em;
    font-weight: 600;
}

.chart-container {
    position: relative;
    height: 400px;
    margin: 20px 0;
}
```

---

## 6. Integration Checklist

- [ ] Copy JSON files to backend static directory
- [ ] Add fairness routes to Flask app
- [ ] Create frontend components
- [ ] Add CSS styling
- [ ] Test API endpoints
- [ ] Integrate with dashboard
- [ ] Verify data loading
- [ ] Test responsive design

---

## 7. Deployment Notes

1. **File Serving:** Serve JSON files as static assets or via API endpoints
2. **CORS:** Enable CORS if frontend and backend on different domains
3. **Caching:** Cache JSON files as they don't change frequently
4. **Update Cycle:** Re-generate reports monthly or quarterly
5. **Performance:** Large datasets may need pagination in tables

---

**Last Updated:** April 9, 2026  
**Version:** 1.0
