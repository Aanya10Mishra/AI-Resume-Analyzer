"""
Extract REAL resumes + JDs from your database with better evaluation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app
from backend.models.database import db, Resume, JobDescription
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_real_data(resume_limit=50, jd_limit=50):
    """Extract real data from database with quality checks"""
    
    app = create_app('development')
    
    with app.app_context():
        logger.info("📂 Extracting real data from database...")
        
        # Get resumes
        resumes = Resume.query.limit(resume_limit).all()
        resume_texts = []
        resume_ids = []
        
        for r in resumes:
            try:
                data = r.get_parsed_data()
                
                # Combine multiple fields for rich text
                skills = " ".join(data.get('skills', []))
                
                exp_texts = []
                for exp in data.get('experience', []):
                    title = exp.get('title', '')
                    company = exp.get('company', '')
                    desc = exp.get('description', '')
                    exp_texts.append(f"{title} at {company} {desc}")
                
                experiences = " ".join(exp_texts)
                
                education = " ".join([
                    f"{e.get('degree')} in {e.get('field')}" 
                    for e in data.get('education', [])
                ])
                
                summary = data.get('summary', '')
                
                # Combine all
                text = f"{summary} {skills} {experiences} {education}".strip()
                
                # Only use resumes with substantial content
                if len(text) > 100:
                    resume_texts.append(text)
                    resume_ids.append(r.id)
                    
            except Exception as e:
                logger.warning(f"⚠️ Resume {r.id}: {e}")
                continue
        
        logger.info(f"✅ Extracted {len(resume_texts)} quality resumes")
        
        # Get JDs
        jds = JobDescription.query.limit(jd_limit).all()
        jd_texts = []
        jd_ids = []
        
        for jd in jds:
            try:
                # Combine all JD fields
                text = f"{jd.title} {jd.description} {jd.requirements}".strip()
                
                if len(text) > 50:
                    jd_texts.append(text)
                    jd_ids.append(jd.id)
                    
            except Exception as e:
                logger.warning(f"⚠️ JD {jd.id}: {e}")
                continue
        
        logger.info(f"✅ Extracted {len(jd_texts)} quality JDs")
        
        # Show stats
        if resume_texts:
            avg_resume_len = sum(len(r) for r in resume_texts) / len(resume_texts)
            logger.info(f"   Avg resume length: {avg_resume_len:.0f} chars")
        
        if jd_texts:
            avg_jd_len = sum(len(j) for j in jd_texts) / len(jd_texts)
            logger.info(f"   Avg JD length: {avg_jd_len:.0f} chars")
        
        return resume_texts, jd_texts, resume_ids, jd_ids

if __name__ == "__main__":
    resumes, jds, resume_ids, jd_ids = extract_real_data(resume_limit=50, jd_limit=50)
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"   Resumes: {len(resumes)}")
    logger.info(f"   JDs: {len(jds)}")
    logger.info(f"   Combinations to test: {len(resumes)} × {len(jds)} = {len(resumes) * len(jds)}")
    
    if resumes and jds:
        logger.info(f"\n📄 Sample Resume (first 300 chars):")
        logger.info(resumes[0][:300] + "...")
        
        logger.info(f"\n📋 Sample JD (first 300 chars):")
        logger.info(jds[0][:300] + "...")
        
        # Save for experiments
        with open('real_data.json', 'w') as f:
            json.dump({
                'resumes': resumes,
                'jds': jds,
                'resume_ids': resume_ids,
                'jd_ids': jd_ids,
                'count': {
                    'resumes': len(resumes),
                    'jds': len(jds)
                }
            }, f)
        logger.info(f"\n✅ Saved to real_data.json")
