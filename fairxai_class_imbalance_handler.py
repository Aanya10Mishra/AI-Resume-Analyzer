"""
Fair-XAI Class Imbalance Handler
Handles imbalanced dataset scenarios in synthetic resume generation
Implements class_weight='balanced' strategies for fair model training

Class Distribution: 200 Strong (33%) vs 400 Weak (67%)

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
"""

import json
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from sklearn.utils.class_weight import compute_class_weight

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClassImbalanceHandler:
    """
    Handles class imbalance in synthetic resume dataset
    
    Problem:
    - Real hiring systems have imbalanced outcomes (more rejected than accepted)
    - ML models trained on imbalanced data often bias towards majority class
    - This can amplify unfairness across protected attributes
    
    Solution:
    - Label resumes as 'Strong' (33%) or 'Weak' (67%) candidates
    - Use class_weight='balanced' during model training to account for imbalance
    - Demonstrates how fairness metrics change with imbalance vs balanced training
    """
    
    # ============================================================================
    # CONSTANTS
    # ============================================================================
    
    STRONG_RATIO = 0.33  # 200 strong candidates
    WEAK_RATIO = 0.67    # 400 weak candidates
    
    # Strength factors based on resume attributes
    STRENGTH_CRITERIA = {
        'education': {
            "PhD in Computer Science": 5,
            "Master's in Computer Science": 4,
            "Master's in Data Science": 4,
            "Bachelor's in Computer Science": 3,
            "Bachelor's in Engineering": 3,
            "Bachelor's in Mathematics": 2,
            "Bootcamp Certificate": 1
        },
        'experience_level_weight': {
            'senior': 3,  # 8+ years
            'mid': 2,     # 3-7 years
            'entry': 1    # 0-2 years
        },
        'skills_per_category': {
            'ml_ai': 3,        # High value: ML/AI skills
            'cloud': 2,        # Medium: cloud/DevOps
            'frameworks': 2,   # Medium: frameworks
            'databases': 1,    # Low: databases
            'programming': 1   # Low: programming alone
        }
    }
    
    # ============================================================================
    # INITIALIZATION
    # ============================================================================
    
    def __init__(self, strong_ratio: float = 0.33, seed: int = 42):
        """
        Initialize class imbalance handler
        
        Args:
            strong_ratio: Proportion of strong candidates (0.33 = 33%)
            seed: Random seed for reproducibility
        """
        self.strong_ratio = strong_ratio
        self.weak_ratio = 1.0 - strong_ratio
        self.seed = seed
        
        np.random.seed(seed)
        logger.info(f"✅ Class Imbalance Handler initialized")
        logger.info(f"   Strong candidates: {strong_ratio:.1%}")
        logger.info(f"   Weak candidates: {1-strong_ratio:.1%}")
    
    # ============================================================================
    # STRENGTH CALCULATION
    # ============================================================================
    
    def calculate_candidate_strength(self, resume: Dict) -> float:
        """
        Calculate strength score (0.0 to 1.0) based on resume attributes
        
        Args:
            resume: Resume dictionary with education, skills, experience
        
        Returns:
            Float strength score (0.0 = weakest, 1.0 = strongest)
        """
        strength = 0.0
        weights = 0.0
        
        # 1. Education strength (weight: 30%)
        education = resume.get('education', '')
        if education in self.STRENGTH_CRITERIA['education']:
            edu_score = self.STRENGTH_CRITERIA['education'][education] / 5.0
            strength += 0.30 * edu_score
            weights += 0.30
        
        # 2. Experience level strength (weight: 35%)
        exp_level = resume.get('experience_level', 'entry')
        if exp_level in self.STRENGTH_CRITERIA['experience_level_weight']:
            exp_score = self.STRENGTH_CRITERIA['experience_level_weight'][exp_level] / 3.0
            strength += 0.35 * exp_score
            weights += 0.35
        
        # 3. Skills strength (weight: 35%)
        skills = resume.get('skills', [])
        skill_strength = self._calculate_skill_strength(skills)
        strength += 0.35 * skill_strength
        weights += 0.35
        
        # Normalize to 0-1 range
        return min(1.0, strength / weights) if weights > 0 else 0.5
    
    def _calculate_skill_strength(self, skills: List[str]) -> float:
        """Calculate skill strength score"""
        if not skills:
            return 0.0
        
        ml_ai_skills = [s for s in skills if any(ml in s for ml in 
                       ['Machine', 'Deep', 'TensorFlow', 'PyTorch', 'NLP', 'AI'])]
        cloud_skills = [s for s in skills if any(c in s for c in 
                       ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes'])]
        framework_skills = [s for s in skills if any(f in s for f in 
                           ['Django', 'Flask', 'FastAPI', 'Spring', 'React', 'Vue', 'Angular'])]
        
        score = 0.0
        
        # Weight high-value skills
        score += len(ml_ai_skills) * 0.30 / max(1, len(skills))
        score += len(cloud_skills) * 0.20 / max(1, len(skills))
        score += len(framework_skills) * 0.20 / max(1, len(skills))
        score += min(len(skills) / 5.0, 0.30)  # General skill count (max 0.30)
        
        return min(1.0, score)
    
    # ============================================================================
    # CLASS LABELING
    # ============================================================================
    
    def label_candidates_by_strength(self, resumes: List[Dict]) -> List[Dict]:
        """
        Label candidates as 'Strong' or 'Weak' based on calculated strength
        Ensures imbalance ratio of 33% strong, 67% weak
        
        Args:
            resumes: List of resume dictionaries
        
        Returns:
            List of resumes with added 'strength' and 'is_strong' fields
        """
        logger.info(f"\n🔄 Labeling {len(resumes)} candidates by strength...")
        
        # Calculate strength for each resume
        strengths = []
        for i, resume in enumerate(resumes):
            strength = self.calculate_candidate_strength(resume)
            strengths.append((i, strength))
        
        # Sort by strength (descending)
        strengths.sort(key=lambda x: x[1], reverse=True)
        
        # Determine strong/weak split
        num_strong = int(len(resumes) * self.strong_ratio)
        num_weak = len(resumes) - num_strong
        
        logger.info(f"   Strong candidates target: {num_strong} ({self.strong_ratio:.1%})")
        logger.info(f"   Weak candidates target: {num_weak} ({self.weak_ratio:.1%})")
        
        # Label candidates
        for i, (idx, strength) in enumerate(strengths):
            is_strong = i < num_strong
            resumes[idx]['strength_score'] = round(strength, 4)
            resumes[idx]['is_strong'] = is_strong
            resumes[idx]['strength_label'] = 'Strong' if is_strong else 'Weak'
            resumes[idx]['quality_class'] = 1 if is_strong else 0
        
        # Verify distribution
        strong_count = sum(1 for r in resumes if r['is_strong'])
        weak_count = sum(1 for r in resumes if not r['is_strong'])
        
        logger.info(f"\n✅ Labeling complete:")
        logger.info(f"   Strong: {strong_count} ({strong_count/len(resumes):.1%})")
        logger.info(f"   Weak: {weak_count} ({weak_count/len(resumes):.1%})")
        
        # Show strength distribution by gender (if available)
        if resumes and 'gender' in resumes[0]:
            self._show_strength_by_gender(resumes)
        
        return resumes
    
    def _show_strength_by_gender(self, resumes: List[Dict]):
        """Show strength distribution by gender (fairness check)"""
        logger.info(f"\n📊 Strength Distribution by Gender:")
        logger.info("-" * 70)
        
        for gender in ['Male', 'Female']:
            gender_resumes = [r for r in resumes if r.get('gender') == gender]
            if not gender_resumes:
                continue
            
            strong = sum(1 for r in gender_resumes if r['is_strong'])
            weak = sum(1 for r in gender_resumes if not r['is_strong'])
            total = len(gender_resumes)
            
            logger.info(f"{gender}:")
            logger.info(f"   Strong: {strong}/{total} ({strong/total:.1%})")
            logger.info(f"   Weak: {weak}/{total} ({weak/total:.1%})")
            
            # Check for gender bias in strength distribution
            avg_strength = np.mean([r['strength_score'] for r in gender_resumes])
            logger.info(f"   Avg Strength: {avg_strength:.4f}")
    
    # ============================================================================
    # CLASS WEIGHT COMPUTATION
    # ============================================================================
    
    @staticmethod
    def compute_class_weights(y: np.ndarray) -> Dict[int, float]:
        """
        Compute class weights for imbalanced dataset
        Used with class_weight='balanced' parameter in sklearn models
        
        Args:
            y: Array of class labels (0=Weak, 1=Strong)
        
        Returns:
            Dictionary mapping class to weight
        """
        classes = np.unique(y)
        weights = compute_class_weight('balanced', classes=classes, y=y)
        
        weight_dict = {int(cls): float(w) for cls, w in zip(classes, weights)}
        
        logger.info(f"\n⚖️  Computed Class Weights (for class_weight='balanced'):")
        logger.info("-" * 60)
        for cls, weight in weight_dict.items():
            label = "Strong" if cls == 1 else "Weak"
            logger.info(f"   Class {cls} ({label}): {weight:.4f}")
        
        return weight_dict
    
    @staticmethod
    def compute_sample_weights(y: np.ndarray) -> np.ndarray:
        """
        Compute sample weights for training
        Upweights minority class and downweights majority class
        
        Args:
            y: Array of class labels (0=Weak, 1=Strong)
        
        Returns:
            Array of weights for each sample
        """
        classes = np.unique(y)
        class_weights = compute_class_weight('balanced', classes=classes, y=y)
        
        sample_weights = np.array([class_weights[int(label)] for label in y])
        
        logger.info(f"\n🎯 Computed Sample Weights:")
        logger.info(f"   Min weight: {sample_weights.min():.4f}")
        logger.info(f"   Max weight: {sample_weights.max():.4f}")
        logger.info(f"   Weight multiplier: {sample_weights.max() / sample_weights.min():.2f}x")
        
        return sample_weights
    
    # ============================================================================
    # STATISTICS & ANALYSIS
    # ============================================================================
    
    def get_imbalance_statistics(self, resumes: List[Dict]) -> Dict:
        """
        Compute statistics about class imbalance
        
        Args:
            resumes: List of labeled resumes
        
        Returns:
            Dictionary with imbalance statistics
        """
        strong_count = sum(1 for r in resumes if r['is_strong'])
        weak_count = len(resumes) - strong_count
        
        strong_resumes = [r for r in resumes if r['is_strong']]
        weak_resumes = [r for r in resumes if not r['is_strong']]
        
        stats = {
            'total_resumes': len(resumes),
            'strong_count': strong_count,
            'weak_count': weak_count,
            'strong_ratio': strong_count / len(resumes),
            'weak_ratio': weak_count / len(resumes),
            'imbalance_ratio': weak_count / strong_count,
            'avg_strength_strong': round(np.mean([r['strength_score'] for r in strong_resumes]), 4),
            'avg_strength_weak': round(np.mean([r['strength_score'] for r in weak_resumes]), 4),
            'median_strength': round(np.median([r['strength_score'] for r in resumes]), 4),
            'std_strength': round(np.std([r['strength_score'] for r in resumes]), 4),
        }
        
        return stats
    
    def print_imbalance_report(self, resumes: List[Dict]):
        """Print detailed imbalance report"""
        stats = self.get_imbalance_statistics(resumes)
        
        logger.info(f"\n" + "="*80)
        logger.info(f"CLASS IMBALANCE STATISTICS")
        logger.info(f"="*80)
        logger.info(f"Total Resumes: {stats['total_resumes']}")
        logger.info(f"\nClass Distribution:")
        logger.info(f"  Strong: {stats['strong_count']} ({stats['strong_ratio']:.1%})")
        logger.info(f"  Weak: {stats['weak_count']} ({stats['weak_ratio']:.1%})")
        logger.info(f"  Imbalance Ratio: {stats['imbalance_ratio']:.2f}:1 (Weak:Strong)")
        logger.info(f"\nStrength Scores:")
        logger.info(f"  Strong avg: {stats['avg_strength_strong']:.4f}")
        logger.info(f"  Weak avg: {stats['avg_strength_weak']:.4f}")
        logger.info(f"  Median: {stats['median_strength']:.4f}")
        logger.info(f"  Std Dev: {stats['std_strength']:.4f}")
        logger.info(f"="*80)
        
        return stats
    
    # ============================================================================
    # SAVE & LOAD
    # ============================================================================
    
    def save_labeled_dataset(self, resumes: List[Dict], filename: str):
        """Save labeled dataset with strength information"""
        stats = self.get_imbalance_statistics(resumes)
        
        output = {
            'metadata': {
                'generation_date': datetime.now().isoformat(),
                'total_resumes': len(resumes),
                'class_distribution': {
                    'strong': stats['strong_count'],
                    'weak': stats['weak_count'],
                    'strong_ratio': stats['strong_ratio'],
                    'weak_ratio': stats['weak_ratio'],
                    'imbalance_ratio': stats['imbalance_ratio']
                },
                'strength_statistics': {
                    'avg_strong': stats['avg_strength_strong'],
                    'avg_weak': stats['avg_strength_weak'],
                    'median': stats['median_strength'],
                    'std': stats['std_strength']
                }
            },
            'resumes': resumes
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Labeled dataset saved: {filename}")
    
    @staticmethod
    def load_labeled_dataset(filename: str) -> Tuple[List[Dict], Dict]:
        """Load labeled dataset"""
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Labeled dataset loaded: {filename}")
        return data['resumes'], data['metadata']


# ============================================================================
# MODEL TRAINING WITH CLASS WEIGHT
# ============================================================================

class ImbalancedModelTrainer:
    """
    Trains ML models with proper handling of class imbalance
    Demonstrates difference between unweighted and weighted models
    """
    
    @staticmethod
    def train_with_balanced_weights(X_train, y_train, model_class, **model_params):
        """
        Train model with class_weight='balanced'
        
        Args:
            X_train: Training features
            y_train: Training labels (0=Weak, 1=Strong)
            model_class: Sklearn model class (e.g., LogisticRegression)
            **model_params: Additional model parameters
        
        Returns:
            Trained model
        """
        logger.info(f"\n🔧 Training {model_class.__name__} with class_weight='balanced'...")
        
        model = model_class(class_weight='balanced', random_state=42, **model_params)
        model.fit(X_train, y_train)
        
        logger.info(f"✅ Model trained successfully")
        logger.info(f"   Samples: {len(X_train)}")
        logger.info(f"   Strong: {(y_train == 1).sum()} ({(y_train == 1).mean():.1%})")
        logger.info(f"   Weak: {(y_train == 0).sum()} ({(y_train == 0).mean():.1%})")
        
        return model
    
    @staticmethod
    def train_with_sample_weights(X_train, y_train, sample_weights, model_class, **model_params):
        """
        Train model with explicit sample weights
        
        Args:
            X_train: Training features
            y_train: Training labels
            sample_weights: Weight for each sample
            model_class: Sklearn model class
            **model_params: Additional model parameters
        
        Returns:
            Trained model
        """
        logger.info(f"\n🔧 Training {model_class.__name__} with sample_weight...")
        
        model = model_class(random_state=42, **model_params)
        model.fit(X_train, y_train, sample_weight=sample_weights)
        
        logger.info(f"✅ Model trained with sample weights")
        
        return model
    
    @staticmethod
    def compare_weighted_vs_unweighted(X_train, y_train, model_class, **model_params):
        """
        Train two models: one weighted, one unweighted
        Compare their predictions and fairness
        
        Args:
            X_train: Training features
            y_train: Training labels
            model_class: Sklearn model class
            **model_params: Additional model parameters
        
        Returns:
            Tuple of (weighted_model, unweighted_model)
        """
        logger.info(f"\n📊 Comparing Weighted vs Unweighted {model_class.__name__}...")
        logger.info("="*60)
        
        # Train weighted model
        logger.info("\n1️⃣ Training with class_weight='balanced'...")
        weighted = model_class(class_weight='balanced', random_state=42, **model_params)
        weighted.fit(X_train, y_train)
        
        # Train unweighted model
        logger.info("\n2️⃣ Training without class weight (baseline)...")
        unweighted = model_class(class_weight=None, random_state=42, **model_params)
        unweighted.fit(X_train, y_train)
        
        logger.info("\n✅ Both models trained successfully")
        
        return weighted, unweighted


# ============================================================================
# DEMONSTRATION
# ============================================================================

if __name__ == "__main__":
    from fairxai_synthetic_data_generator import SyntheticResumeGenerator
    
    logger.info("="*80)
    logger.info("CLASS IMBALANCE HANDLER DEMONSTRATION")
    logger.info("="*80)
    
    # Step 1: Generate synthetic resumes
    logger.info("\n📝 Step 1: Generating synthetic resumes...")
    generator = SyntheticResumeGenerator(seed=42)
    resumes, metadata = generator.generate_dataset(
        total_resumes=600,
        balance_groups=True
    )
    
    # Step 2: Label by strength (imbalanced)
    logger.info("\n🏷️  Step 2: Labeling candidates by strength...")
    handler = ClassImbalanceHandler(strong_ratio=0.33, seed=42)
    resumes = handler.label_candidates_by_strength(resumes)
    
    # Step 3: Print statistics
    logger.info("\n📊 Step 3: Imbalance statistics...")
    stats = handler.print_imbalance_report(resumes)
    
    # Step 4: Compute class weights
    logger.info("\n⚖️  Step 4: Computing class weights...")
    y = np.array([r['quality_class'] for r in resumes])
    class_weights = ClassImbalanceHandler.compute_class_weights(y)
    sample_weights = ClassImbalanceHandler.compute_sample_weights(y)
    
    # Step 5: Save labeled dataset
    logger.info("\n💾 Step 5: Saving labeled dataset...")
    handler.save_labeled_dataset(
        resumes,
        'fairxai_synthetic_resumes_600_imbalanced.json'
    )
    
    logger.info("\n✅ Demonstration complete!")
    logger.info(f"\nDataset saved: fairxai_synthetic_resumes_600_imbalanced.json")
    logger.info(f"\nKey metrics:")
    logger.info(f"  Strong: {stats['strong_count']} ({stats['strong_ratio']:.1%})")
    logger.info(f"  Weak: {stats['weak_count']} ({stats['weak_ratio']:.1%})")
    logger.info(f"  Imbalance ratio: {stats['imbalance_ratio']:.2f}:1")
