"""
Large Scale Experiment - 50 resumes × 50 JDs
Generates REAL results for research paper
"""

import json
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_large_scale_experiment():
    """Run realistic experiment on 50x50 dataset"""
    
    logger.info("📂 Loading large dataset...")
    
    try:
        with open('large_realistic_data.json') as f:
            data = json.load(f)
        resumes = data['resumes']
        jds = data['jds']
    except FileNotFoundError:
        logger.error("❌ large_realistic_data.json not found")
        logger.info("Run: python create_large_dataset.py")
        return
    
    logger.info(f"✅ Loaded {len(resumes)} resumes, {len(jds)} JDs")
    logger.info(f"📊 Total pairs to evaluate: {len(resumes) * len(jds):,}\n")
    
    # ==================== TEST 1: TF-IDF ====================
    logger.info("🔍 TEST 1: TF-IDF Baseline")
    logger.info("-" * 60)
    
    start = time.time()
    
    vectorizer = TfidfVectorizer(
        max_features=10000, 
        stop_words='english', 
        ngram_range=(1, 2),
        min_df=1,
        max_df=0.9
    )
    
    logger.info("Vectorizing texts...")
    tfidf_vectors = vectorizer.fit_transform(resumes + jds)
    resume_vecs = tfidf_vectors[:len(resumes)]
    jd_vecs = tfidf_vectors[len(resumes):]
    
    logger.info("Computing similarities...")
    tfidf_similarities = cosine_similarity(resume_vecs, jd_vecs)
    
    tfidf_time = time.time() - start
    
    # Metrics
    tfidf_rankings = np.argsort(-tfidf_similarities, axis=1)
    tfidf_top1_correct = np.sum(tfidf_rankings[:, 0] == np.arange(len(resumes)) % len(jds))
    tfidf_top5_correct = sum(1 for i, ranking in enumerate(tfidf_rankings) 
                              if (i % len(jds)) in ranking[:5])
    
    logger.info(f"✅ Top-1 Accuracy: {tfidf_top1_correct}/{len(resumes)} = {tfidf_top1_correct/len(resumes)*100:.1f}%")
    logger.info(f"✅ Top-5 Accuracy: {tfidf_top5_correct}/{len(resumes)} = {tfidf_top5_correct/len(resumes)*100:.1f}%")
    logger.info(f"✅ Mean Similarity: {np.mean(tfidf_similarities):.3f}")
    logger.info(f"✅ Processing Time: {tfidf_time:.2f}s")
    
    # ==================== TEST 2: Embeddings ====================
    logger.info("\n🔍 TEST 2: Sentence Transformers")
    logger.info("-" * 60)
    
    logger.info("Loading model...")
    start = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    logger.info("Encoding resumes (this may take a minute)...")
    resume_embeddings = model.encode(resumes, show_progress_bar=True, batch_size=32)
    
    logger.info("Encoding JDs...")
    jd_embeddings = model.encode(jds, show_progress_bar=True, batch_size=32)
    
    logger.info("Computing similarities...")
    embed_similarities = cosine_similarity(resume_embeddings, jd_embeddings)
    
    embed_time = time.time() - start
    
    # Metrics
    embed_rankings = np.argsort(-embed_similarities, axis=1)
    embed_top1_correct = np.sum(embed_rankings[:, 0] == np.arange(len(resumes)) % len(jds))
    embed_top5_correct = sum(1 for i, ranking in enumerate(embed_rankings) 
                              if (i % len(jds)) in ranking[:5])
    
    logger.info(f"✅ Top-1 Accuracy: {embed_top1_correct}/{len(resumes)} = {embed_top1_correct/len(resumes)*100:.1f}%")
    logger.info(f"✅ Top-5 Accuracy: {embed_top5_correct}/{len(resumes)} = {embed_top5_correct/len(resumes)*100:.1f}%")
    logger.info(f"✅ Mean Similarity: {np.mean(embed_similarities):.3f}")
    logger.info(f"✅ Processing Time: {embed_time:.2f}s")
    
    # ==================== COMPARISON ====================
    logger.info("\n" + "="*60)
    logger.info("FINAL RESULTS & COMPARISON")
    logger.info("="*60)
    
    tfidf_top1_acc = tfidf_top1_correct / len(resumes) * 100
    embed_top1_acc = embed_top1_correct / len(resumes) * 100
    
    tfidf_top5_acc = tfidf_top5_correct / len(resumes) * 100
    embed_top5_acc = embed_top5_correct / len(resumes) * 100
    
    tfidf_mean = np.mean(tfidf_similarities)
    embed_mean = np.mean(embed_similarities)
    
    sim_improvement = ((embed_mean - tfidf_mean) / tfidf_mean) * 100
    
    logger.info(f"\n📊 Top-1 Accuracy (best match):")
    logger.info(f"   TF-IDF:     {tfidf_top1_acc:.1f}%")
    logger.info(f"   Embeddings: {embed_top1_acc:.1f}%")
    logger.info(f"   Improvement: +{(embed_top1_acc - tfidf_top1_acc):.1f}%")
    
    logger.info(f"\n📊 Top-5 Accuracy (top 5 matches):")
    logger.info(f"   TF-IDF:     {tfidf_top5_acc:.1f}%")
    logger.info(f"   Embeddings: {embed_top5_acc:.1f}%")
    logger.info(f"   Improvement: +{(embed_top5_acc - tfidf_top5_acc):.1f}%")
    
    logger.info(f"\n📊 Mean Similarity Scores:")
    logger.info(f"   TF-IDF:     {tfidf_mean:.4f}")
    logger.info(f"   Embeddings: {embed_mean:.4f}")
    logger.info(f"   Improvement: +{sim_improvement:.1f}%")
    
    logger.info(f"\n⚡ Processing Speed:")
    logger.info(f"   TF-IDF:     {tfidf_time:.2f}s")
    logger.info(f"   Embeddings: {embed_time:.2f}s")
    logger.info(f"   Overhead:   {embed_time/tfidf_time:.1f}x slower")
    
    # Distribution analysis
    logger.info(f"\n📈 Similarity Score Distribution:")
    logger.info(f"   TF-IDF  - Min: {np.min(tfidf_similarities):.3f}, Max: {np.max(tfidf_similarities):.3f}, Std: {np.std(tfidf_similarities):.3f}")
    logger.info(f"   Embed   - Min: {np.min(embed_similarities):.3f}, Max: {np.max(embed_similarities):.3f}, Std: {np.std(embed_similarities):.3f}")
    
    # Save results for paper
    results = {
        'experiment_info': {
            'dataset_size': {
                'resumes': len(resumes),
                'jds': len(jds),
                'total_pairs': len(resumes) * len(jds)
            },
            'date': time.strftime('%Y-%m-%d %H:%M:%S')
        },
        'tfidf': {
            'method': 'TF-IDF Baseline',
            'model': 'sklearn TfidfVectorizer',
            'top1_accuracy': float(tfidf_top1_acc),
            'top5_accuracy': float(tfidf_top5_acc),
            'mean_similarity': float(tfidf_mean),
            'max_similarity': float(np.max(tfidf_similarities)),
            'min_similarity': float(np.min(tfidf_similarities)),
            'std_similarity': float(np.std(tfidf_similarities)),
            'processing_time_seconds': float(tfidf_time)
        },
        'embeddings': {
            'method': 'Sentence Transformers',
            'model': 'all-MiniLM-L6-v2',
            'embedding_dimension': 384,
            'top1_accuracy': float(embed_top1_acc),
            'top5_accuracy': float(embed_top5_acc),
            'mean_similarity': float(embed_mean),
            'max_similarity': float(np.max(embed_similarities)),
            'min_similarity': float(np.min(embed_similarities)),
            'std_similarity': float(np.std(embed_similarities)),
            'processing_time_seconds': float(embed_time)
        },
        'comparison': {
            'similarity_improvement_percent': float(sim_improvement),
            'top1_accuracy_improvement': float(embed_top1_acc - tfidf_top1_acc),
            'top5_accuracy_improvement': float(embed_top5_acc - tfidf_top5_acc),
            'speed_overhead_multiplier': float(embed_time / tfidf_time),
            'key_finding': f"Sentence Transformers achieve {sim_improvement:.1f}% higher mean similarity scores with {embed_time/tfidf_time:.1f}x processing overhead"
        }
    }
    
    with open('final_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n✅✅✅ Results saved to final_results.json")
    logger.info(f"    Use these numbers in your PAPER!")

if __name__ == "__main__":
    run_large_scale_experiment()
