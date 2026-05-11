"""
TF-IDF Baseline for Resume-Job Matching Comparison
For research paper "Semantic Resume-Job Matching"
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TFIDFMatcher:
    """
    Traditional TF-IDF baseline for comparison with embeddings
    This is what we're proving transformers can beat!
    """
    
    def __init__(self):
        """Initialize TF-IDF vectorizer"""
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        self.resume_vectors = None
        self.jd_vectors = None
        logger.info("✅ TF-IDF Matcher initialized")
    
    def fit_on_resumes(self, resumes: List[str]):
        """Fit TF-IDF on resume corpus"""
        logger.info(f"🔧 Fitting TF-IDF on {len(resumes)} resumes...")
        self.resume_vectors = self.vectorizer.fit_transform(resumes)
        logger.info(f"✅ Vocabulary size: {len(self.vectorizer.get_feature_names_out())}")
    
    def match_resume_to_jds(self, resume_text: str, jd_texts: List[str]) -> Tuple[List[float], List[int]]:
        """
        Match resume to multiple job descriptions
        
        Returns:
            - scores: Similarity scores for each JD
            - rankings: Indices sorted by score (best first)
        """
        # Transform resume and JDs using same vectorizer
        resume_vec = self.vectorizer.transform([resume_text])
        jd_vecs = self.vectorizer.transform(jd_texts)
        
        # Calculate cosine similarity
        scores = cosine_similarity(resume_vec, jd_vecs)[0]
        rankings = np.argsort(scores)[::-1]  # Sort descending
        
        return scores, rankings
    
    def batch_matching(self, resumes: List[str], job_descriptions: List[str]) -> Dict:
        """
        Match all resumes to all job descriptions
        Used for evaluation
        """
        logger.info(f"⚙️  Running batch matching: {len(resumes)} resumes vs {len(job_descriptions)} JDs")
        
        # Vectorize resumes and JDs
        resume_vecs = self.vectorizer.fit_transform(resumes)
        jd_vecs = self.vectorizer.transform(job_descriptions)
        
        # Compute similarity matrix
        similarity_matrix = cosine_similarity(resume_vecs, jd_vecs)
        
        results = {
            'similarity_matrix': similarity_matrix,
            'resumes_count': len(resumes),
            'jds_count': len(job_descriptions),
            'mean_score': np.mean(similarity_matrix),
            'max_score': np.max(similarity_matrix),
            'min_score': np.min(similarity_matrix),
            'std_score': np.std(similarity_matrix)
        }
        
        logger.info(f"✅ Batch matching complete")
        logger.info(f"   Mean similarity: {results['mean_score']:.3f}")
        logger.info(f"   Range: {results['min_score']:.3f} - {results['max_score']:.3f}")
        
        return results


# For quick testing
if __name__ == "__main__":
    # Sample data
    resumes_sample = [
        "Python Django JavaScript TypeScript React Vue Node.js Docker Kubernetes",
        "Java Spring Boot AWS Lambda DynamoDB Microservices"
    ]
    
    jds_sample = [
        "Senior Python Developer needed. Required: Django, Flask, PostgreSQL",
        "Java Backend Engineer. Skills: Spring Boot, AWS, Docker"
    ]
    
    matcher = TFIDFMatcher()
    results = matcher.batch_matching(resumes_sample, jds_sample)
    print("Results:", results)
