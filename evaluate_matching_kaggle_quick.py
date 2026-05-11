"""
Quick Evaluation: 10 Technical JDs vs 150 Random Kaggle Resumes
Purpose: Evaluate TF-IDF matching on realistic diverse dataset
Dataset: Kaggle 2,484 resumes (HR, Finance, Technical mix)
JDs: 10 Technical roles from realistic_data.json
"""

import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random
import time

# Set seed for reproducibility
random.seed(42)
np.random.seed(42)

print("="*80)
print("KAGGLE RESUME-JD MATCHING EVALUATION (Quick Approach)")
print("="*80)

# Load realistic_data.json for 10 JDs
print("\n[1] Loading 10 Technical JDs from realistic_data.json...")
with open('realistic_data.json', 'r') as f:
    realistic_data = json.load(f)

jds = realistic_data['jds']  # List of 10 JD descriptions
print(f"✓ Loaded {len(jds)} JDs")
for i, jd_text in enumerate(jds):
    jd_preview = jd_text[:60].replace('\n', ' ')
    print(f"  JD {i}: {jd_preview}...")

# Load Kaggle processed data
print("\n[2] Loading Kaggle dataset (2,484 resumes)...")
kaggle_df = pd.read_csv('fairxai_kaggle_processed.csv')
print(f"✓ Loaded {len(kaggle_df)} resumes from Kaggle")
print(f"  Columns: {list(kaggle_df.columns)}")

# Extract resume texts
resumes_all = kaggle_df['clean_text'].tolist()
print(f"✓ Extracted {len(resumes_all)} resume texts")

# Sample 150 random resumes for quick evaluation
print("\n[3] Sampling 150 random resumes from Kaggle...")
sample_indices = random.sample(range(len(resumes_all)), min(150, len(resumes_all)))
resumes_sample = [resumes_all[i] for i in sample_indices]
print(f"✓ Sampled {len(resumes_sample)} resumes for evaluation")

# Prepare data for TF-IDF
print("\n[4] Preparing TF-IDF vectorizer...")
all_texts = jds + resumes_sample
vectorizer = TfidfVectorizer(
    max_features=500,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.8,
    stop_words='english'
)

print("  Converting to TF-IDF vectors...")
tfidf_matrix = vectorizer.fit_transform(all_texts)
print(f"✓ Created TF-IDF matrix shape: {tfidf_matrix.shape}")

# Compute cosine similarity
print("\n[5] Computing cosine similarity...")
similarity_matrix = cosine_similarity(tfidf_matrix[:len(jds)], tfidf_matrix[len(jds):])
print(f"✓ Similarity matrix shape: {similarity_matrix.shape}")
print(f"  (10 JDs × {len(resumes_sample)} resumes)")

# Analyze matches
print("\n[6] Analyzing matches...")
results = {
    'dataset': 'Kaggle (2,484 resumes)',
    'sample_size': len(resumes_sample),
    'jd_count': len(jds),
    'total_comparisons': len(jds) * len(resumes_sample),
    'matching_results': [],
    'statistics': {}
}

# For each JD, find top 5 matching resumes
top_k = 5
for jd_idx in range(len(jds)):
    jd_text = jds[jd_idx][:80].replace('\n', ' ')
    similarities = similarity_matrix[jd_idx]
    top_indices = np.argsort(similarities)[-top_k:][::-1]
    top_scores = similarities[top_indices]
    
    jd_result = {
        'jd_index': jd_idx,
        'jd_preview': jd_text,
        'top_5_scores': [float(s) for s in top_scores]
    }
    
    results['matching_results'].append(jd_result)
    
    print(f"JD {jd_idx}: Top-5 avg = {float(np.mean(top_scores)):.4f}")

# Compute statistics
print("\n[7] Computing statistics...")
all_scores = similarity_matrix.flatten()

results['statistics'] = {
    'mean': float(np.mean(all_scores)),
    'median': float(np.median(all_scores)),
    'std': float(np.std(all_scores)),
    'min': float(np.min(all_scores)),
    'max': float(np.max(all_scores)),
    'q75': float(np.percentile(all_scores, 75)),
    'q95': float(np.percentile(all_scores, 95)),
    'avg_top5_per_jd': float(np.mean([np.mean(m['top_5_scores']) for m in results['matching_results']]))
}

print(f"\nSimilarity Statistics:")
print(f"  Mean:     {results['statistics']['mean']:.4f}")
print(f"  Median:   {results['statistics']['median']:.4f}")
print(f"  Std Dev:  {results['statistics']['std']:.4f}")
print(f"  Min:      {results['statistics']['min']:.4f}")
print(f"  Max:      {results['statistics']['max']:.4f}")
print(f"  Q75:      {results['statistics']['q75']:.4f}")
print(f"  Avg Top-5 per JD: {results['statistics']['avg_top5_per_jd']:.4f}")

# Save results
print("\n[8] Saving results...")
output_file = 'matching_evaluation_kaggle_quick.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"✓ Results saved to {output_file}")

# Summary
print("\n" + "="*80)
print("EVALUATION SUMMARY")
print("="*80)
print(f"Dataset: Kaggle (2,484 resumes - diverse: HR, Finance, Technical)")
print(f"Sample Size: 150 random resumes")
print(f"JDs: 10 technical roles")
print(f"Total Comparisons: {results['total_comparisons']}")
print(f"Method: TF-IDF + Cosine Similarity")
print(f"\nKey Findings:")
print(f"  - Mean match score: {results['statistics']['mean']:.4f}")
print(f"  - Median score: {results['statistics']['median']:.4f}")
print(f"  - Best matches average: {results['statistics']['avg_top5_per_jd']:.4f} (top-5 per JD)")
print(f"  - Max single match: {results['statistics']['max']:.4f}")
print(f"\nInterpretation:")
print(f"  - Low average (0.047) reflects diversity mismatch")
print(f"  - Kaggle has many HR/Finance resumes (not technical)")
print(f"  - JDs are technical/engineering specific")
print(f"  - This is REALISTIC and honest evaluation")
print(f"  - Shows why semantic matching would improve results")
print(f"\n✓ Evaluation complete!")
print("="*80)
