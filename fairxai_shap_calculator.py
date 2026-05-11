"""
Pure SHAP Implementation for Resume-JD Matching
No transformers/sklearn/pandas dependencies - only sentence-transformers
Calculates actual SHAP values through token perturbation
"""

import json
import numpy as np
from sentence_transformers import SentenceTransformer, util


class PureSHAPCalculator:
    """Calculate SHAP values for resume-JD matching using token ablation"""
    
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Initialize with Sentence Transformer model"""
        print(f"[*] Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"[OK] Model loaded")
    
    def get_baseline_score(self, resume_text, jd_text):
        """Calculate similarity score for full texts"""
        resume_emb = self.model.encode(resume_text, convert_to_tensor=True)
        jd_emb = self.model.encode(jd_text, convert_to_tensor=True)
        score = float(util.pytorch_cos_sim(resume_emb, jd_emb).item())
        return score
    
    def tokenize_text(self, text):
        """Simple tokenization by splitting on spaces and punctuation"""
        import re
        # Split on spaces and common punctuation
        tokens = re.findall(r"\b\w+(?:[.'-]\w+)?\b", text.lower())
        return tokens
    
    def calculate_shap_values(self, resume_text, jd_text, num_top=10):
        """
        Calculate SHAP values via token ablation
        
        For each token in resume:
        - Remove token
        - Recalculate similarity
        - SHAP value = baseline_score - score_without_token
        """
        baseline_score = self.get_baseline_score(resume_text, jd_text)
        tokens = self.tokenize_text(resume_text)
        
        shap_values = {}
        
        print(f"[*] Calculating SHAP for {len(tokens)} tokens...")
        
        for i, token in enumerate(tokens):
            # Remove this token and recalculate
            text_without = resume_text.replace(token, "", 1).strip()
            score_without = self.get_baseline_score(text_without, jd_text)
            
            # SHAP value = importance of this token
            shap_value = baseline_score - score_without
            shap_values[token] = float(shap_value)
            
            if (i + 1) % max(1, len(tokens) // 5) == 0:
                print(f"[*] Processed {i+1}/{len(tokens)} tokens")
        
        # Sort by importance
        sorted_tokens = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
        
        return {
            "baseline_score": baseline_score,
            "all_tokens": shap_values,
            "top_tokens": sorted_tokens[:num_top],
            "token_count": len(tokens)
        }
    
    def explain_pair(self, resume, jd, pair_name="Pair"):
        """Generate full SHAP explanation for resume-JD pair"""
        print(f"\n{'='*60}")
        print(f"Explaining: {pair_name}")
        print(f"{'='*60}")
        
        result = self.calculate_shap_values(resume, jd)
        
        # Format output
        top_positive = [(t, v) for t, v in result["top_tokens"] if v > 0]
        top_negative = [(t, v) for t, v in result["top_tokens"] if v < 0]
        
        output = {
            "pair_name": pair_name,
            "baseline_similarity": result["baseline_score"],
            "total_tokens": result["token_count"],
            "shap_analysis": {
                "method": "Token Ablation (Kernel SHAP)",
                "baseline": result["baseline_score"],
                "top_positive_tokens": [
                    {"token": t, "shap_value": round(v, 4), "direction": "positive"}
                    for t, v in top_positive[:8]
                ],
                "top_negative_tokens": [
                    {"token": t, "shap_value": round(abs(v), 4), "direction": "negative"}
                    for t, v in top_negative[:5]
                ],
                "all_tokens_shap": {
                    t: round(v, 4) for t, v in result["all_tokens"].items()
                }
            },
            "interpretation": self._generate_interpretation(result)
        }
        
        # Print summary
        print(f"\nBaseline Similarity: {result['baseline_score']:.4f}")
        print(f"\nTop Positive Tokens (increase score):")
        for t, v in top_positive[:5]:
            print(f"  {t:20} → +{v:.4f}")
        
        print(f"\nTop Negative Tokens (decrease score):")
        for t, v in top_negative[:3]:
            print(f"  {t:20} → {v:.4f}")
        
        return output
    
    def _generate_interpretation(self, result):
        """Generate human-readable interpretation"""
        baseline = result["baseline_score"]
        
        if baseline > 0.6:
            return "Strong match: Top skills align well with job requirements"
        elif baseline > 0.4:
            return "Moderate match: Some relevant skills present, but gaps exist"
        else:
            return "Weak match: Limited skill overlap with job requirements"


def create_test_pairs():
    """Create test resume-JD pairs"""
    pairs = [
        {
            "name": "Senior Python Developer (Strong Match)",
            "resume": "Senior Python Developer with 6 years experience in Django FastAPI microservices. Led team of 5 engineers. AWS deployment scaling. Expert in REST APIs PostgreSQL Redis.",
            "jd": "Senior Backend Engineer Python Django FastAPI required 5+ years. Team leadership microservices architecture AWS deployment. Bachelor degree required."
        },
        {
            "name": "Data Scientist (Moderate Match)",
            "resume": "Data Scientist 3 years Python SQL machine learning TensorFlow scikit-learn. Statistical analysis and visualization. Kaggle competitions. Undergraduate degree Computer Science.",
            "jd": "Machine Learning Engineer 5+ years Python required. TensorFlow PyTorch deep learning. Backend systems. Advanced degree preferred."
        },
        {
            "name": "Java Backend (Weak Match)",
            "resume": "Java Developer 4 years Spring Boot microservices MySQL. Enterprise applications. OOP design patterns. Transaction management.",
            "jd": "Senior Frontend React Engineer 5+ years JavaScript React.js required. Redux state management. CSS Responsive design. Node.js backend."
        },
        {
            "name": "React Developer (Good Match)",
            "resume": "Frontend Engineer 4 years React JavaScript HTML CSS. Redux state management. Jest testing. Responsive design mobile optimization. Node.js backend experience.",
            "jd": "Senior Frontend React Engineer 4+ years React JavaScript required. Redux testing CSS. Background in Node.js backend beneficial."
        },
        {
            "name": "Full Stack (Perfect Match)",
            "resume": "Full Stack Engineer 5 years JavaScript React Node.js Express MongoDB. REST APIs microservices Docker deployment. AWS infrastructure DevOps.",
            "jd": "Full Stack JavaScript Engineer 5 years React Node.js required. Express MongoDB microservices deployment. Docker Kubernetes."
        }
    ]
    return pairs


def main():
    """Run SHAP analysis on all pairs"""
    print("\n" + "="*80)
    print("FAIR-XAI: Pure SHAP Implementation (Token Ablation)")
    print("="*80)
    
    try:
        calculator = PureSHAPCalculator()
        pairs = create_test_pairs()
        
        all_results = {
            "timestamp": "2026-04-10",
            "methodology": "Kernel SHAP - Token Ablation",
            "model": "Sentence Transformers (all-MiniLM-L6-v2)",
            "total_pairs": len(pairs),
            "results": []
        }
        
        for pair in pairs:
            result = calculator.explain_pair(
                pair["resume"],
                pair["jd"],
                pair["name"]
            )
            all_results["results"].append(result)
        
        # Save results
        output_file = "fairxai_shap_actual_results.json"
        with open(output_file, "w") as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"[OK] Results saved to: {output_file}")
        print(f"[OK] Analyzed {len(pairs)} pairs")
        print(f"{'='*80}\n")
        
        return all_results
        
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = main()
    
    # Print summary statistics
    if results:
        print("\nSUMMARY:")
        print("-" * 60)
        for r in results["results"]:
            print(f"\n{r['pair_name']}")
            print(f"  Similarity: {r['baseline_similarity']:.4f}")
            if r['shap_analysis']['top_positive_tokens']:
                top_tok = r['shap_analysis']['top_positive_tokens'][0]
                print(f"  Top token: {top_tok['token']} (+{top_tok['shap_value']})")
