"""
Smart Experiment Runner - Shows REAL differences with better evaluation
"""

import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_realistic_experiment():
    """
    More realistic evaluation:
    - Multiple JDs that could match each resume
    - Rank all JDs for each resume
    - Check if correct ranking differs between methods
    """
    
    logger.info("📂 Loading real data...")
    
    try:
        with open('real_data.json') as f:
            data = json.load(f)
        resumes = data['resumes']
        jds = data['jds']
    except:
        logger.error("❌ real_data.json not found. Run: python extract_real_data.py")
        return
    
    if len(resumes) < 10 or len(jds) < 10:
        logger.error("❌ Not enough data. Need at least 10+ resumes and JDs")
        return
    
    logger.info(f"✅ Loaded {len(resumes)} resumes, {len(jds)} JDs")
    
    # ==================== TEST 1: TF-IDF ====================
    logger.info("\n🔍 TEST 1: TF-IDF Baseline...")
    
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1,2))
    
    # Fit on all texts
    all_texts = resumes + jds
    vectorizer.fit(all_texts)
    
    # Vectorize
    resume_vecs = vectorizer.transform(resumes)
    jd_vecs = vectorizer.transform(jds)
    
    # Similarities
    tfidf_similarities = cosine_similarity(resume_vecs, jd_vecs)
    
    # Metrics
    tfidf_rankings = np.argsort(-tfidf_similarities, axis=1)  # Sort descending
    tfidf_top1_correct = np.sum(tfidf_rankings[:, 0] == np.arange(len(resumes)) % len(jds))
    tfidf_top5_correct = sum(1 for i, ranking in enumerate(tfidf_rankings) 
                              if (i % len(jds)) in ranking[:5])
    
    logger.info(f"   Accuracy (Top-1): {tfidf_top1_correct}/{len(resumes)} = {tfidf_top1_correct/len(resumes)*100:.1f}%")
    logger.info(f"   Accuracy (Top-5): {tfidf_top5_correct}/{len(resumes)} = {tfidf_top5_correct/len(resumes)*100:.1f}%")
    logger.info(f"   Mean similarity: {np.mean(tfidf_similarities):.3f}")
    
    # ==================== TEST 2: Embeddings ====================
    logger.info("\n🔍 TEST 2: Sentence Transformers...")
    
    logger.info("   Loading model (first time: ~30 seconds)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Encode all texts
    logger.info("   Encoding resumes...")
    resume_embeddings = model.encode(resumes, show_progress_bar=True)
    
    logger.info("   Encoding JDs...")
    jd_embeddings = model.encode(jds, show_progress_bar=True)
    
    # Similarities
    embed_similarities = cosine_similarity(resume_embeddings, jd_embeddings)
    
    # Metrics
    embed_rankings = np.argsort(-embed_similarities, axis=1)
    embed_top1_correct = np.sum(embed_rankings[:, 0] == np.arange(len(resumes)) % len(jds))
    embed_top5_correct = sum(1 for i, ranking in enumerate(embed_rankings) 
                              if (i % len(jds)) in ranking[:5])
    
    logger.info(f"   Accuracy (Top-1): {embed_top1_correct}/{len(resumes)} = {embed_top1_correct/len(resumes)*100:.1f}%")
    logger.info(f"   Accuracy (Top-5): {embed_top5_correct}/{len(resumes)} = {embed_top5_correct/len(resumes)*100:.1f}%")
    logger.info(f"   Mean similarity: {np.mean(embed_similarities):.3f}")
    
    # ==================== COMPARISON ====================
    logger.info("\n" + "="*70)
    logger.info("COMPARISON SUMMARY")
    logger.info("="*70)
    
    tfidf_acc = tfidf_top1_correct / len(resumes) * 100
    embed_acc = embed_top1_correct / len(resumes) * 100
    
    logger.info(f"\nAccuracy (Top-1):")
    logger.info(f"  TF-IDF:     {tfidf_acc:.1f}%")
    logger.info(f"  Embeddings: {embed_acc:.1f}%")
    logger.info(f"  ➜ Improvement: +{(embed_acc - tfidf_acc):.1f}%")
    
    logger.info(f"\nMean Similarity Scores:")
    logger.info(f"  TF-IDF:     {np.mean(tfidf_similarities):.3f}")
    logger.info(f"  Embeddings: {np.mean(embed_similarities):.3f}")
    improvement = ((np.mean(embed_similarities) - np.mean(tfidf_similarities)) / 
                   np.mean(tfidf_similarities) * 100)
    logger.info(f"  ➜ Improvement: +{improvement:.1f}%")
    
    logger.info(f"\nTop-5 Accuracy:")
    logger.info(f"  TF-IDF:     {tfidf_top5_correct/len(resumes)*100:.1f}%")
    logger.info(f"  Embeddings: {embed_top5_correct/len(resumes)*100:.1f}%")
    
    # Save results
    results = {
        'dataset': {
            'resumes': len(resumes),
            'jds': len(jds)
        },
        'tfidf': {
            'top1_accuracy': float(tfidf_acc),
            'top5_accuracy': float(tfidf_top5_correct / len(resumes) * 100),
            'mean_similarity': float(np.mean(tfidf_similarities))
        },
        'embeddings': {
            'top1_accuracy': float(embed_acc),
            'top5_accuracy': float(embed_top5_correct / len(resumes) * 100),
            'mean_similarity': float(np.mean(embed_similarities))
        },
        'improvement': {
            'accuracy': float(embed_acc - tfidf_acc),
            'similarity': float(improvement)
        }
    }
    
    with open('realistic_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n✅ Results saved to realistic_results.json")

if __name__ == "__main__":
    run_realistic_experiment()
