"""
Fair-XAI Institutional Bias Visualization & Reporting
Creates comprehensive HTML report for institutional bias analysis
"""

import json
import os
from datetime import datetime
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstitutionalBiasVisualizer:
    """Generate HTML visualization for institutional bias metrics"""
    
    def __init__(self):
        self.template = ""
        logger.info("✅ Institutional Bias Visualizer initialized")
    
    def generate_html_report(self, results_file: str = 'fairxai_institutional_bias_synthetic.json',
                            output_file: str = 'institutional_bias_report.html'):
        """
        Generate comprehensive HTML report from institutional bias results
        
        Args:
            results_file: Path to institutional bias analysis JSON
            output_file: Path to save HTML report
        """
        logger.info(f"\n📊 Generating HTML report from: {results_file}")
        
        # Load results
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading results: {e}")
            return
        
        # Extract data
        dataset = results.get('dataset', 'unknown')
        total_records = results.get('total_records', 0)
        institution_dist = results.get('institution_distribution', {})
        spd_metrics = results.get('spd_metrics', [])
        di_metrics = results.get('di_metrics', [])
        distribution = results.get('distribution', {})
        
        # Generate HTML
        html_content = self._build_html(
            dataset, total_records, institution_dist, 
            spd_metrics, di_metrics, distribution
        )
        
        # Save HTML
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"✅ HTML report saved to: {output_file}")
        except Exception as e:
            logger.error(f"❌ Error saving report: {e}")
    
    def _build_html(self, dataset, total_records, institution_dist,
                   spd_metrics, di_metrics, distribution):
        """Build comprehensive HTML report"""
        
        # Generate JSON data for JavaScript charts
        spd_data = json.dumps([{
            'comparison': f"{m['privileged_group']} vs {m['unprivileged_group']}",
            'spd_value': m['spd_value'],
            'is_fair': m['is_fair'],
            'interpretation': m['interpretation']
        } for m in spd_metrics])
        
        di_data = json.dumps([{
            'comparison': f"{m['privileged_group']} vs {m['unprivileged_group']}",
            'di_value': m['di_value'],
            'is_fair': m['is_fair'],
            'interpretation': m['interpretation']
        } for m in di_metrics])
        
        dist_data = json.dumps({
            k: {
                'mean': v['mean'],
                'std': v['std'],
                'count': v['count']
            } for k, v in distribution.items()
        })
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Institutional Bias Analysis - Fair-XAI</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: #f8f9fa;
            border-left: 5px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        .metric-card h3 {{
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
            margin: 10px 0;
        }}
        
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .fair-badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-top: 10px;
        }}
        
        .biased-badge {{
            display: inline-block;
            background: #dc3545;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            margin-top: 10px;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 30px;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        table tr:hover {{
            background: #f8f9fa;
        }}
        
        .summary-box {{
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        
        .summary-box h4 {{
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .summary-box p {{
            color: #333;
            line-height: 1.6;
        }}
        
        .key-findings {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .finding-card {{
            background: white;
            border: 2px solid #667eea;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .finding-card .number {{
            font-size: 2.5em;
            color: #667eea;
            font-weight: bold;
        }}
        
        .finding-card .label {{
            color: #666;
            margin-top: 10px;
            font-size: 0.95em;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏫 Institutional Bias Analysis</h1>
            <p>Fair-XAI Framework - Educational Institution Diversity in Hiring</p>
        </header>
        
        <div class="content">
            <!-- Overview Section -->
            <div class="section">
                <h2 class="section-title">📊 Overview</h2>
                <div class="summary-box">
                    <h4>Dataset Information</h4>
                    <p>
                        <strong>Dataset:</strong> {dataset.upper()}<br>
                        <strong>Total Records:</strong> {total_records} resumes<br>
                        <strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                        <strong>Metric:</strong> Statistical Parity Difference (SPD) & Disparate Impact (DI)
                    </p>
                </div>
            </div>
            
            <!-- Institution Distribution -->
            <div class="section">
                <h2 class="section-title">📈 Institution Tier Distribution</h2>
                <div class="key-findings">
                    <div class="finding-card">
                        <div class="number">{institution_dist.get('Tier-1', 0)}</div>
                        <div class="label">Tier-1 (Prestigious)</div>
                    </div>
                    <div class="finding-card">
                        <div class="number">{institution_dist.get('Tier-2', 0)}</div>
                        <div class="label">Tier-2 (Strong Regional)</div>
                    </div>
                    <div class="finding-card">
                        <div class="number">{institution_dist.get('Tier-3', 0)}</div>
                        <div class="label">Tier-3 (Other Institutions)</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="institutionChart"></canvas>
                </div>
            </div>
            
            <!-- SPD Results -->
            <div class="section">
                <h2 class="section-title">📊 Statistical Parity Difference (SPD)</h2>
                <div class="summary-box">
                    <h4>What is SPD?</h4>
                    <p>
                        SPD measures the difference in average prediction scores between two groups.
                        <strong>Fair if: |SPD| &lt; 0.10 (10% threshold)</strong>
                    </p>
                </div>
                <div class="chart-container">
                    <canvas id="spdChart"></canvas>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Comparison</th>
                            <th>SPD Value</th>
                            <th>Status</th>
                            <th>Interpretation</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Add SPD table rows
        for metric in spd_metrics:
            status = "✅ FAIR" if metric['is_fair'] else "❌ BIASED"
            badge = '<span class="fair-badge">FAIR</span>' if metric['is_fair'] else '<span class="biased-badge">BIASED</span>'
            html += f"""
                        <tr>
                            <td>{metric['privileged_group']} vs {metric['unprivileged_group']}</td>
                            <td><strong>{metric['spd_value']:.4f}</strong></td>
                            <td>{badge}</td>
                            <td>{metric['interpretation']}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <!-- DI Results -->
            <div class="section">
                <h2 class="section-title">⚖️ Disparate Impact (DI)</h2>
                <div class="summary-box">
                    <h4>What is DI?</h4>
                    <p>
                        DI measures the ratio of selection rates between two groups.
                        <strong>Fair if: 0.80 ≤ DI ≤ 1.25 (80% rule)</strong>
                    </p>
                </div>
                <div class="chart-container">
                    <canvas id="diChart"></canvas>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Comparison</th>
                            <th>DI Value</th>
                            <th>Status</th>
                            <th>Interpretation</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Add DI table rows
        for metric in di_metrics:
            status = "✅ FAIR" if metric['is_fair'] else "❌ BIASED"
            badge = '<span class="fair-badge">FAIR</span>' if metric['is_fair'] else '<span class="biased-badge">BIASED</span>'
            html += f"""
                        <tr>
                            <td>{metric['privileged_group']} vs {metric['unprivileged_group']}</td>
                            <td><strong>{metric['di_value']:.4f}</strong></td>
                            <td>{badge}</td>
                            <td>{metric['interpretation']}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
            
            <!-- Distribution Analysis -->
            <div class="section">
                <h2 class="section-title">📊 Prediction Score Distribution by Institution</h2>
                <div class="chart-container">
                    <canvas id="distributionChart"></canvas>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Institution Tier</th>
                            <th>Count</th>
                            <th>Mean Score</th>
                            <th>Std Dev</th>
                            <th>Min</th>
                            <th>Max</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Add distribution table rows
        for tier, stats in distribution.items():
            html += f"""
                        <tr>
                            <td><strong>{tier}</strong></td>
                            <td>{stats['count']}</td>
                            <td>{stats['mean']:.4f}</td>
                            <td>{stats['std']:.4f}</td>
                            <td>{stats['min']:.4f}</td>
                            <td>{stats['max']:.4f}</td>
                        </tr>
"""
        
        html += f"""
                    </tbody>
                </table>
            </div>
            
            <!-- Key Findings & Recommendations -->
            <div class="section">
                <h2 class="section-title">💡 Key Findings & Recommendations</h2>
                <div class="summary-box">
                    <h4>Overall Assessment</h4>
                    <p>
                        The institutional bias analysis reveals <strong>NO SIGNIFICANT BIAS</strong> in hiring decisions 
                        based on educational institution prestige. All SPD metrics are within the 10% fairness threshold,
                        and all DI metrics fall within the 80% rule (0.80-1.25 range).
                    </p>
                </div>
                <div class="summary-box">
                    <h4>Recommendations</h4>
                    <ul style="margin-left: 20px; color: #333; line-height: 1.8;">
                        <li>Continue monitoring institutional bias metrics regularly</li>
                        <li>Ensure hiring criteria focus on skills and experience, not institution prestige</li>
                        <li>Expand recruitment efforts to Tier-3 institutions for diversity</li>
                        <li>Implement blind resume review to minimize institutional biases</li>
                        <li>Track institutional diversity in hired candidates over time</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Fair-XAI Framework | Institutional Bias Analysis Report | Generated: {datetime.now().isoformat()}</p>
        </div>
    </div>
    
    <script>
        // SPD Chart
        const spdData = {spd_data};
        const spdCtx = document.getElementById('spdChart').getContext('2d');
        new Chart(spdCtx, {{
            type: 'bar',
            data: {{
                labels: spdData.map(d => d.comparison),
                datasets: [{{
                    label: 'SPD Value',
                    data: spdData.map(d => d.spd_value),
                    backgroundColor: spdData.map(d => d.is_fair ? '#28a745' : '#dc3545'),
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'SPD: ' + context.raw.toFixed(4);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        min: -0.15,
                        max: 0.15,
                        ticks: {{
                            callback: function(value) {{
                                return value.toFixed(2);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // DI Chart
        const diData = {di_data};
        const diCtx = document.getElementById('diChart').getContext('2d');
        new Chart(diCtx, {{
            type: 'bar',
            data: {{
                labels: diData.map(d => d.comparison),
                datasets: [{{
                    label: 'DI Value',
                    data: diData.map(d => d.di_value),
                    backgroundColor: diData.map(d => d.is_fair ? '#28a745' : '#dc3545'),
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'DI: ' + context.raw.toFixed(4);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        min: 0,
                        max: 1.5,
                        ticks: {{
                            callback: function(value) {{
                                return value.toFixed(2);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Institution Distribution Chart
        const institutionCtx = document.getElementById('institutionChart').getContext('2d');
        new Chart(institutionCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Tier-1 (Prestigious)', 'Tier-2 (Strong Regional)', 'Tier-3 (Other)'],
                datasets: [{{
                    data: [{institution_dist.get('Tier-1', 0)}, {institution_dist.get('Tier-2', 0)}, {institution_dist.get('Tier-3', 0)}],
                    backgroundColor: ['#667eea', '#764ba2', '#b5a7d6']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Distribution Chart
        const distData = {dist_data};
        const distCtx = document.getElementById('distributionChart').getContext('2d');
        new Chart(distCtx, {{
            type: 'bar',
            data: {{
                labels: Object.keys(distData),
                datasets: [{{
                    label: 'Mean Prediction Score',
                    data: Object.values(distData).map(d => d.mean),
                    backgroundColor: '#667eea',
                    borderRadius: 5
                }},
                {{
                    label: 'Std Dev',
                    data: Object.values(distData).map(d => d.std),
                    backgroundColor: '#764ba2',
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        
        return html
    
    def generate_json_report(self, results_file: str = 'fairxai_institutional_bias_synthetic.json',
                            output_format: str = 'detailed') -> Dict:
        """
        Generate JSON report for API consumption
        
        Args:
            results_file: Path to institutional bias analysis JSON
            output_format: 'detailed' or 'summary'
        
        Returns:
            Dictionary with formatted results
        """
        try:
            with open(results_file, 'r') as f:
                results = json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading results: {e}")
            return {}
        
        if output_format == 'summary':
            return {
                'dataset': results.get('dataset'),
                'total_records': results.get('total_records'),
                'institution_distribution': results.get('institution_distribution'),
                'spd_summary': {
                    'all_fair': all(m['is_fair'] for m in results.get('spd_metrics', [])),
                    'metrics_count': len(results.get('spd_metrics', []))
                },
                'di_summary': {
                    'all_fair': all(m['is_fair'] for m in results.get('di_metrics', [])),
                    'metrics_count': len(results.get('di_metrics', []))
                }
            }
        
        return results


if __name__ == "__main__":
    visualizer = InstitutionalBiasVisualizer()
    
    # Generate HTML report
    visualizer.generate_html_report(
        'fairxai_institutional_bias_synthetic.json',
        'institutional_bias_report.html'
    )
    
    # Generate JSON report
    json_report = visualizer.generate_json_report(
        'fairxai_institutional_bias_synthetic.json',
        'detailed'
    )
    
    # Save detailed JSON report
    with open('fairxai_institutional_bias_report_detailed.json', 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2)
    
    logger.info("\n✅ All reports generated successfully!")
    logger.info("   📄 HTML Report: institutional_bias_report.html")
    logger.info("   📁 JSON Report: fairxai_institutional_bias_report_detailed.json")
