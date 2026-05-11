"""
Comparative Experiment Runner
Tests: TF-IDF vs Sentence Transformers vs Full Pipeline
Generates results for research paper
"""

import time
import json
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import logging

# Your imports
from backend.utils.embedding_matcher import EmbeddingMatcher
from backend.utils.tfidf_baseline import TFIDFMatcher
from sklearn.metrics import precision_recall_fscore_support

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExperimentRunner:
    """
    Runs comparative experiments for paper
    Measures: Accuracy, Speed, Fairness
    """
    
    def __init__(self, use_embeddings=True):
        """Initialize both matchers"""
        logger.info("🚀 Initializing experiment runner...")
        self.tfidf_matcher = TFIDFMatcher()
        self.use_embeddings = use_embeddings
        
        if use_embeddings:
            logger.info("📥 Loading embedding model (this may take 30 seconds on first run)...")
            try:
                self.embedding_matcher = EmbeddingMatcher('all-MiniLM-L6-v2')
                logger.info("✅ Embedding model loaded")
            except Exception as e:
                logger.warning(f"⚠️  Embedding model failed: {e}. Using TF-IDF only.")
                self.use_embeddings = False
        
        self.results = {}
        logger.info("✅ Experiment runner ready")
    
    def load_real_resumes_from_db(self, limit: int = 50) -> Tuple[List[str], List[str]]:
        """
        Load real resumes + JDs from your database
        """
        logger.info(f"📂 Loading real data from database (limit: {limit})...")
        
        # Import your database models
        from backend.models.database import Resume, JobDescription, db
        
        try:
            # Fetch resumes
            resumes = Resume.query.limit(limit).all()
            resume_texts = []
            for resume in resumes:
                parsed_data = resume.get_parsed_data()
                # Combine resume fields into one text
                text = f"{parsed_data.get('summary', '')} {' '.join(parsed_data.get('skills', []))} " \
                       f"{' '.join([exp.get('description', '') for exp in parsed_data.get('experience', [])])}"
                if text.strip():
                    resume_texts.append(text)
            
            # Fetch job descriptions
            jds = JobDescription.query.limit(limit).all()
            jd_texts = [jd.description for jd in jds if jd.description]
            
            logger.info(f"✅ Loaded {len(resume_texts)} resumes, {len(jd_texts)} JDs")
            return resume_texts, jd_texts
            
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            logger.warning("Using sample data instead...")
            return self._get_sample_data()
    
    def _get_sample_data(self) -> Tuple[List[str], List[str]]:
        """Fallback sample data"""
        resumes = [
            "Python Django REST API PostgreSQL Docker AWS experienced developer with 5 years",
            "Full stack javascript react node.js mongodb express AWS certified",
            "Java Spring Boot microservices Kubernetes Docker CI/CD pipelines",
            "Machine learning python tensorflow PyTorch data science analytics",
            "DevOps engineer kubernetes docker jenkins terraform cloud infrastructure"
        ]
        
        jds = [
            "Senior Python Developer required. Must know Django, PostgreSQL, Docker, AWS",
            "Full Stack JavaScript Engineer needed. React, Node.js, MongoDB, Express",
            "Java Backend Engineer. Spring Boot, microservices, Kubernetes, Docker",
            "ML Engineer wanted. TensorFlow, PyTorch, Python, data analysis skills",
            "DevOps Lead needed. Kubernetes, Docker, CI/CD, Terraform, Cloud"
        ]
        
        return resumes, jds
    
    def run_comparative_test(self, resumes: List[str], jds: List[str]) -> Dict:
        """
        Main experiment: Compare both methods
        """
        logger.info("\n" + "="*70)
        logger.info("RUNNING COMPARATIVE EXPERIMENT")
        logger.info("="*70 + "\n")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'resumes_count': len(resumes),
            'jds_count': len(jds),
            'methods': {}
        }
        
        # TEST 1: TF-IDF Matching
        logger.info("🔍 TEST 1: TF-IDF Baseline...")
        tfidf_results = self._test_tfidf(resumes, jds)
        results['methods']['tfidf'] = tfidf_results
        
        # TEST 2: Embeddings (Your implementation)
        if self.use_embeddings:
            logger.info("\n🔍 TEST 2: Sentence Transformers (Embeddings)...")
            embedding_results = self._test_embeddings(resumes, jds)
            results['methods']['embeddings'] = embedding_results
            
            # Comparative Analysis
            results['comparison'] = self._compare_results(tfidf_results, embedding_results)
        else:
            logger.warning("⚠️  Skipping embeddings test (model not available)")
            results['comparison'] = None
        
        return results
    
    def _test_tfidf(self, resumes: List[str], jds: List[str]) -> Dict:
        """Test TF-IDF method"""
        start_time = time.time()
        
        # Run matching
        tfidf_results = self.tfidf_matcher.batch_matching(resumes, jds)
        similarity_matrix = tfidf_results['similarity_matrix']
        
        elapsed = time.time() - start_time
        
        # Calculate metrics
        metrics = self._calculate_metrics(similarity_matrix)
        
        return {
            'method': 'TF-IDF',
            'model': 'sklearn TfidfVectorizer',
            'time_seconds': elapsed,
            'time_per_match_ms': (elapsed / (len(resumes) * len(jds))) * 1000,
            'metrics': metrics,
            'similarity_stats': {
                'mean': float(np.mean(similarity_matrix)),
                'std': float(np.std(similarity_matrix)),
                'min': float(np.min(similarity_matrix)),
                'max': float(np.max(similarity_matrix))
            }
        }
    
    def _test_embeddings(self, resumes: List[str], jds: List[str]) -> Dict:
        """Test Embedding method (your implementation)"""
        if not self.use_embeddings:
            return None
            
        start_time = time.time()
        
        try:
            # Get embeddings
            resume_embeddings = np.array([self.embedding_matcher.get_embedding(r) for r in resumes])
            jd_embeddings = np.array([self.embedding_matcher.get_embedding(jd) for jd in jds])
            
            # Calculate similarity matrix
            from sklearn.metrics.pairwise import cosine_similarity
            similarity_matrix = cosine_similarity(resume_embeddings, jd_embeddings)
            
            elapsed = time.time() - start_time
            
            # Calculate metrics
            metrics = self._calculate_metrics(similarity_matrix)
            
            return {
                'method': 'Sentence Transformers',
                'model': 'all-MiniLM-L6-v2',
                'time_seconds': elapsed,
                'time_per_match_ms': (elapsed / (len(resumes) * len(jds))) * 1000,
                'embedding_dim': self.embedding_matcher.embedding_dim,
                'metrics': metrics,
                'similarity_stats': {
                    'mean': float(np.mean(similarity_matrix)),
                    'std': float(np.std(similarity_matrix)),
                    'min': float(np.min(similarity_matrix)),
                    'max': float(np.max(similarity_matrix))
                }
            }
        except Exception as e:
            logger.error(f"❌ Embedding test failed: {e}")
            return None
    
    def _calculate_metrics(self, similarity_matrix: np.ndarray) -> Dict:
        """Calculate evaluation metrics"""
        # Assuming diagonal is gold standard (resume i matched to JD i)
        predictions = np.argmax(similarity_matrix, axis=1)
        ground_truth = np.arange(len(similarity_matrix))
        
        accuracy = np.mean(predictions == ground_truth)
        
        # Top-K accuracy
        top_3_accuracy = np.mean([np.any(np.argsort(row)[-3:] == i) 
                                  for i, row in enumerate(similarity_matrix)])
        
        return {
            'accuracy': float(accuracy),
            'top_3_accuracy': float(top_3_accuracy),
            'mean_similarity': float(np.mean(similarity_matrix)),
            'std_similarity': float(np.std(similarity_matrix))
        }
    
    def _compare_results(self, tfidf_res: Dict, embed_res: Dict) -> Dict:
        """Compare both methods"""
        
        tfidf_acc = tfidf_res['metrics']['accuracy']
        embed_acc = embed_res['metrics']['accuracy']
        accuracy_improvement = ((embed_acc - tfidf_acc) / tfidf_acc) * 100
        
        tfidf_time = tfidf_res['time_per_match_ms']
        embed_time = embed_res['time_per_match_ms']
        overhead = (embed_time / tfidf_time) - 1
        
        return {
            'accuracy_improvement_percent': accuracy_improvement,
            'embedding_accuracy_higher': embed_acc > tfidf_acc,
            'time_overhead_percent': overhead * 100,
            'speed_tradeoff': f"Embeddings are {overhead:.1%} slower but {accuracy_improvement:.1f}% more accurate"
        }
    
    def save_results(self, results: Dict, filename: str = "experiment_results.json"):
        """Save results to JSON"""
        filepath = f"c:\\Users\\Manvi\\Documents\\AI Resume Analyzer\\{filename}"
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"✅ Results saved to {filepath}")
        return filepath
    
    def print_summary(self, results: Dict):
        """Print summary of results"""
        logger.info("\n" + "="*70)
        logger.info("EXPERIMENT RESULTS SUMMARY")
        logger.info("="*70)
        
        for method_name, method_results in results['methods'].items():
            if method_results is None:
                continue
            logger.info(f"\n📊 {method_results['method']} ({method_results['model']})")
            logger.info(f"   Accuracy: {method_results['metrics']['accuracy']:.1%}")
            logger.info(f"   Top-3 Accuracy: {method_results['metrics']['top_3_accuracy']:.1%}")
            logger.info(f"   Time per match: {method_results['time_per_match_ms']:.2f}ms")
        
        if results['comparison']:
            logger.info(f"\n🎯 COMPARISON")
            logger.info(f"   {results['comparison']['speed_tradeoff']}")
        logger.info("="*70 + "\n")


# Quick run
if __name__ == "__main__":
    import sys
    
    # Check if user wants to run embeddings (slower)
    run_embeddings = '--embeddings' in sys.argv or '-e' in sys.argv
    
    runner = ExperimentRunner(use_embeddings=run_embeddings)
    
    # Load real data (or use sample)
    try:
        resumes, jds = runner.load_real_resumes_from_db(limit=30)
    except Exception as e:
        logger.warning(f"Database load failed: {e}. Using sample data...")
        resumes, jds = runner._get_sample_data()
    
    # Run experiment
    results = runner.run_comparative_test(resumes, jds)
    
    # Save and display
    runner.save_results(results)
    runner.print_summary(results)
    
    if not run_embeddings:
        logger.info("💡 TIP: Run with --embeddings flag to test Sentence Transformers:")
        logger.info("   python experiment_runner.py --embeddings")
