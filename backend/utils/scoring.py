"""
Scoring System
ATS score calculation and skill gap analysis
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ATSScorer:
    """
    ATS (Applicant Tracking System) Score Calculator
    Evaluates resume completeness and formatting
    """
    
    # Scoring weights
    WEIGHTS = {
        'contact_info': 15,
        'skills': 25,
        'experience': 30,
        'education': 20,
        'length': 10
    }
    
    @staticmethod
    def calculate_ats_score(parsed_data: Dict) -> Dict:
        """
        Calculate ATS score based on resume completeness
        
        Args:
            parsed_data: Dictionary with parsed resume data
            
        Returns:
            {
                'score': float,
                'max_score': 100,
                'percentage': float,
                'breakdown': dict,
                'grade': str,
                'suggestions': list
            }
        """
        score = 0
        breakdown = {}
        suggestions = []
        
        # 1. Contact Information (15 points)
        contact_score = 0
        if parsed_data.get('email'):
            contact_score += 10
            breakdown['email'] = 10
        else:
            suggestions.append("Add your email address")
            
        if parsed_data.get('phone'):
            contact_score += 5
            breakdown['phone'] = 5
        else:
            suggestions.append("Add your phone number")
            
        score += contact_score
        
        # 2. Skills Section (25 points)
        skills = parsed_data.get('skills', [])
        skills_count = len(skills)
        
        if skills_count >= 10:
            skills_score = 25
        elif skills_count >= 7:
            skills_score = 20
        elif skills_count >= 5:
            skills_score = 15
        elif skills_count >= 3:
            skills_score = 10
        elif skills_count > 0:
            skills_score = 5
        else:
            skills_score = 0
            suggestions.append("Add technical skills to your resume")
        
        if skills_count < 7:
            suggestions.append(f"Add more skills (currently: {skills_count}, recommended: 7-10)")
        
        score += skills_score
        breakdown['skills'] = skills_score
        
        # 3. Experience Section (30 points)
        experience = parsed_data.get('experience', [])
        exp_count = len(experience)
        
        if exp_count >= 3:
            exp_score = 30
        elif exp_count == 2:
            exp_score = 20
        elif exp_count == 1:
            exp_score = 15
        else:
            exp_score = 0
            suggestions.append("Add work experience or projects")
        
        if exp_count < 2:
            suggestions.append("Add more experience entries or relevant projects")
        
        score += exp_score
        breakdown['experience'] = exp_score
        
        # 4. Education Section (20 points)
        education = parsed_data.get('education', [])
        edu_count = len(education)
        
        if edu_count >= 1:
            edu_score = 20
        else:
            edu_score = 0
            suggestions.append("Add your education details")
        
        score += edu_score
        breakdown['education'] = edu_score
        
        # 5. Resume Length (10 points)
        word_count = parsed_data.get('word_count', 0)
        
        if 400 <= word_count <= 800:  # Ideal: 1-2 pages
            length_score = 10
        elif 300 <= word_count <= 1000:
            length_score = 7
        elif 200 <= word_count < 300:
            length_score = 4
            suggestions.append("Resume is too short. Add more details.")
        elif word_count > 1000:
            length_score = 5
            suggestions.append("Resume is too long. Keep it concise (1-2 pages).")
        else:
            length_score = 0
            suggestions.append("Resume appears incomplete")
        
        score += length_score
        breakdown['length'] = length_score
        
        # Calculate grade
        grade = ATSScorer._get_grade(score)
        
        logger.info(f"ATS Score calculated: {score}/100 (Grade: {grade})")
        
        return {
            'score': round(score, 2),
            'max_score': 100,
            'percentage': round(score, 2),
            'breakdown': breakdown,
            'grade': grade,
            'suggestions': suggestions
        }
    
    @staticmethod
    def _get_grade(score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        else:
            return 'D'

class SkillGapAnalyzer:
    """
    Analyze skill gaps between resume and job requirements
    """
    
    @staticmethod
    def analyze(resume_skills: List[str], jd_skills: List[str]) -> Dict:
        """
        Basic skill gap analysis (exact matching)
        Note: Use TextProcessor.calculate_skill_similarity() for semantic matching
        
        Args:
            resume_skills: Skills from resume
            jd_skills: Required skills from JD
            
        Returns:
            Skill gap analysis
        """
        if not jd_skills:
            return {
                'matched_skills': [],
                'missing_skills': [],
                'match_percentage': 0,
                'total_required': 0,
                'total_matched': 0
            }
        
        # Convert to lowercase for comparison
        resume_skills_lower = [s.lower().strip() for s in resume_skills]
        jd_skills_lower = [s.lower().strip() for s in jd_skills]
        
        # Find matches (exact)
        matched = []
        missing = []
        
        for jd_skill in jd_skills:
            if jd_skill.lower().strip() in resume_skills_lower:
                matched.append(jd_skill)
            else:
                missing.append(jd_skill)
        
        match_percentage = (len(matched) / len(jd_skills) * 100) if jd_skills else 0
        
        logger.info(f"Skill Gap: {len(matched)}/{len(jd_skills)} skills matched")
        
        return {
            'matched_skills': matched,
            'missing_skills': missing,
            'match_percentage': round(match_percentage, 2),
            'total_required': len(jd_skills),
            'total_matched': len(matched)
        }