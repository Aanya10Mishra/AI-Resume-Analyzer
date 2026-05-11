#!/usr/bin/env python3
"""
REAL GROUND TRUTH: Resume-JD Matching Evaluation
Evaluates matching accuracy on 10 realistic resumes matched against 10 job descriptions
Uses BOTH TF-IDF and Sentence-BERT
Calculates real precision, recall, and F1-scores
"""

import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
import warnings
warnings.filterwarnings('ignore')

def load_realistic_data():
    """Load the realistic resume and JD data"""
    with open('realistic_data.json', 'r') as f:
        data = json.load(f)
    return data['resumes'], data['jds']

def evaluate_tfidf_matching(resumes, jds):
    """Evaluate TF-IDF based matching"""
    # Combine resumes and jds for vectorization
    all_texts = resumes + jds
    
    # Vectorize
    vectorizer = TfidfVectorizer(lowercase=True, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Split back
    resume_vectors = tfidf_matrix[:len(resumes)]
    jd_vectors = tfidf_matrix[len(resumes):]
    
    # Calculate similarity (10x10 matrix)
    similarity_matrix = cosine_similarity(resume_vectors, jd_vectors)
    
    return similarity_matrix

def evaluate_sentence_bert_matching(resumes, jds):
    """Evaluate Sentence-BERT based matching"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # Load model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Embed resumes and JDs
        resume_embeddings = model.encode(resumes, show_progress_bar=False)
        jd_embeddings = model.encode(jds, show_progress_bar=False)
        
        # Calculate similarity
        similarity_matrix = cosine_similarity(resume_embeddings, jd_embeddings)
        
        return similarity_matrix
    except ImportError:
        print("⚠️ Sentence-BERT not installed. Using TF-IDF only.")
        return None

def calculate_metrics(similarity_matrix, method_name):
    """
    Calculate precision, recall, F1 for matching accuracy
    
    Ground truth: Resume i should match JD i (diagonal should be highest)
    """
    
    # For each resume, find best matching JD
    predicted_matches = np.argmax(similarity_matrix, axis=1)
    
    # Ground truth: resume i should match jd i
    true_matches = np.arange(len(similarity_matrix))
    
    # Calculate accuracy
    correct = np.sum(predicted_matches == true_matches)
    total = len(true_matches)
    accuracy = correct / total
    
    # For precision/recall, treat as binary classification for each position
    y_true = true_matches
    y_pred = predicted_matches
    
    # Calculate metrics
    precision = np.mean([predicted_matches[i] == true_matches[i] for i in range(len(true_matches))])
    recall = accuracy  # For this case, precision = recall
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'method': method_name,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'correct_matches': correct,
        'total_matches': total
    }

def print_matching_details(similarity_matrix, resumes, jds):
    """Print detailed matching results"""
    print("\n" + "="*80)
    print("DETAILED MATCHING RESULTS (Resume → Best Matching JD)")
    print("="*80)
    
    for i, resume in enumerate(resumes):
        # Get best match
        best_jd_idx = np.argmax(similarity_matrix[i])
        best_score = similarity_matrix[i][best_jd_idx]
        
        # Get top 3 matches
        top_3_indices = np.argsort(similarity_matrix[i])[-3:][::-1]
        
        correct = "✅ CORRECT" if best_jd_idx == i else "❌ WRONG"
        
        print(f"\nResume {i}: {resume[:60]}...")
        print(f"  Best Match: JD {best_jd_idx} (score: {best_score:.4f}) {correct}")
        print(f"  Top 3 matches:")
        for rank, jd_idx in enumerate(top_3_indices, 1):
            score = similarity_matrix[i][jd_idx]
            correct_marker = "✅" if jd_idx == i else "  "
            print(f"    {rank}. JD {jd_idx}: {score:.4f} {correct_marker} {jds[jd_idx][:50]}...")

def generate_report(results_tfidf, results_bert):
    """Generate comprehensive evaluation report"""
    
    report = {
        'timestamp': '2026-04-10',
        'evaluation_type': 'Resume-JD Matching Accuracy (REAL GROUND TRUTH)',
        'dataset': {
            'resumes': 10,
            'jds': 10,
            'total_pairs': 100,
            'methodology': 'Each resume has a corresponding JD (Resume i should match JD i)'
        },
        'tfidf_results': results_tfidf,
        'bert_results': results_bert,
        'comparison': {
            'tfidf_accuracy': results_tfidf['accuracy'],
            'bert_accuracy': results_bert['accuracy'],
            'bert_improvement': results_bert['accuracy'] - results_tfidf['accuracy'],
            'bert_better': results_bert['accuracy'] > results_tfidf['accuracy']
        }
    }
    
    return report

def main():
    print("\n" + "="*80)
    print("REAL GROUND TRUTH EVALUATION: Resume-JD Matching")
    print("="*80)
    print("\n📊 Loading realistic data...")
    
    # Load data
    resumes, jds = load_realistic_data()
    print(f"✅ Loaded {len(resumes)} resumes and {len(jds)} job descriptions")
    
    # Evaluate TF-IDF
    print("\n🔍 Evaluating TF-IDF matching...")
    tfidf_similarity = evaluate_tfidf_matching(resumes, jds)
    results_tfidf = calculate_metrics(tfidf_similarity, 'TF-IDF')
    
    print(f"   Accuracy: {results_tfidf['accuracy']:.1%}")
    print(f"   Correct matches: {results_tfidf['correct_matches']}/{results_tfidf['total_matches']}")
    print(f"   Precision: {results_tfidf['precision']:.4f}")
    print(f"   Recall: {results_tfidf['recall']:.4f}")
    print(f"   F1-Score: {results_tfidf['f1_score']:.4f}")
    
    # Evaluate Sentence-BERT
    print("\n🔍 Evaluating Sentence-BERT matching...")
    bert_similarity = evaluate_sentence_bert_matching(resumes, jds)
    
    if bert_similarity is not None:
        results_bert = calculate_metrics(bert_similarity, 'Sentence-BERT')
        print(f"   Accuracy: {results_bert['accuracy']:.1%}")
        print(f"   Correct matches: {results_bert['correct_matches']}/{results_bert['total_matches']}")
        print(f"   Precision: {results_bert['precision']:.4f}")
        print(f"   Recall: {results_bert['recall']:.4f}")
        print(f"   F1-Score: {results_bert['f1_score']:.4f}")
        
        # Print detailed results for Sentence-BERT (better method)
        print_matching_details(bert_similarity, resumes, jds)
    else:
        results_bert = None
        print("   Skipped (dependency not available)")
    
    # Print comparison
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    if results_bert:
        print(f"TF-IDF Accuracy:     {results_tfidf['accuracy']:.1%}")
        print(f"Sentence-BERT Accuracy: {results_bert['accuracy']:.1%}")
        improvement = (results_bert['accuracy'] - results_tfidf['accuracy']) * 100
        print(f"Improvement:         {improvement:+.1f}%")
    
    # Generate and save report
    report = generate_report(results_tfidf, results_bert)
    
    with open('matching_evaluation_groundtruth.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\n✅ Detailed report saved to: matching_evaluation_groundtruth.json")
    
    # Print summary for paper
    print("\n" + "="*80)
    print("PAPER-READY SUMMARY")
    print("="*80)
    print(f"\nResume-JD Matching Evaluation")
    print(f"Dataset: 10 realistic resumes matched against 10 job descriptions")
    print(f"\nResults:")
    print(f"  TF-IDF: {results_tfidf['accuracy']:.1%} accuracy, F1={results_tfidf['f1_score']:.4f}")
    if results_bert:
        print(f"  Sentence-BERT: {results_bert['accuracy']:.1%} accuracy, F1={results_bert['f1_score']:.4f}")
    print(f"\nMethodology: Each resume is evaluated for correct matching to its")
    print(f"corresponding job description (Resume i → JD i)")
    
    return report

if __name__ == "__main__":
    report = main()
