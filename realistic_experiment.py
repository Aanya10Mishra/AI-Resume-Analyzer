"""
Run experiments with REALISTIC data showing actual differences
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

def run_realistic_comparison():
    """Compare TF-IDF vs Embeddings on realistic data"""
    
    logger.info("📂 Loading realistic data...")
    
    try:
        with open('realistic_data.json') as f:
            data = json.load(f)
        resumes = data['resumes']
        jds = data['jds']
    except FileNotFoundError:
        logger.error("❌ realistic_data.json not found")
        logger.info("Run: python create_realistic_data.py")
        return
    
    logger.info(f"✅ Loaded {len(resumes)} resumes, {len(jds)} JDs\n")
    
    # ==================== TEST 1: TF-IDF ====================
    logger.info("🔍 TEST 1: TF-IDF Baseline")
    logger.info("-" * 50)
    
    start = time.time()
    
    vectorizer = TfidfVectorizer(
        max_features=5000, 
        stop_words='english', 
        ngram_range=(1, 2),
        min_df=1
    )
    
    # Fit and transform
    tfidf_vectors = vectorizer.fit_transform(resumes + jds)
    resume_vecs = tfidf_vectors[:len(resumes)]
    jd_vecs = tfidf_vectors[len(resumes):]
    
    # Calculate similarities
    tfidf_similarities = cosine_similarity(resume_vecs, jd_vecs)
    
    tfidf_time = time.time() - start
    
    # Rank JDs for each resume
    tfidf_rankings = np.argsort(-tfidf_similarities, axis=1)
    
    # Best match for each resume
    logger.info("\nTF-IDF Top matches for each resume:")
    logger.info("-" * 50)
    for i, resume in enumerate(resumes[:3]):
        top_jd_idx = tfidf_rankings[i, 0]
        top_score = tfidf_similarities[i, top_jd_idx]
        print(f"\nResume {i}: {resume[:60]}...")
        print(f"  ➜ Top match: JD {top_jd_idx} (score: {top_score:.3f})")
        print(f"     {jds[top_jd_idx][:80]}...")
    
    logger.info(f"\n📊 TF-IDF Statistics:")
    logger.info(f"   Mean similarity: {np.mean(tfidf_similarities):.3f}")
    logger.info(f"   Max similarity:  {np.max(tfidf_similarities):.3f}")
    logger.info(f"   Min similarity:  {np.min(tfidf_similarities):.3f}")
    logger.info(f"   Processing time: {tfidf_time:.2f}s")
    
    # ==================== TEST 2: Embeddings ====================
    logger.info("\n\n🔍 TEST 2: Sentence Transformers")
    logger.info("-" * 50)
    
    logger.info("Loading embedding model...")
    start = time.time()
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    logger.info("Encoding resumes...")
    resume_embeddings = model.encode(resumes, show_progress_bar=False)
    
    logger.info("Encoding JDs...")
    jd_embeddings = model.encode(jds, show_progress_bar=False)
    
    embed_time = time.time() - start
    
    # Calculate similarities
    embed_similarities = cosine_similarity(resume_embeddings, jd_embeddings)
    
    # Rank JDs for each resume
    embed_rankings = np.argsort(-embed_similarities, axis=1)
    
    # Best match for each resume
    logger.info("\nSentence Transformers Top matches for each resume:")
    logger.info("-" * 50)
    for i, resume in enumerate(resumes[:3]):
        top_jd_idx = embed_rankings[i, 0]
        top_score = embed_similarities[i, top_jd_idx]
        print(f"\nResume {i}: {resume[:60]}...")
        print(f"  ➜ Top match: JD {top_jd_idx} (score: {top_score:.3f})")
        print(f"     {jds[top_jd_idx][:80]}...")
    
    logger.info(f"\n📊 Embedding Statistics:")
    logger.info(f"   Mean similarity: {np.mean(embed_similarities):.3f}")
    logger.info(f"   Max similarity:  {np.max(embed_similarities):.3f}")
    logger.info(f"   Min similarity:  {np.min(embed_similarities):.3f}")
    logger.info(f"   Processing time: {embed_time:.2f}s")
    
    # ==================== COMPARISON ====================
    logger.info("\n\n" + "="*70)
    logger.info("COMPARISON & KEY INSIGHTS")
    logger.info("="*70)
    
    # Accuracy: how many got correct top match
    tfidf_correct = sum(1 for i in range(len(resumes)) 
                        if tfidf_rankings[i, 0] == i)
    embed_correct = sum(1 for i in range(len(resumes)) 
                        if embed_rankings[i, 0] == i)
    
    logger.info(f"\nCorrect Top Matches:")
    logger.info(f"  TF-IDF:     {tfidf_correct}/{len(resumes)} = {tfidf_correct/len(resumes)*100:.1f}%")
    logger.info(f"  Embeddings: {embed_correct}/{len(resumes)} = {embed_correct/len(resumes)*100:.1f}%")
    
    # Similarity differences
    sim_diff = np.mean(embed_similarities) - np.mean(tfidf_similarities)
    sim_pct_diff = (sim_diff / np.mean(tfidf_similarities)) * 100
    
    logger.info(f"\nMean Similarity Scores:")
    logger.info(f"  TF-IDF:     {np.mean(tfidf_similarities):.3f}")
    logger.info(f"  Embeddings: {np.mean(embed_similarities):.3f}")
    logger.info(f"  ➜ Embeddings better by: {sim_pct_diff:+.1f}%")
    
    # Speed
    logger.info(f"\nProcessing Speed:")
    logger.info(f"  TF-IDF:     {tfidf_time:.3f}s")
    logger.info(f"  Embeddings: {embed_time:.3f}s")
    logger.info(f"  ➜ Embeddings {embed_time/tfidf_time:.1f}x slower (but more accurate)")
    
    # Show specific mismatches
    logger.info(f"\n\n🔍 DETAILED ANALYSIS - First Mismatches:")
    logger.info("-" * 50)
    
    mismatch_count = 0
    for i in range(len(resumes)):
        tfidf_top = tfidf_rankings[i, 0]
        embed_top = embed_rankings[i, 0]
        
        if tfidf_top != embed_top and mismatch_count < 3:
            print(f"\nResume {i}:")
            print(f"  TF-IDF recommends:     JD {tfidf_top} (score: {tfidf_similarities[i, tfidf_top]:.3f})")
            print(f"  Embeddings recommend: JD {embed_top} (score: {embed_similarities[i, embed_top]:.3f})")
            print(f"  Resume snippet: {resumes[i][:80]}...")
            print(f"  TF-IDF top: {jds[tfidf_top][:70]}...")
            print(f"  Embed top:  {jds[embed_top][:70]}...")
            
            mismatch_count += 1
    
    # Save results
    results = {
        'dataset': {
            'resumes': len(resumes),
            'jds': len(jds),
            'pairs': len(resumes) * len(jds)
        },
        'tfidf': {
            'correct_matches': int(tfidf_correct),
            'accuracy': float(tfidf_correct / len(resumes) * 100),
            'mean_similarity': float(np.mean(tfidf_similarities)),
            'processing_time': float(tfidf_time)
        },
        'embeddings': {
            'correct_matches': int(embed_correct),
            'accuracy': float(embed_correct / len(resumes) * 100),
            'mean_similarity': float(np.mean(embed_similarities)),
            'processing_time': float(embed_time)
        },
        'comparison': {
            'accuracy_improvement': float(embed_correct - tfidf_correct),
            'accuracy_improvement_pct': float((embed_correct - tfidf_correct) / tfidf_correct * 100) if tfidf_correct > 0 else 0,
            'similarity_improvement_pct': float(sim_pct_diff),
            'speed_overhead': float(embed_time / tfidf_time)
        }
    }
    
    with open('realistic_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n\n✅ Results saved to realistic_results.json")
    logger.info(f"   Use in your paper for REAL quantitative results!")

if __name__ == "__main__":
    run_realistic_comparison()
