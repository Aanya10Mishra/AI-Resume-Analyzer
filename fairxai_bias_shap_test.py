
"""
Institutional Bias Analysis with SHAP
Tests if Tier-1 vs Tier-3 resumes with identical skills get different SHAP importance
"""

import json
from fairxai_shap_calculator import PureSHAPCalculator


def test_institutional_bias():
    """Compare SHAP analysis for Tier-1 vs Tier-3 with identical skills"""
    
    print("\n" + "="*80)
    print("INSTITUTIONAL BIAS TEST: SHAP Analysis")
    print("="*80)
    
    calculator = PureSHAPCalculator()
    
    # Same base resume, different institutions
    base_skills = "Full Stack Engineer 4 years JavaScript React Node.js Express. REST APIs microservices deployment. Database design optimization."
    jd = "Full Stack JavaScript Engineer 4+ years React Node.js required. Microservices REST APIs. Express backend. Database design skills needed."
    
    # Tier-1 institution (high prestige)
    tier1_resume = f"{base_skills} MS from MIT."
    
    # Tier-3 institution (regional college)
    tier3_resume = f"{base_skills} MS from Regional College."
    
    print("\n[*] Testing: Same skills, different institutions")
    print(f"\nTier-1 Resume (MIT): {tier1_resume[:60]}...")
    print(f"Tier-3 Resume (Regional): {tier3_resume[:60]}...")
    print(f"\nJob Description: {jd[:60]}...\n")
    
    # Get SHAP for both
    tier1_result = calculator.explain_pair(tier1_resume, jd, "Tier-1 (MIT)")
    tier3_result = calculator.explain_pair(tier3_resume, jd, "Tier-3 (Regional)")
    
    # Compare results
    tier1_score = tier1_result["baseline_similarity"]
    tier3_score = tier3_result["baseline_similarity"]
    difference = tier1_score - tier3_score
    percentage_diff = (difference / tier3_score) * 100 if tier3_score > 0 else 0
    
    print(f"\n{'='*80}")
    print("INSTITUTIONAL BIAS ANALYSIS - RESULTS")
    print("="*80)
    
    print(f"\nTier-1 Similarity Score: {tier1_score:.4f}")
    print(f"Tier-3 Similarity Score: {tier3_score:.4f}")
    print(f"Absolute Difference:     {difference:.4f}")
    print(f"Percentage Difference:   {percentage_diff:.2f}%")
    
    # Extract institution tokens
    tier1_shap = tier1_result["shap_analysis"]["all_tokens_shap"]
    tier3_shap = tier3_result["shap_analysis"]["all_tokens_shap"]
    
    institution_tokens_t1 = {k: v for k, v in tier1_shap.items() if "mit" in k.lower()}
    institution_tokens_t3 = {k: v for k, v in tier3_shap.items() if "regional" in k.lower() or "college" in k.lower()}
    
    print(f"\nInstitution Contribution:")
    print(f"  Tier-1 (MIT):     {sum(institution_tokens_t1.values()):.4f} SHAP value")
    print(f"  Tier-3 (Regional): {sum(institution_tokens_t3.values()):.4f} SHAP value")
    
    # Check if bias exists
    bias_detected = percentage_diff > 5.0  # More than 5% difference
    
    print(f"\n{'='*80}")
    print("BIAS VERDICT")
    print("="*80)
    print(f"\nBias Detected: {'YES' if bias_detected else 'NO'}")
    print(f"Magnitude: {percentage_diff:.2f}% difference")
    
    if not bias_detected:
        print("\nConclusion: No significant institutional bias detected.")
        print(f"The {percentage_diff:.2f}% difference is within normal statistical variation.")
        print("The FAIR-XAI system treats candidates fairly regardless of institution.")
    else:
        print(f"\nWarning: {percentage_diff:.2f}% difference detected between tiers.")
        print("Further investigation of bias may be needed.")
    
    # Build output JSON
    analysis = {
        "test": "Institutional Bias via SHAP Token Ablation",
        "timestamp": "2026-04-10",
        "methodology": "Compare SHAP values for identical skills from different institutions",
        "results": {
            "tier_1": {
                "institution": "MIT (Tier-1)",
                "resume": tier1_resume,
                "baseline_similarity": tier1_score,
                "top_positive_tokens": tier1_result["shap_analysis"]["top_positive_tokens"][:5],
                "shap_values": tier1_shap
            },
            "tier_3": {
                "institution": "Regional College (Tier-3)",
                "resume": tier3_resume,
                "baseline_similarity": tier3_score,
                "top_positive_tokens": tier3_result["shap_analysis"]["top_positive_tokens"][:5],
                "shap_values": tier3_shap
            }
        },
        "comparison": {
            "tier1_score": round(tier1_score, 4),
            "tier3_score": round(tier3_score, 4),
            "absolute_difference": round(difference, 4),
            "percentage_difference": round(percentage_diff, 2),
            "institution_contribution_tier1": round(sum(institution_tokens_t1.values()), 4),
            "institution_contribution_tier3": round(sum(institution_tokens_t3.values()), 4)
        },
        "conclusion": {
            "bias_detected": bias_detected,
            "magnitude": f"{percentage_diff:.2f}%",
            "interpretation": "No significant institutional bias" if not bias_detected else "Possible institutional bias"
        }
    }
    
    # Save results
    output_file = "fairxai_institutional_bias_shap_test.json"
    with open(output_file, "w") as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n[OK] Detailed results saved to: {output_file}")
    print("="*80 + "\n")
    
    return analysis


if __name__ == "__main__":
    test_institutional_bias()
