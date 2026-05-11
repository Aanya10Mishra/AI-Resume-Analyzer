"""
FAIR-XAI Advanced Explainability Module
SHAP and LIME implementations for resume matching interpretability
Explains which resume phrases drive similarity scores

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
Author: Aanya Mishra
"""

import numpy as np
import pandas as pd
import json
import logging
from typing import Dict, List, Tuple, Optional
from sentence_transformers import SentenceTransformer, util
import warnings

# Try to import LIME
try:
    from lime.lime_text import LimeTextExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    print("[WARNING] LIME not installed. Install with: pip install lime")

# Try to import SHAP
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("[WARNING] SHAP not installed. Install with: pip install shap")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SHAPLIMEExplainer:
    """
    Combined SHAP and LIME explainability for resume-to-JD matching
    Explains which resume phrases contribute to similarity scores
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize explainability engine
        
        Args:
            model_name: Sentence transformer model to use
        """
        logger.info("🔄 Initializing SHAP-LIME Explainer...")
        
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self.lime_explainer = None
        self.results = []
        
        # Initialize LIME if available
        if LIME_AVAILABLE:
            self.lime_explainer = LimeTextExplainer(class_names=['Low Similarity', 'High Similarity'])
            logger.info("✅ LIME explainer initialized")
        else:
            logger.warning("⚠️  LIME not available")
        
        if SHAP_AVAILABLE:
            logger.info("✅ SHAP available for analysis")
        else:
            logger.warning("⚠️  SHAP not available")
    
    # ========================================================================
    # LIME IMPLEMENTATION
    # ========================================================================
    
    def explain_with_lime(self, 
                         resume_text: str, 
                         jd_text: str, 
                         num_features: int = 10) -> Dict:
        """
        Explain resume-JD similarity using LIME
        Shows which resume phrases most influence the similarity score
        
        Args:
            resume_text: Resume content
            jd_text: Job description
            num_features: Number of top phrases to explain
        
        Returns:
            Dict with LIME explanation
        """
        if not LIME_AVAILABLE:
            logger.error("LIME not available")
            return {"error": "LIME not installed"}
        
        try:
            logger.info(f"🔍 Running LIME explanation...")
            
            # Get JD embedding (fixed reference)
            jd_embedding = self.model.encode(jd_text)
            
            # Define prediction function that LIME will perturb
            def predict_similarity(texts):
                """
                Predict similarity for text variations
                Maps to [Low, High] probability space for LIME
                """
                similarities = []
                for text in texts:
                    if len(text.strip()) == 0:
                        similarities.append(0.0)
                    else:
                        text_embedding = self.model.encode(text)
                        sim = float(util.pytorch_cos_sim(text_embedding, jd_embedding).item())
                        similarities.append(sim)
                
                # Convert to probabilities [P(Low), P(High)]
                # Higher similarity = higher probability of "High" class
                prob_high = np.array(similarities).reshape(-1, 1)
                prob_low = (1 - prob_high)
                
                return np.hstack([prob_low, prob_high])
            
            # Get baseline similarity
            baseline_sim = float(util.pytorch_cos_sim(
                self.model.encode(resume_text), 
                jd_embedding
            ).item())
            
            # Run LIME
            explanation = self.lime_explainer.explain_instance(
                resume_text,
                predict_similarity,
                num_features=min(num_features, len(resume_text.split())),
                top_labels=1
            )
            
            # Extract contributions
            contributions = []
            for phrase, weight in explanation.as_list():
                contributions.append({
                    "phrase": phrase,
                    "contribution": float(weight),
                    "direction": "positive" if weight > 0 else "negative"
                })
            
            # Sort by absolute contribution
            contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)
            
            result = {
                "method": "LIME",
                "baseline_similarity": baseline_sim,
                "top_contributing_phrases": contributions[:num_features],
                "explanation_text": f"Resume similarity score: {baseline_sim:.4f}",
                "interpretation": self._interpret_lime_results(contributions)
            }
            
            logger.info(f"✅ LIME explanation complete")
            return result
            
        except Exception as e:
            logger.error(f"❌ LIME explanation failed: {e}")
            return {"error": str(e)}
    
    # ========================================================================
    # SHAP IMPLEMENTATION (Token-level)
    # ========================================================================
    
    def explain_with_shap_tokens(self,
                                resume_text: str,
                                jd_text: str) -> Dict:
        """
        Explain using token-level SHAP values
        Shows importance of each word in the resume
        
        Args:
            resume_text: Resume content
            jd_text: Job description
        
        Returns:
            Dict with SHAP token importance
        """
        if not SHAP_AVAILABLE:
            logger.error("SHAP not available")
            return {"error": "SHAP not installed"}
        
        try:
            logger.info(f"🔍 Running SHAP token explanation...")
            
            # Tokenize resume
            resume_tokens = resume_text.split()
            jd_embedding = self.model.encode(jd_text)
            
            # Define scoring function
            def score_with_tokens(token_subsets):
                """
                Score based on different token subsets
                Used by SHAP to compute importance
                """
                scores = []
                for token_list in token_subsets:
                    if len(token_list) == 0:
                        scores.append(0.0)
                    else:
                        reconstructed = " ".join(token_list)
                        text_emb = self.model.encode(reconstructed)
                        sim = float(util.pytorch_cos_sim(text_emb, jd_embedding).item())
                        scores.append(sim)
                
                return np.array(scores)
            
            # Get baseline (full resume similarity)
            baseline_sim = float(util.pytorch_cos_sim(
                self.model.encode(resume_text),
                jd_embedding
            ).item())
            
            # Simple SHAP-like analysis using ablation
            # For each token, compute importance = score_with_token - score_without_token
            token_importance = []
            
            for i, token in enumerate(resume_tokens):
                # Score without this token
                tokens_without = resume_tokens[:i] + resume_tokens[i+1:]
                text_without = " ".join(tokens_without) if tokens_without else "[empty]"
                sim_without = float(util.pytorch_cos_sim(
                    self.model.encode(text_without),
                    jd_embedding
                ).item()) if tokens_without else 0.0
                
                # Importance = difference
                importance = baseline_sim - sim_without
                
                token_importance.append({
                    "token": token,
                    "importance": float(importance),
                    "direction": "positive" if importance > 0 else "negative"
                })
            
            # Sort by importance
            token_importance.sort(key=lambda x: abs(x['importance']), reverse=True)
            
            result = {
                "method": "SHAP (Token Ablation)",
                "baseline_similarity": baseline_sim,
                "top_important_tokens": token_importance[:15],
                "positive_tokens": [t for t in token_importance if t['importance'] > 0],
                "negative_tokens": [t for t in token_importance if t['importance'] < 0],
                "interpretation": self._interpret_shap_results(token_importance)
            }
            
            logger.info(f"✅ SHAP explanation complete")
            return result
            
        except Exception as e:
            logger.error(f"❌ SHAP explanation failed: {e}")
            return {"error": str(e)}
    
    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================
    
    def _interpret_lime_results(self, contributions: List[Dict]) -> str:
        """Generate human-readable interpretation of LIME results"""
        
        if not contributions:
            return "No significant phrases identified."
        
        positive = [c for c in contributions if c['direction'] == 'positive']
        negative = [c for c in contributions if c['direction'] == 'negative']
        
        interpretation = "**LIME Interpretation:**\n"
        
        if positive:
            interpretation += f"\n✅ Phrases that INCREASE match (helping candidate):\n"
            for item in positive[:3]:
                interpretation += f"  • '{item['phrase']}' (contribution: +{item['contribution']:.3f})\n"
        
        if negative:
            interpretation += f"\n❌ Phrases that DECREASE match (hurting candidate):\n"
            for item in negative[:3]:
                interpretation += f"  • '{item['phrase']}' (contribution: {item['contribution']:.3f})\n"
        
        if not positive and not negative:
            interpretation += "No clear phrase-level patterns detected."
        
        return interpretation
    
    def _interpret_shap_results(self, token_importance: List[Dict]) -> str:
        """Generate human-readable interpretation of SHAP results"""
        
        if not token_importance:
            return "No token importance detected."
        
        interpretation = "**SHAP Token Importance:**\n"
        
        top_positive = [t for t in token_importance if t['direction'] == 'positive'][:5]
        top_negative = [t for t in token_importance if t['direction'] == 'negative'][:5]
        
        if top_positive:
            interpretation += f"\n✅ Most important positive tokens:\n"
            for item in top_positive:
                interpretation += f"  • '{item['token']}' (importance: +{item['importance']:.4f})\n"
        
        if top_negative:
            interpretation += f"\n❌ Most problematic tokens:\n"
            for item in top_negative:
                interpretation += f"  • '{item['token']}' (importance: {item['importance']:.4f})\n"
        
        return interpretation
    
    def explain_pair(self,
                    resume_text: str,
                    jd_text: str,
                    methods: List[str] = ['lime', 'shap']) -> Dict:
        """
        Comprehensive explanation of a resume-JD pair
        
        Args:
            resume_text: Resume content
            jd_text: Job description
            methods: Methods to use ['lime', 'shap', or both]
        
        Returns:
            Dict with all explanations
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"EXPLAINING RESUME-JD MATCH")
        logger.info(f"{'='*80}")
        
        result = {
            "resume_preview": resume_text[:100] + "..." if len(resume_text) > 100 else resume_text,
            "jd_preview": jd_text[:100] + "..." if len(jd_text) > 100 else jd_text,
            "explanations": {}
        }
        
        if 'lime' in methods or 'LIME' in methods:
            result["explanations"]["LIME"] = self.explain_with_lime(resume_text, jd_text)
        
        if 'shap' in methods or 'SHAP' in methods:
            result["explanations"]["SHAP"] = self.explain_with_shap_tokens(resume_text, jd_text)
        
        # Store result
        self.results.append(result)
        
        return result
    
    def save_explanations(self, filepath: str):
        """Save all explanations to JSON file"""
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"✅ Explanations saved to {filepath}")


# ============================================================================
# CONVENIENCE BATCH FUNCTION
# ============================================================================

def explain_batch(resume_jd_pairs: List[Tuple[str, str]], 
                 output_file: str = 'fairxai_shap_lime_results.json'):
    """
    Explain a batch of resume-JD pairs
    
    Args:
        resume_jd_pairs: List of (resume_text, jd_text) tuples
        output_file: Where to save results
    
    Returns:
        LimeExplainer object with results
    """
    
    explainer = SHAPLIMEExplainer()
    
    logger.info(f"\n{'='*80}")
    logger.info(f"BATCH EXPLAINING {len(resume_jd_pairs)} RESUME-JD PAIRS")
    logger.info(f"{'='*80}\n")
    
    for i, (resume, jd) in enumerate(resume_jd_pairs, 1):
        logger.info(f"\n[{i}/{len(resume_jd_pairs)}]")
        explainer.explain_pair(resume, jd)
    
    explainer.save_explanations(output_file)
    
    logger.info(f"\n✅ Batch explanation complete! Results saved to {output_file}")
    
    return explainer


if __name__ == "__main__":
    # Example usage
    sample_resume = """
    Senior Python Developer with 5+ years experience.
    Expertise in Django, FastAPI, and microservices.
    Led team of 8 engineers at tech startup.
    Published 3 papers on machine learning.
    MS Computer Science from MIT.
    """
    
    sample_jd = """
    Senior Backend Engineer - Python
    Seeking 5+ years Python development experience
    Microservices architecture expertise required
    Team leadership skills valued
    """
    
    logger.info("Running example explanation...")
    explainer = SHAPLIMEExplainer()
    result = explainer.explain_pair(sample_resume, sample_jd, methods=['lime', 'shap'])
    
    logger.info("\n" + "="*80)
    logger.info("RESULTS:")
    logger.info("="*80)
    print(json.dumps(result, indent=2))
