"""
Generate visualizations for research paper from experiment results
"""

import json
import matplotlib.pyplot as plt
import numpy as np

# Load results
with open('experiment_results.json') as f:
    results = json.load(f)

# Extract data
tfidf_acc = results['methods']['tfidf']['metrics']['accuracy'] * 100
embed_acc = results['methods']['embeddings']['metrics']['accuracy'] * 100

tfidf_time = results['methods']['tfidf']['time_per_match_ms']
embed_time = results['methods']['embeddings']['time_per_match_ms']

# Create figure with 2 subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Plot 1: Accuracy Comparison
methods = ['TF-IDF\n(Baseline)', 'Sentence\nTransformers']
accuracy = [tfidf_acc, embed_acc]
colors = ['#FF6B6B', '#4ECDC4']

bars1 = ax1.bar(methods, accuracy, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
ax1.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
ax1.set_title('Resume-Job Matching Accuracy Comparison', fontsize=13, fontweight='bold')
ax1.set_ylim([0, 105])
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels on bars
for bar, val in zip(bars1, accuracy):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

# Plot 2: Speed Comparison (log scale for better visualization)
times = [tfidf_time, embed_time]
bars2 = ax2.bar(methods, times, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
ax2.set_ylabel('Time per Match (ms)', fontsize=12, fontweight='bold')
ax2.set_title('Matching Speed Comparison', fontsize=13, fontweight='bold')
ax2.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels
for bar, val in zip(bars2, times):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.2f}ms', ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('comparison_results.png', dpi=300, bbox_inches='tight')
print("✅ Saved: comparison_results.png")

# Create Plot 3: Similarity Score Distribution
fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(12, 5))

tfidf_scores = results['methods']['tfidf']['similarity_stats']
embed_scores = results['methods']['embeddings']['similarity_stats']

# Distribution visualization
methods_dist = ['TF-IDF', 'Embeddings']
means = [tfidf_scores['mean'], embed_scores['mean']]
stds = [tfidf_scores['std'], embed_scores['std']]

x = np.arange(len(methods_dist))
bars3 = ax3.bar(x, means, yerr=stds, color=colors, alpha=0.8, 
                capsize=10, edgecolor='black', linewidth=1.5)
ax3.set_ylabel('Mean Similarity Score', fontsize=12, fontweight='bold')
ax3.set_title('Similarity Score Distribution', fontsize=13, fontweight='bold')
ax3.set_xticks(x)
ax3.set_xticklabels(methods_dist)
ax3.grid(axis='y', alpha=0.3, linestyle='--')

# Add value labels
for i, (bar, val) in enumerate(zip(bars3, means)):
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.3f}±{stds[i]:.3f}', ha='center', va='bottom', 
            fontweight='bold', fontsize=10)

# Summary metrics table
summary_text = f"""
EXPERIMENTAL SUMMARY
{'='*40}
Dataset Size:        {results['resumes_count']} resumes × {results['jds_count']} JDs
Timestamp:           {results['timestamp'][:10]}

TF-IDF Baseline:
  • Accuracy:        {tfidf_acc:.1f}%
  • Top-3 Accuracy:  {results['methods']['tfidf']['metrics']['top_3_accuracy']*100:.1f}%
  • Speed:           {tfidf_time:.2f} ms/match
  • Mean Similarity: {tfidf_scores['mean']:.3f}

Sentence Transformers:
  • Accuracy:        {embed_acc:.1f}%
  • Top-3 Accuracy:  {results['methods']['embeddings']['metrics']['top_3_accuracy']*100:.1f}%
  • Speed:           {embed_time:.2f} ms/match
  • Mean Similarity: {embed_scores['mean']:.3f}
  • Model:           all-MiniLM-L6-v2 (384-dim)

Comparison:
  • Accuracy Diff:   {(embed_acc-tfidf_acc):.1f}%
  • Speed Overhead:  {(embed_time/tfidf_time - 1)*100:.0f}%
"""

ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes,
        fontsize=10, verticalalignment='top', fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
ax4.axis('off')

plt.tight_layout()
plt.savefig('detailed_analysis.png', dpi=300, bbox_inches='tight')
print("✅ Saved: detailed_analysis.png")

print("\n📊 Visualization Summary:")
print(f"   TF-IDF:         {tfidf_acc:.1f}% accuracy, {tfidf_time:.2f}ms per match")
print(f"   Embeddings:     {embed_acc:.1f}% accuracy, {embed_time:.2f}ms per match")
print(f"   Mean similarity difference: {embed_scores['mean'] - tfidf_scores['mean']:.3f}")
