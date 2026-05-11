"""
FAIR-XAI SHAP-LIME Analysis Runner
Calculate and save SHAP and LIME explanations for resume-JD matching

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
Author: Aanya Mishra
"""

import json
import logging
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# LOAD DATA FROM KAGGLE EVALUATION
# ============================================================================

def load_kaggle_evaluation_data(json_file: str = 'matching_evaluation_kaggle_quick.json') -> Dict:
    """Load Kaggle evaluation data with resume-JD pairs"""
    
    logger.info(f"📂 Loading evaluation data from {json_file}...")
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        logger.info(f"✅ Loaded {data.get('sample_size', 'N/A')} resumes")
        logger.info(f"✅ With {data.get('jd_count', 'N/A')} job descriptions")
        
        return data
    
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        return None


def load_synthetic_dataset(json_file: str = 'fairxai_synthetic_resumes_600_imbalanced.json') -> List[Dict]:
    """Load synthetic resume dataset"""
    
    logger.info(f"📂 Loading synthetic data from {json_file}...")
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'resumes' in data:
            resumes = data['resumes']
        else:
            resumes = data if isinstance(data, list) else []
        
        logger.info(f"✅ Loaded {len(resumes)} synthetic resumes")
        
        return resumes
    
    except Exception as e:
        logger.error(f"❌ Failed to load synthetic data: {e}")
        return []


# ============================================================================
# EXTRACT SAMPLE RESUME-JD PAIRS
# ============================================================================

def create_realistic_resume_jd_pairs() -> List[Tuple[str, str]]:
    """Create realistic sample pairs from the project"""
    
    pairs = [
        # Pair 1: Strong match
        (
            """Senior Python Developer
            5+ years Django and FastAPI development
            Experience with microservices, Kubernetes, Docker
            Led team of 5 developers at tech startup
            BS Computer Science from Top University
            """,
            """Senior Backend Engineer
            5+ years Python development required
            Microservices architecture expertise needed
            Team leadership experience valued
            Django or FastAPI experience preferred"""
        ),
        
        # Pair 2: Moderate match
        (
            """Data Scientist
            3 years Python and SQL experience
            Machine learning with scikit-learn, TensorFlow
            Undergraduate degree in Mathematics
            Some experience with AWS
            """,
            """Machine Learning Engineer
            5+ years Python required
            TensorFlow and PyTorch expertise needed
            Advanced statistics knowledge essential
            PhD in Computer Science or related field preferred"""
        ),
        
        # Pair 3: Weak match
        (
            """Java Developer
            4 years Spring Boot development
            Database design and optimization
            BS Information Technology from regional college
            Basic Python knowledge
            """,
            """Senior Frontend React Developer
            5+ years React.js required
            Node.js and TypeScript expertise needed
            CSS/HTML proficiency essential
            MS Computer Science preferred"""
        ),
        
        # Pair 4: Institutional bias test (same skills, different colleges)
        (
            """Full Stack Engineer
            4+ years JavaScript, React, Node.js
            Database design, deployment scaling
            Published research on Web optimization
            MS from Tier-1 Institution (MIT/Stanford/Berkeley)
            """,
            """Full Stack JavaScript Engineer
            4+ years React and Node.js required
            Microservices and scaling experience
            Database design skills needed
            Bachelor's degree required"""
        ),
        
        # Pair 5: Same skills as Pair 4, but Tier-3
        (
            """Full Stack Engineer
            4+ years JavaScript, React, Node.js
            Database design, deployment scaling
            Published research on Web optimization
            MS from Tier-3 Regional College
            """,
            """Full Stack JavaScript Engineer
            4+ years React and Node.js required
            Microservices and scaling experience
            Database design skills needed
            Bachelor's degree required"""
        ),
    ]
    
    return pairs


# ============================================================================
# MAIN ANALYSIS
# ============================================================================

def run_shap_lime_analysis(output_file: str = 'fairxai_shap_lime_explanations.json'):
    """
    Run SHAP and LIME explanations on resume-JD pairs
    """
    
    logger.info(f"\n{'='*80}")
    logger.info(f"FAIR-XAI SHAP-LIME ANALYSIS")
    logger.info(f"{'='*80}\n")
    
    # Import the explainer
    try:
        from fairxai_shap_lime_explainer import SHAPLIMEExplainer
    except ImportError as e:
        logger.error(f"❌ Cannot import explainer: {e}")
        logger.info("Make sure fairxai_shap_lime_explainer.py is in the same directory")
        return
    
    # Initialize explainer
    explainer = SHAPLIMEExplainer()
    
    # Get sample pairs
    pairs = create_realistic_resume_jd_pairs()
    
    logger.info(f"📊 Analyzing {len(pairs)} resume-JD pairs...\n")
    
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "total_pairs": len(pairs),
        "methodology": "SHAP (Token Ablation) + LIME (Phrase Perturbation)",
        "model": "Sentence Transformers (all-MiniLM-L6-v2)",
        "pairs_analyzed": []
    }
    
    # Explain each pair
    for i, (resume, jd) in enumerate(pairs, 1):
        logger.info(f"\n[{i}/{len(pairs)}] Explaining resume-JD pair...")
        
        result = explainer.explain_pair(resume, jd, methods=['lime', 'shap'])
        
        # Add pair number and metadata
        result['pair_number'] = i
        result['resume_length'] = len(resume.split())
        result['jd_length'] = len(jd.split())
        
        all_results['pairs_analyzed'].append(result)
        
        # Show summary
        if 'LIME' in result.get('explanations', {}):
            lime_sim = result['explanations']['LIME'].get('baseline_similarity', 0)
            logger.info(f"   LIME Baseline Similarity: {lime_sim:.4f}")
            
            lime_contrib = result['explanations']['LIME'].get('top_contributing_phrases', [])
            if lime_contrib:
                logger.info(f"   Top phrase: '{lime_contrib[0]['phrase']}' (contribution: {lime_contrib[0]['contribution']:.4f})")
        
        if 'SHAP' in result.get('explanations', {}):
            shap_sim = result['explanations']['SHAP'].get('baseline_similarity', 0)
            logger.info(f"   SHAP Baseline Similarity: {shap_sim:.4f}")
            
            shap_tokens = result['explanations']['SHAP'].get('top_important_tokens', [])
            if shap_tokens:
                logger.info(f"   Most important token: '{shap_tokens[0]['token']}' (importance: {shap_tokens[0]['importance']:.4f})")
    
    # Save results
    logger.info(f"\n{'='*80}")
    logger.info(f"SAVING RESULTS")
    logger.info(f"{'='*80}\n")
    
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"✅ Results saved to {output_file}")
    
    return all_results


# ============================================================================
# ANALYSIS COMPARISON (Institutional Bias Test)
# ============================================================================

def run_institutional_bias_shap_lime_test():
    """
    Specific test comparing SHAP-LIME explanations
    for same candidate skills but different institutions
    (Pair 4 vs Pair 5 from above)
    """
    
    logger.info(f"\n{'='*80}")
    logger.info(f"INSTITUTIONAL BIAS EXPLANATION ANALYSIS")
    logger.info(f"{'='*80}\n")
    
    try:
        from fairxai_shap_lime_explainer import SHAPLIMEExplainer
    except ImportError as e:
        logger.error(f"❌ Cannot import explainer: {e}")
        return
    
    explainer = SHAPLIMEExplainer()
    
    # Job description (same for both)
    jd = """Full Stack JavaScript Engineer
    4+ years React and Node.js required
    Microservices and scaling experience
    Database design skills needed
    Bachelor's degree required"""
    
    # Resume from Tier-1 institution
    resume_tier1 = """Full Stack Engineer
    4+ years JavaScript, React, Node.js
    Database design, deployment scaling
    Published research on Web optimization
    MS from Tier-1 Institution (MIT/Stanford/Berkeley)"""
    
    # Resume from Tier-3 institution (same skills)
    resume_tier3 = """Full Stack Engineer
    4+ years JavaScript, React, Node.js
    Database design, deployment scaling
    Published research on Web optimization
    MS from Tier-3 Regional College"""
    
    logger.info("📊 Testing institutional bias through SHAP-LIME explanations...\n")
    
    # Explain both
    result_tier1 = explainer.explain_pair(resume_tier1, jd, methods=['lime', 'shap'])
    result_tier3 = explainer.explain_pair(resume_tier3, jd, methods=['lime', 'shap'])
    
    # Compare
    comparison = {
        "test": "Institutional Bias - SHAP-LIME Analysis",
        "methodology": "Compare explanations for identical skills from different institutions",
        "results": {
            "Tier-1 (MIT/Stanford)": result_tier1,
            "Tier-3 (Regional College)": result_tier3,
            "difference_lime": {
                "tier1_similarity": result_tier1['explanations'].get('LIME', {}).get('baseline_similarity', 0),
                "tier3_similarity": result_tier3['explanations'].get('LIME', {}).get('baseline_similarity', 0),
                "difference": result_tier1['explanations'].get('LIME', {}).get('baseline_similarity', 0) - 
                             result_tier3['explanations'].get('LIME', {}).get('baseline_similarity', 0)
            },
            "difference_shap": {
                "tier1_similarity": result_tier1['explanations'].get('SHAP', {}).get('baseline_similarity', 0),
                "tier3_similarity": result_tier3['explanations'].get('SHAP', {}).get('baseline_similarity', 0),
                "difference": result_tier1['explanations'].get('SHAP', {}).get('baseline_similarity', 0) - 
                             result_tier3['explanations'].get('SHAP', {}).get('baseline_similarity', 0)
            }
        },
        "interpretation": "If similarity scores differ despite identical skills, it indicates institutional bias"
    }
    
    # Save
    output_file = 'fairxai_institutional_bias_shap_lime.json'
    with open(output_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    logger.info(f"\n✅ Institutional bias analysis saved to {output_file}")
    
    # Print summary
    logger.info("\n" + "="*80)
    logger.info("INSTITUTIONAL BIAS TEST RESULTS")
    logger.info("="*80)
    
    lime_diff = comparison['results']['difference_lime']['difference']
    shap_diff = comparison['results']['difference_shap']['difference']
    
    logger.info(f"\nLIME Analysis:")
    logger.info(f"  Tier-1 similarity: {comparison['results']['difference_lime']['tier1_similarity']:.4f}")
    logger.info(f"  Tier-3 similarity: {comparison['results']['difference_lime']['tier3_similarity']:.4f}")
    logger.info(f"  Difference: {lime_diff:.4f}")
    
    logger.info(f"\nSHAP Analysis:")
    logger.info(f"  Tier-1 similarity: {comparison['results']['difference_shap']['tier1_similarity']:.4f}")
    logger.info(f"  Tier-3 similarity: {comparison['results']['difference_shap']['tier3_similarity']:.4f}")
    logger.info(f"  Difference: {shap_diff:.4f}")
    
    if abs(lime_diff) < 0.05 and abs(shap_diff) < 0.05:
        logger.info("\n✅ ✅ ✅ NO INSTITUTIONAL BIAS DETECTED")
        logger.info("Both methods show similar treatment regardless of institution")
    else:
        logger.info("\n⚠️  INSTITUTIONAL BIAS DETECTED")
        logger.info("Model treats candidates differently based on institution")
    
    return comparison


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    
    # First, check if dependencies are installed
    logger.info("Checking dependencies...")
    
    try:
        import lime
        logger.info("✅ LIME is installed")
    except ImportError:
        logger.warning("⚠️  LIME not installed. Run: pip install lime")
    
    try:
        import shap
        logger.info("✅ SHAP is installed")
    except ImportError:
        logger.warning("⚠️  SHAP not installed. Run: pip install shap")
    
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("✅ Sentence Transformers is installed\n")
    except ImportError:
        logger.error("❌ Sentence Transformers not installed. Run: pip install sentence-transformers")
        exit(1)
    
    # Run main analysis
    logger.info("\nRunning main SHAP-LIME analysis...")
    results = run_shap_lime_analysis()
    
    # Run institutional bias test
    logger.info("\nRunning institutional bias SHAP-LIME test...")
    bias_results = run_institutional_bias_shap_lime_test()
    
    logger.info(f"\n{'='*80}")
    logger.info(f"ANALYSIS COMPLETE ✅")
    logger.info(f"{'='*80}")
    logger.info(f"\n📄 Output files:")
    logger.info(f"  1. fairxai_shap_lime_explanations.json - Main analysis")
    logger.info(f"  2. fairxai_institutional_bias_shap_lime.json - Bias test")
