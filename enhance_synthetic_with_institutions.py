"""
Enhance Synthetic Dataset with Institutional Diversity
Adds realistic educational institutions with Tier-1/2/3 distribution
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyntheticDataEnhancer:
    """Add institutional diversity to synthetic dataset"""
    
    TIER_1_UNIVERSITIES = [
        'Harvard University', 'Yale University', 'Princeton University',
        'Stanford University', 'MIT', 'Columbia University',
        'University of Pennsylvania', 'California Institute of Technology',
        'Northwestern University', 'Duke University',
        'University of Chicago', 'Cornell University'
    ]
    
    TIER_2_UNIVERSITIES = [
        'UC Berkeley', 'University of Michigan', 'University of Texas at Austin',
        'Georgia Institute of Technology', 'University of Illinois Urbana-Champaign',
        'University of Wisconsin-Madison', 'University of Southern California',
        'Carnegie Mellon University', 'New York University', 'Boston University',
        'Pennsylvania State University', 'Purdue University'
    ]
    
    TIER_3_UNIVERSITIES = [
        'American University', 'Auburn University', 'George Mason University',
        'University of Arizona', 'University of Minnesota',
        'Temple University', 'Kent State University', 'San Diego State University',
        'Florida Atlantic University', 'Portland State University',
        'University of New Mexico', 'University of Colorado'
    ]
    
    DEGREE_FIELDS = [
        'Computer Science', 'Engineering', 'Business Administration',
        'Information Technology', 'Mathematics', 'Physics',
        'Economics', 'Data Science', 'Software Engineering'
    ]
    
    def enhance_dataset(self, input_path: str, output_path: str):
        """
        Add institutional diversity to synthetic dataset
        
        Args:
            input_path: Path to original synthetic dataset
            output_path: Path to save enhanced dataset
        """
        logger.info("📚 Loading synthetic dataset for enhancement...")
        
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        resumes = data['resumes']
        total = len(resumes)
        
        # Define institutional distribution
        # Tier-1: 15%, Tier-2: 35%, Tier-3: 50%
        tier1_count = int(total * 0.15)
        tier2_count = int(total * 0.35)
        tier3_count = total - tier1_count - tier2_count
        
        logger.info(f"   Tier-1 allocation: {tier1_count} ({tier1_count/total*100:.1f}%)")
        logger.info(f"   Tier-2 allocation: {tier2_count} ({tier2_count/total*100:.1f}%)")
        logger.info(f"   Tier-3 allocation: {tier3_count} ({tier3_count/total*100:.1f}%)")
        
        # Shuffle indices for random assignment
        indices = np.arange(total)
        np.random.shuffle(indices)
        
        tier1_indices = set(indices[:tier1_count])
        tier2_indices = set(indices[tier1_count:tier1_count+tier2_count])
        tier3_indices = set(indices[tier1_count+tier2_count:])
        
        logger.info("\n🔄 Adding institutional diversity...")
        
        for idx, resume in enumerate(resumes):
            field = np.random.choice(self.DEGREE_FIELDS)
            degree = np.random.choice(['Bachelor', "Bachelor's", 'B.S.', 'B.A.', 'B.Eng'])
            
            if idx in tier1_indices:
                university = np.random.choice(self.TIER_1_UNIVERSITIES)
                year = np.random.randint(2010, 2024)
            elif idx in tier2_indices:
                university = np.random.choice(self.TIER_2_UNIVERSITIES)
                year = np.random.randint(2008, 2024)
            else:
                university = np.random.choice(self.TIER_3_UNIVERSITIES)
                year = np.random.randint(2006, 2024)
            
            resume['education_enhanced'] = f"{degree} in {field} from {university}, {year}"
            resume['institution'] = university
            resume['degree_field'] = field
            resume['education_year'] = year
        
        # Update metadata
        data['metadata']['enhanced_with_institutions'] = True
        data['metadata']['institutional_distribution'] = {
            'Tier-1': tier1_count,
            'Tier-2': tier2_count,
            'Tier-3': tier3_count
        }
        data['metadata']['enhancement_timestamp'] = datetime.now().isoformat()
        
        # Save enhanced dataset
        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"\n✅ Enhanced dataset saved to: {output_path}")
            logger.info(f"   Total records: {len(resumes)}")
            logger.info(f"   New fields: institution, degree_field, education_year, education_enhanced")
        except Exception as e:
            logger.error(f"❌ Error saving enhanced dataset: {e}")


if __name__ == "__main__":
    enhancer = SyntheticDataEnhancer()
    enhancer.enhance_dataset(
        'fairxai_synthetic_resumes_600_imbalanced.json',
        'fairxai_synthetic_resumes_enhanced_institutional.json'
    )
