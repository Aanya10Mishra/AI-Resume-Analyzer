"""
FAIR-XAI Lightweight LIME & SHAP Implementation
No heavy dependencies - works with existing sentence-transformers
Calculates explainability without sklearn/pandas conflicts

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
Author: Aanya Mishra
"""

import json
import logging
from typing import Dict, List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer, util

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightweightLIMEExplainer:
    """
    Lightweight LIME implementation - no sklearn dependency
    Explains which resume phrases drive similarity scores
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize with Sentence Transformer"""
        logger.info(f"[*] Initializing LIME Explainer with {model_name}...")
        self.model = SentenceTransformer(model_name)
        model_name_clean = model_name
        logger.info(f"[OK] Model loaded: {model_name_clean}")
    
    def calculate_phrase_importance(self, 
                                   resume_text: str,
                                   jd_text: str,
                                   num_features: int = 10) -> Dict:
        """
        Calculate phrase-level importance using perturbation
        
        Args:
            resume_text: Resume content
            jd_text: Job description
            num_features: Top phrases to return
        
        Returns:
            Dict with phrase importance scores
        """
        
        logger.info(f"[*] Analyzing phrase importance (LIME-style)...")
        
        # Get baseline similarity
        resume_emb = self.model.encode(resume_text)
        jd_emb = self.model.encode(jd_text)
        baseline_sim = float(util.pytorch_cos_sim(resume_emb, jd_emb).item())
        
        # Split into phrases (2-3 word chunks)
        words = resume_text.split()
        phrases = []
        
        for i in range(len(words)):
            # Single word
            phrases.append(words[i])
            # Two-word phrases
            if i < len(words) - 1:
                phrases.append(f"{words[i]} {words[i+1]}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_phrases = []
        for p in phrases:
            if p.lower() not in seen:
                unique_phrases.append(p)
                seen.add(p.lower())
        
        # Calculate importance for each phrase
        phrase_importance = []
        
        for phrase in unique_phrases[:30]:  # Limit to top 30
            # Remove phrase from resume
            resume_without = resume_text.replace(phrase, "").replace("  ", " ").strip()
            
            if not resume_without:
                importance = baseline_sim  # Removing it reduces by full amount
            else:
                without_emb = self.model.encode(resume_without)
                sim_without = float(util.pytorch_cos_sim(without_emb, jd_emb).item())
                importance = baseline_sim - sim_without
            
            if abs(importance) > 0.001:  # Filter out negligible contributions
                phrase_importance.append({
                    "phrase": phrase,
                    "importance": float(importance),
                    "direction": "positive" if importance > 0 else "negative"
                })
        
        # Sort by absolute importance
        phrase_importance.sort(key=lambda x: abs(x['importance']), reverse=True)
        
        return {
            "method": "Lightweight LIME (Perturbation-based)",
            "baseline_similarity": baseline_sim,
            "top_contributing_phrases": phrase_importance[:num_features],
            "positive_phrases": [p for p in phrase_importance if p['direction'] == 'positive'][:5],
            "negative_phrases": [p for p in phrase_importance if p['direction'] == 'negative'][:5]
        }
    
    def calculate_token_importance(self,
                                  resume_text: str,
                                  jd_text: str) -> Dict:
        """
        Calculate token-level importance (SHAP-style ablation)
        
        Args:
            resume_text: Resume content
            jd_text: Job description
        
        Returns:
            Dict with token importance scores
        """
        
        logger.info(f"[*] Analyzing token importance (SHAP-style)...")
        
        # Get baseline
        resume_emb = self.model.encode(resume_text)
        jd_emb = self.model.encode(jd_text)
        baseline_sim = float(util.pytorch_cos_sim(resume_emb, jd_emb).item())
        
        # Split into tokens
        tokens = resume_text.split()
        
        token_importance = []
        
        for i, token in enumerate(tokens):
            # Remove this token
            tokens_without = tokens[:i] + tokens[i+1:]
            
            if not tokens_without:
                importance = baseline_sim
            else:
                text_without = " ".join(tokens_without)
                without_emb = self.model.encode(text_without)
                sim_without = float(util.pytorch_cos_sim(without_emb, jd_emb).item())
                importance = baseline_sim - sim_without
            
            token_importance.append({
                "token": token,
                "importance": float(importance),
                "direction": "positive" if importance > 0 else "negative"
            })
        
        # Sort by importance
        token_importance.sort(key=lambda x: abs(x['importance']), reverse=True)
        
        return {
            "method": "Token Ablation (SHAP-style)",
            "baseline_similarity": baseline_sim,
            "top_important_tokens": token_importance[:15],
            "positive_tokens": [t for t in token_importance if t['direction'] == 'positive'],
            "negative_tokens": [t for t in token_importance if t['direction'] == 'negative']
        }
    
    def explain_pair(self,
                    resume_text: str,
                    jd_text: str) -> Dict:
        """Full explanation of a resume-JD pair"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"EXPLAINING RESUME-JD SIMILARITY")
        logger.info(f"{'='*80}")
        
        # Get both explanations
        lime_result = self.calculate_phrase_importance(resume_text, jd_text)
        shap_result = self.calculate_token_importance(resume_text, jd_text)
        
        # Combine results
        result = {
            "explanations": {
                "LIME": lime_result,
                "SHAP": shap_result
            },
            "resume_preview": resume_text[:80] + "...",
            "jd_preview": jd_text[:80] + "..."
        }
        
        logger.info(f"\n[OK] Explanation complete!")
        logger.info(f"     LIME baseline similarity: {lime_result['baseline_similarity']:.4f}")
        logger.info(f"     SHAP baseline similarity: {shap_result['baseline_similarity']:.4f}")
        
        if lime_result['top_contributing_phrases']:
            top_phrase = lime_result['top_contributing_phrases'][0]
            logger.info(f"     Top LIME phrase: '{top_phrase['phrase']}' ({top_phrase['importance']:+.4f})")
        
        if shap_result['top_important_tokens']:
            top_token = shap_result['top_important_tokens'][0]
            logger.info(f"     Top SHAP token: '{top_token['token']}' ({top_token['importance']:+.4f})")
        
        return result


# ============================================================================
# ANALYSIS RUNNER
# ============================================================================

def analyze_resume_jd_pairs():
    """Run analysis on sample pairs"""
    
    logger.info("\n" + "="*80)
    logger.info("FAIR-XAI LIGHTWEIGHT LIMA & SHAP ANALYSIS")
    logger.info("="*80)
    
    # Sample pairs
    pairs = [
        # PAIR 1: Strong match
        (
            "Senior Python Developer. 5+ years Django FastAPI microservices. Kubernetes Docker. Led team of developers. BS Computer Science from top university.",
            "Senior Backend Engineer. 5+ years Python required. Microservices architecture. Team leadership valued."
        ),
        
        # PAIR 2: Moderate match
        (
            "Data Scientist. 3 years Python SQL machine learning. TensorFlow scikit-learn. Undergraduate Mathematics. AWS experience.",
            "Machine Learning Engineer. 5+ years Python required. TensorFlow PyTorch expertise. Advanced statistics knowledge."
        ),
        
        # PAIR 3: Weak match  
        (
            "Java Developer. 4 years Spring Boot development. Database design optimization. BS Information Technology from regional college.",
            "Senior Frontend React Developer. 5+ years React.js required. Node.js TypeScript expertise essential."
        ),
        
        # PAIR 4: Institutional Bias - Tier 1
        (
            "Full Stack Engineer. 4+ years JavaScript React Node.js. Database design scaling. MS from MIT Stanford Berkeley.",
            "Full Stack JavaScript Engineer. 4+ years React Node.js required. Microservices and scaling experience."
        ),
        
        # PAIR 5: Institutional Bias - Tier 3 (same skills!)
        (
            "Full Stack Engineer. 4+ years JavaScript React Node.js. Database design scaling. MS from Regional College.",
            "Full Stack JavaScript Engineer. 4+ years React Node.js required. Microservices and scaling experience."
        ),
    ]
    
    explainer = LightweightLIMEExplainer()
    
    results = {
        "timestamp": "2026-04-10",
        "methodology": "Lightweight LIME (Phrase Perturbation) + SHAP (Token Ablation)",
        "total_pairs": len(pairs),
        "model": "Sentence Transformers (all-MiniLM-L6-v2)",
        "pairs": []
    }
    
    for i, (resume, jd) in enumerate(pairs, 1):
        logger.info(f"\n[{i}/{len(pairs)}]")
        result = explainer.explain_pair(resume, jd)
        result['pair_number'] = i
        results['pairs'].append(result)
    
    # Save results
    output_file = 'fairxai_lightweight_shap_lime_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n\nRESULTS SAVED: {output_file}")
    
    return results


def analyze_institutional_bias():
    """Specific institutional bias analysis"""
    
    logger.info("\n" + "="*80)
    logger.info("INSTITUTIONAL BIAS - SHAP/LIME ANALYSIS")
    logger.info("="*80 + "\n")
    
    explainer = LightweightLIMEExplainer()
    
    jd = "Full Stack JavaScript Engineer. 4+ years React Node.js required. Microservices scaling experience."
    
    resume_tier1 = "Full Stack Engineer. 4+ years JavaScript React Node.js. Database design scaling. MS from MIT Stanford Berkeley."
    resume_tier3 = "Full Stack Engineer. 4+ years JavaScript React Node.js. Database design scaling. MS from Regional College."
    
    result_tier1 = explainer.explain_pair(resume_tier1, jd)
    result_tier3 = explainer.explain_pair(resume_tier3, jd)
    
    # Compare
    comparison = {
        "test": "Institutional Bias",
        "description": "Same skills from different institutions",
        "results": {
            "Tier-1 (MIT/Stanford/Berkeley)": result_tier1,
            "Tier-3 (Regional College)": result_tier3
        }
    }
    
    # Calculate difference
    lime_t1 = result_tier1['explanations']['LIME']['baseline_similarity']
    lime_t3 = result_tier3['explanations']['LIME']['baseline_similarity']
    shap_t1 = result_tier1['explanations']['SHAP']['baseline_similarity']
    shap_t3 = result_tier3['explanations']['SHAP']['baseline_similarity']
    
    comparison['analysis'] = {
        "LIME": {
            "Tier-1_similarity": float(lime_t1),
            "Tier-3_similarity": float(lime_t3),
            "difference": float(lime_t1 - lime_t3),
            "bias_detected": abs(lime_t1 - lime_t3) > 0.05
        },
        "SHAP": {
            "Tier-1_similarity": float(shap_t1),
            "Tier-3_similarity": float(shap_t3),
            "difference": float(shap_t1 - shap_t3),
            "bias_detected": abs(shap_t1 - shap_t3) > 0.05
        }
    }
    
    # Save
    with open('fairxai_institutional_bias_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n{'='*80}")
    logger.info("BIAS ANALYSIS SUMMARY")
    logger.info(f"{'='*80}\n")
    
    print(f"LIME Similarities:")
    print(f"  Tier-1: {lime_t1:.4f}")
    print(f"  Tier-3: {lime_t3:.4f}")
    print(f"  Difference: {lime_t1 - lime_t3:.4f}")
    print(f"  Bias Detected: {'YES' if abs(lime_t1 - lime_t3) > 0.05 else 'NO'}")
    
    print(f"\nSHAP Similarities:")
    print(f"  Tier-1: {shap_t1:.4f}")
    print(f"  Tier-3: {shap_t3:.4f}")
    print(f"  Difference: {shap_t1 - shap_t3:.4f}")
    print(f"  Bias Detected: {'YES' if abs(shap_t1 - shap_t3) > 0.05 else 'NO'}")
    
    logger.info(f"\n[OK] Institutional bias analysis saved: fairxai_institutional_bias_analysis.json")
    
    return comparison


if __name__ == "__main__":
    
    # Run analysis
    results = analyze_resume_jd_pairs()
    
    # Run bias test
    bias_results = analyze_institutional_bias()
    
    logger.info(f"\n{'='*80}")
    logger.info("ALL ANALYSES COMPLETE")
    logger.info(f"{'='*80}\n")
    logger.info("Output files:")
    logger.info("  1. fairxai_lightweight_shap_lime_results.json")
    logger.info("  2. fairxai_institutional_bias_analysis.json")
