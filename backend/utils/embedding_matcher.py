"""
Embedding Matcher
Uses Sentence Transformers for semantic similarity matching
Replaces traditional TF-IDF with deep learning embeddings
"""
from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import List, Dict, Tuple
import torch
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingMatcher:
    """
    Advanced semantic matching using Sentence Transformers
    Provides much better understanding than keyword-based matching
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize embedding model
        
        Args:
            model_name: Name of sentence transformer model
                - 'all-MiniLM-L6-v2': Fast, 384-dim, 22MB (RECOMMENDED)
                - 'all-mpnet-base-v2': Better quality, 768-dim, 420MB
                - 'paraphrase-MiniLM-L6-v2': Good for paraphrasing
        """
        logger.info(f"🔄 Loading embedding model: {model_name}...")
        try:
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"✅ Model '{model_name}' loaded successfully!")
            logger.info(f"   Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
        
        # Cache for embeddings (to avoid recomputation)
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_embedding(self, text: str, use_cache: bool = True) -> np.ndarray:
        """
        Generate embedding vector for text
        
        Args:
            text: Input text
            use_cache: Whether to use cached embeddings
            
        Returns:
            Numpy array of shape (embedding_dim,)
        """
        if not text or len(text.strip()) == 0:
            logger.warning("Empty text provided for embedding")
            return np.zeros(self.embedding_dim)
        
        # Check cache
        if use_cache and text in self.cache:
            self.cache_hits += 1
            return self.cache[text]
        
        self.cache_misses += 1
        
        # Generate embedding
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Cache it
            if use_cache:
                self.cache[text] = embedding
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.embedding_dim)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-100)
            
        Example:
            >>> matcher = EmbeddingMatcher()
            >>> matcher.calculate_similarity("Python developer", "Python engineer")
            92.5  # High similarity despite different words
        """
        if not text1 or not text2:
            return 0.0
        
        # Get embeddings
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        
        # Calculate cosine similarity
        similarity = util.cos_sim(emb1, emb2).item()
        
        # Convert to percentage (0-100)
        return round(similarity * 100, 2)
    
    def calculate_detailed_match(
        self, 
        resume_text: str, 
        jd_text: str
    ) -> Dict:
        """
        Comprehensive matching analysis between resume and JD
        
        Args:
            resume_text: Full resume text
            jd_text: Job description text
            
        Returns:
            {
                'overall_match': float,
                'section_scores': dict,
                'recommendation': str,
                'confidence': str
            }
        """
        # Overall similarity
        overall_score = self.calculate_similarity(resume_text, jd_text)
        
        # Extract sections for detailed analysis
        resume_sections = self._extract_sections(resume_text)
        jd_sections = self._extract_sections(jd_text)
        
        # Calculate section-wise scores
        section_scores = {}
        for section in ['skills', 'experience', 'summary']:
            if resume_sections.get(section) and jd_sections.get(section):
                section_scores[section] = self.calculate_similarity(
                    resume_sections[section],
                    jd_sections[section]
                )
            else:
                section_scores[section] = 0.0
        
        # Generate recommendation
        recommendation = self._generate_recommendation(overall_score)
        confidence = self._calculate_confidence(overall_score, section_scores)
        
        return {
            'overall_match': overall_score,
            'section_scores': section_scores,
            'recommendation': recommendation,
            'confidence': confidence
        }
    
    def calculate_skill_similarity(
        self, 
        resume_skills: List[str], 
        jd_skills: List[str],
        threshold: float = 0.70
    ) -> Dict:
        """
        Advanced skill matching using embeddings
        Understands that "Python" ≈ "Python3", "ML" ≈ "Machine Learning"
        
        Args:
            resume_skills: Skills from resume
            jd_skills: Required skills from JD
            threshold: Minimum similarity to consider a match (0.0-1.0)
            
        Returns:
            Detailed skill analysis with matched/unmatched skills
        """
        if not resume_skills or not jd_skills:
            return {
                'average_similarity': 0,
                'matched_pairs': [],
                'unmatched_jd_skills': jd_skills if jd_skills else [],
                'match_percentage': 0,
                'strong_matches': [],
                'weak_matches': [],
                'total_required': len(jd_skills) if jd_skills else 0,
                'total_matched': 0
            }
        
        logger.info(f"Matching {len(resume_skills)} resume skills vs {len(jd_skills)} JD skills")
        
        # Get embeddings for all skills
        resume_embeddings = np.array([
            self.get_embedding(skill) for skill in resume_skills
        ])
        jd_embeddings = np.array([
            self.get_embedding(skill) for skill in jd_skills
        ])
        
        # Calculate similarity matrix
        similarity_matrix = util.cos_sim(resume_embeddings, jd_embeddings)
        
        matched_pairs = []
        strong_matches = []  # >85% similarity
        weak_matches = []    # 70-85% similarity
        unmatched_jd_skills = []
        
        for jd_idx, jd_skill in enumerate(jd_skills):
            # Get best match for this JD skill
            similarities = similarity_matrix[:, jd_idx]
            max_sim = similarities.max().item()
            best_match_idx = similarities.argmax().item()
            
            if max_sim >= threshold:
                match_info = {
                    'jd_skill': jd_skill,
                    'resume_skill': resume_skills[best_match_idx],
                    'similarity': round(max_sim * 100, 2)
                }
                matched_pairs.append(match_info)
                
                # Categorize match strength
                if max_sim >= 0.85:
                    strong_matches.append(match_info)
                else:
                    weak_matches.append(match_info)
            else:
                unmatched_jd_skills.append(jd_skill)
        
        # Calculate average similarity
        avg_similarity = (
            sum(pair['similarity'] for pair in matched_pairs) / len(jd_skills)
            if jd_skills else 0
        )
        
        logger.info(f"✅ Matched: {len(matched_pairs)}/{len(jd_skills)} skills")
        
        return {
            'average_similarity': round(avg_similarity, 2),
            'matched_pairs': matched_pairs,
            'unmatched_jd_skills': unmatched_jd_skills,
            'match_percentage': round(len(matched_pairs) / len(jd_skills) * 100, 2),
            'strong_matches': strong_matches,
            'weak_matches': weak_matches,
            'total_required': len(jd_skills),
            'total_matched': len(matched_pairs)
        }
    
    def rank_resumes(
        self, 
        resumes: List[Dict], 
        jd_text: str
    ) -> List[Dict]:
        """
        Rank multiple resumes against a job description
        Perfect for HR screening
        
        Args:
            resumes: List of dicts with keys: 'id', 'text', 'name', etc.
            jd_text: Job description text
            
        Returns:
            Sorted list of resumes with match scores
        """
        logger.info(f"Ranking {len(resumes)} resumes against JD")
        
        jd_embedding = self.get_embedding(jd_text)
        
        ranked = []
        for resume in resumes:
            resume_embedding = self.get_embedding(resume.get('text', ''))
            similarity = util.cos_sim(resume_embedding, jd_embedding).item()
            score = round(similarity * 100, 2)
            
            ranked.append({
                'resume_id': resume.get('id'),
                'candidate_name': resume.get('name', 'Unknown'),
                'match_score': score,
                'recommendation': self._generate_recommendation(score),
                'resume_data': resume
            })
        
        # Sort by match score (descending)
        ranked.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add rank numbers
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
        
        logger.info(f"✅ Ranking complete. Top score: {ranked[0]['match_score']}%")
        
        return ranked
    
    def find_similar_careers(
        self, 
        resume_text: str, 
        career_options: List[str],
        top_n: int = 5
    ) -> List[Dict]:
        """
        Find careers most similar to resume content
        Useful for career recommendations
        
        Args:
            resume_text: Full resume text
            career_options: List of career titles to match against
            top_n: Number of top matches to return
            
        Returns:
            List of career matches with similarity scores
        """
        if not career_options:
            return []
        
        resume_embedding = self.get_embedding(resume_text)
        
        matches = []
        for career in career_options:
            career_embedding = self.get_embedding(career)
            similarity = util.cos_sim(resume_embedding, career_embedding).item()
            
            matches.append({
                'career': career,
                'similarity': round(similarity * 100, 2),
                'fit_level': self._get_fit_level(similarity * 100)
            })
        
        # Sort by similarity
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        return matches[:top_n]
    
    def batch_embed(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts efficiently
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of shape (num_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract different sections from resume/JD text
        Simple keyword-based extraction (can be enhanced)
        """
        text_lower = text.lower()
        sections = {}
        
        # Skills section
        if 'skill' in text_lower:
            skill_idx = text_lower.find('skill')
            sections['skills'] = text[skill_idx:min(skill_idx+800, len(text))]
        
        # Experience section
        if 'experience' in text_lower or 'work' in text_lower:
            exp_idx = text_lower.find('experience')
            if exp_idx == -1:
                exp_idx = text_lower.find('work')
            if exp_idx != -1:
                sections['experience'] = text[exp_idx:min(exp_idx+1500, len(text))]
        
        # Summary/Objective (first portion)
        sections['summary'] = text[:min(500, len(text))]
        
        return sections
    
    def _generate_recommendation(self, score: float) -> str:
        """Generate hiring recommendation based on score"""
        if score >= 85:
            return "Excellent match! Highly recommended for interview."
        elif score >= 70:
            return "Strong match. Recommended for consideration."
        elif score >= 55:
            return "Good match. Worth reviewing in detail."
        elif score >= 40:
            return "Moderate match. May be suitable with upskilling."
        else:
            return "Low match. Significant skill gaps present."
    
    def _calculate_confidence(self, overall: float, sections: Dict) -> str:
        """Calculate confidence level in the match"""
        if not sections or len(sections) < 2:
            return "Low"
        
        section_values = [v for v in sections.values() if v > 0]
        if not section_values:
            return "Low"
        
        variance = np.std(section_values)
        
        if variance < 10 and overall > 60:
            return "High"
        elif variance < 20:
            return "Medium"
        else:
            return "Low"
    
    def _get_fit_level(self, score: float) -> str:
        """Get fit level for career recommendations"""
        if score >= 80:
            return "Excellent Fit"
        elif score >= 65:
            return "Good Fit"
        elif score >= 50:
            return "Moderate Fit"
        else:
            return "Low Fit"
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': round(hit_rate, 2)
        }
    
    def clear_cache(self):
        """Clear embedding cache to free memory"""
        cache_size = len(self.cache)
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info(f"✅ Cache cleared ({cache_size} embeddings removed)")