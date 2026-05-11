"""
Fair-XAI Synthetic Dataset Generator
Generates 600 synthetic resumes with controlled sensitive attributes (gender, experience)
for fairness experimentation and bias auditing

Paper: "Ethical Challenges and Bias Mitigation in AI Resume Analyzers: A FAIR-XAI Framework"
"""

import json
import random
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyntheticResumeGenerator:
    """
    Generates controlled synthetic resumes to test fairness metrics
    Ensures balanced groups for SPD and DI calculation
    """
    
    def __init__(self, seed: int = 42):
        """Initialize generator with reproducible randomness"""
        random.seed(seed)
        np.random.seed(seed)
        self.seed = seed
        
    # ============================================================================
    # SKILL POOLS & DATA
    # ============================================================================
    
    SKILL_POOLS = {
        'programming': [
            'Python', 'Java', 'JavaScript', 'C++', 'Go', 'Rust', 'TypeScript',
            'C#', 'PHP', 'Kotlin', 'Swift', 'R', 'Scala', 'Ruby', 'SQL'
        ],
        'frameworks': [
            'Django', 'Flask', 'FastAPI', 'Spring Boot', 'React', 'Vue.js',
            'Angular', 'Node.js', 'Express', 'ASP.NET', 'Laravel', 'Rails',
            'TensorFlow', 'PyTorch', 'Keras'
        ],
        'databases': [
            'PostgreSQL', 'MongoDB', 'MySQL', 'Redis', 'Elasticsearch',
            'DynamoDB', 'Oracle', 'Cassandra', 'Firebase'
        ],
        'cloud': [
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
            'Jenkins', 'CI/CD', 'GitHub Actions'
        ],
        'ml_ai': [
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch',
            'NLP', 'Computer Vision', 'Scikit-learn', 'XGBoost',
            'BERT', 'Transformers', 'Neural Networks'
        ],
        'soft_skills': [
            'Communication', 'Leadership', 'Problem-solving', 'Teamwork',
            'Project Management', 'Agile', 'Mentoring', 'Technical Writing'
        ]
    }
    
    EDUCATION_LEVELS = [
        "Bachelor's in Computer Science",
        "Bachelor's in Engineering",
        "Master's in Computer Science",
        "Master's in Data Science",
        "PhD in Computer Science",
        "Bachelor's in Mathematics",
        "Bootcamp Certificate"
    ]
    
    JOB_TITLES_BY_EXPERIENCE = {
        'entry': [
            'Junior Software Developer',
            'Junior Data Analyst',
            'Junior QA Engineer',
            'Associate Developer',
            'Graduate Software Engineer'
        ],
        'mid': [
            'Software Engineer',
            'Senior Developer',
            'Data Scientist',
            'DevOps Engineer',
            'Full Stack Engineer',
            'ML Engineer'
        ],
        'senior': [
            'Senior Software Engineer',
            'Staff Engineer',
            'Principal Engineer',
            'Lead Data Scientist',
            'Engineering Manager',
            'Solutions Architect'
        ]
    }
    
    GENDERS = ['Male', 'Female']
    GENDER_INDICATOR_NAMES = {
        'Male': ['John', 'Michael', 'David', 'James', 'Robert', 'William', 'Richard'],
        'Female': ['Sarah', 'Jennifer', 'Mary', 'Lisa', 'Patricia', 'Emma', 'Susan']
    }
    
    # ============================================================================
    # SYNTHETIC RESUME GENERATION
    # ============================================================================
    
    def generate_resume(self, resume_id: int, gender: str, experience_level: str) -> Dict:
        """
        Generate a single synthetic resume with controlled attributes
        
        Args:
            resume_id: Unique identifier for resume
            gender: 'Male' or 'Female' (for fairness testing)
            experience_level: 'entry' (0-2 yrs), 'mid' (3-7 yrs), 'senior' (8+ yrs)
        
        Returns:
            Dictionary containing resume data with sensitive attributes
        """
        
        # Generate experience years based on level
        experience_ranges = {
            'entry': (0, 2),
            'mid': (3, 7),
            'senior': (8, 15)
        }
        years_experience = random.randint(*experience_ranges[experience_level])
        
        # Generate name with gender indicator (biased feature)
        first_name = random.choice(self.GENDER_INDICATOR_NAMES[gender])
        last_name = random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia'])
        name = f"{first_name} {last_name}"
        
        # Select job title based on experience
        job_title = random.choice(self.JOB_TITLES_BY_EXPERIENCE[experience_level])
        
        # Generate education
        education = random.choice(self.EDUCATION_LEVELS)
        
        # Generate skills based on experience (more experienced = more skills)
        num_skills = random.randint(3 + years_experience, 8 + years_experience)
        skills = random.sample(
            self.SKILL_POOLS['programming'] + 
            self.SKILL_POOLS['frameworks'] +
            self.SKILL_POOLS['databases'],
            min(num_skills, 15)
        )
        
        # Add soft skills
        soft_skills = random.sample(self.SKILL_POOLS['soft_skills'], random.randint(2, 4))
        
        # Generate work history
        work_history = self._generate_work_history(years_experience, job_title)
        
        # Create resume text
        resume_text = self._create_resume_text(
            name, job_title, years_experience, education, skills, soft_skills, work_history
        )
        
        # Create clean text for embedding
        clean_text = self._create_clean_text(resume_text)
        
        resume = {
            'id': resume_id,
            'name': name,
            'gender': gender,  # SENSITIVE ATTRIBUTE
            'years_experience': years_experience,  # SENSITIVE ATTRIBUTE
            'experience_level': experience_level,
            'current_title': job_title,
            'education': education,
            'skills': skills,
            'soft_skills': soft_skills,
            'work_history': work_history,
            'resume_text': resume_text,
            'clean_text': clean_text,
            'generated_at': datetime.now().isoformat()
        }
        
        return resume
    
    def _generate_work_history(self, years_experience: int, current_title: str) -> List[Dict]:
        """Generate work history entries"""
        history = []
        remaining_years = years_experience
        positions = random.randint(1, max(1, years_experience // 2 + 1))
        
        position_titles = [current_title]
        position_titles.extend(random.sample(
            [t for level in self.JOB_TITLES_BY_EXPERIENCE.values() for t in level 
             if t != current_title],
            min(positions - 1, 3)
        ))
        
        for i, title in enumerate(position_titles):
            # Ensure we don't overshoot remaining years
            max_duration = max(1, remaining_years)
            duration = random.randint(1, max_duration)
            remaining_years -= duration
            
            end_date = datetime.now() - timedelta(days=random.randint(30, 365))
            start_date = end_date - timedelta(days=duration * 365)
            
            history.append({
                'position': title,
                'company': f"{random.choice(['Tech', 'Data', 'Cloud'])} Corp {chr(65 + i)}",
                'duration_years': duration,
                'start_date': start_date.strftime('%Y-%m'),
                'end_date': end_date.strftime('%Y-%m'),
                'achievements': random.sample([
                    'Improved performance by 40%',
                    'Led team of 5+ engineers',
                    'Reduced costs by 30%',
                    'Implemented new system',
                    'Mentored junior developers',
                    'Architected microservices',
                    'Published research paper'
                ], k=random.randint(1, 3))
            })
        
        return history
    
    def _create_resume_text(self, name: str, title: str, years: int, 
                           education: str, skills: List[str], 
                           soft_skills: List[str], work_history: List[Dict]) -> str:
        """Create human-readable resume text"""
        text = f"""
{name}
{title}

Professional Summary:
Experienced {title.lower()} with {years} years of industry experience.
Proficient in {', '.join(skills[:5])}.

Education:
{education}

Technical Skills:
{', '.join(skills)}

Soft Skills:
{', '.join(soft_skills)}

Professional Experience:
"""
        for job in work_history:
            text += f"""
{job['position']} at {job['company']}
{job['start_date']} to {job['end_date']} ({job['duration_years']} years)
Achievements:
"""
            for achievement in job['achievements']:
                text += f"• {achievement}\n"
        
        return text
    
    def _create_clean_text(self, resume_text: str) -> str:
        """Create cleaned text for embedding (remove personal identifiers)"""
        import re
        clean = resume_text.lower()
        # Remove names and personal details (this mimics fairness preprocessing)
        clean = re.sub(r'\b[a-z]+ [a-z]+\b', '[PERSON]', clean)
        return clean
    
    def generate_dataset(self, total_resumes: int = 600, 
                        balance_groups: bool = True) -> Tuple[List[Dict], Dict]:
        """
        Generate balanced synthetic dataset with controlled sensitive attributes
        
        Args:
            total_resumes: Total number of resumes to generate
            balance_groups: If True, balance gender and experience groups for fair metrics
        
        Returns:
            Tuple of (resumes_list, metadata)
        """
        
        logger.info(f"🔄 Generating {total_resumes} synthetic resumes...")
        
        resumes = []
        
        if balance_groups:
            # Balanced distribution
            per_group = total_resumes // (len(self.GENDERS) * len(self.JOB_TITLES_BY_EXPERIENCE))
            
            for gender in self.GENDERS:
                for exp_level in self.JOB_TITLES_BY_EXPERIENCE.keys():
                    for i in range(per_group):
                        resume_id = len(resumes)
                        resume = self.generate_resume(resume_id, gender, exp_level)
                        resumes.append(resume)
                        
                        if (resume_id + 1) % 100 == 0:
                            logger.info(f"  ✓ Generated {resume_id + 1} resumes")
        else:
            # Random distribution
            for i in range(total_resumes):
                gender = random.choice(self.GENDERS)
                exp_level = random.choice(list(self.JOB_TITLES_BY_EXPERIENCE.keys()))
                resume = self.generate_resume(i, gender, exp_level)
                resumes.append(resume)
                
                if (i + 1) % 100 == 0:
                    logger.info(f"  ✓ Generated {i + 1} resumes")
        
        # Compute metadata
        metadata = {
            'total_resumes': len(resumes),
            'generation_date': datetime.now().isoformat(),
            'seed': self.seed,
            'balanced': balance_groups,
            'gender_distribution': self._compute_distribution([r['gender'] for r in resumes]),
            'experience_distribution': self._compute_distribution([r['experience_level'] for r in resumes]),
            'avg_skills': np.mean([len(r['skills']) for r in resumes]),
            'avg_experience_years': np.mean([r['years_experience'] for r in resumes])
        }
        
        logger.info(f"✅ Dataset generated: {len(resumes)} resumes")
        logger.info(f"   Metadata: {json.dumps(metadata, indent=2, default=str)}")
        
        return resumes, metadata
    
    def _compute_distribution(self, values: List) -> Dict[str, float]:
        """Compute value distribution as percentages"""
        total = len(values)
        dist = {}
        for v in set(values):
            dist[v] = round(100 * values.count(v) / total, 2)
        return dist
    
    # ============================================================================
    # SAVE & LOAD
    # ============================================================================
    
    def save_dataset(self, resumes: List[Dict], metadata: Dict, filename: str):
        """Save dataset to JSON file"""
        output = {
            'metadata': metadata,
            'resumes': resumes
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        logger.info(f"✅ Dataset saved to: {filename}")
    
    def load_dataset(self, filename: str) -> Tuple[List[Dict], Dict]:
        """Load dataset from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        logger.info(f"✅ Dataset loaded from: {filename}")
        return data['resumes'], data['metadata']


# ============================================================================
# MAIN: RUN GENERATOR
# ============================================================================

if __name__ == "__main__":
    generator = SyntheticResumeGenerator(seed=42)
    
    # Generate 600 synthetic resumes (balanced groups)
    resumes, metadata = generator.generate_dataset(
        total_resumes=600,
        balance_groups=True
    )
    
    # Save to file
    generator.save_dataset(
        resumes, 
        metadata,
        'fairxai_synthetic_resumes_600.json'
    )
    
    # Print summary
    print("\n" + "="*80)
    print("SYNTHETIC DATASET GENERATION SUMMARY")
    print("="*80)
    print(f"Total Resumes: {metadata['total_resumes']}")
    print(f"\nGender Distribution:")
    for gender, pct in metadata['gender_distribution'].items():
        print(f"  {gender}: {pct}%")
    print(f"\nExperience Level Distribution:")
    for level, pct in metadata['experience_distribution'].items():
        print(f"  {level}: {pct}%")
    print(f"\nAverage Skills per Resume: {metadata['avg_skills']:.2f}")
    print(f"Average Experience: {metadata['avg_experience_years']:.2f} years")
    print(f"\nFile: fairxai_synthetic_resumes_600.json")
    print("="*80)
