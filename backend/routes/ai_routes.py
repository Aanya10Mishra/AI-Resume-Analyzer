"""
AI-Powered Routes
Features: AI resume suggestions, career advice, interview prep
"""
from flask import Blueprint, request, jsonify
from models.database import db, Resume, JobDescription, ResumeAnalysis
from utils import ATSScorer
from utils.ai_integration import GroqAI, OnetAPI
import logging

logger = logging.getLogger(__name__)

# Create blueprint
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# Initialize AI services
groq_ai = None
onet_api = None
ats_scorer = None

def init_ai_routes(ats):
    """Initialize AI routes with utilities"""
    global groq_ai, onet_api, ats_scorer
    
    groq_ai = GroqAI()
    onet_api = OnetAPI()
    ats_scorer = ats
    
    logger.info("✅ AI routes initialized")
    logger.info("   - Groq AI: " + ("Enabled" if groq_ai.client else "Fallback mode"))
    logger.info("   - O*NET API: " + ("Configured" if onet_api.auth else "Public access"))

@ai_bp.route('/improve-resume/<int:resume_id>', methods=['GET'])
def improve_resume(resume_id):
    """
    Get AI-powered resume improvement suggestions
    
    Uses Groq AI (Llama 3) to analyze resume and provide specific improvements
    """
    try:
        logger.info(f"🤖 Generating AI suggestions for resume {resume_id}")
        
        # Get resume
        resume = Resume.query.get(resume_id)
        
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        # Get parsed data and ATS score
        parsed_data = resume.get_parsed_data()
        ats_result = ats_scorer.calculate_ats_score(parsed_data)
        
        # Generate AI suggestions
        ai_suggestions = groq_ai.generate_resume_suggestions(parsed_data, ats_result)
        
        # Categorize by priority
        high_priority = [s for s in ai_suggestions if s.get('priority') == 'high']
        medium_priority = [s for s in ai_suggestions if s.get('priority') == 'medium']
        low_priority = [s for s in ai_suggestions if s.get('priority') == 'low']
        
        # Calculate potential impact
        potential_improvement = len(high_priority) * 5 + len(medium_priority) * 3 + len(low_priority) * 1
        potential_ats_score = min(ats_result['percentage'] + potential_improvement, 100)
        
        response = {
            'resume_id': resume_id,
            'current_ats_score': ats_result['percentage'],
            'potential_ats_score': potential_ats_score,
            'improvement_potential': potential_improvement,
            'ai_suggestions': ai_suggestions,
            'suggestions_by_priority': {
                'high': high_priority,
                'medium': medium_priority,
                'low': low_priority
            },
            'total_suggestions': len(ai_suggestions),
            'powered_by': 'Groq AI (Llama 3.1)'
        }
        
        logger.info(f"✅ Generated {len(ai_suggestions)} AI suggestions for resume {resume_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ AI suggestions error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/career-advice/<int:user_id>', methods=['POST'])
def career_advice(user_id):
    """
    Get personalized AI career advice
    
    Body (optional): { "target_role": "Senior Software Engineer" }
    """
    try:
        logger.info(f"🎯 Generating career advice for user {user_id}")
        
        # Get latest resume
        resume = Resume.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).first()
        
        if not resume:
            return jsonify({
                'error': 'No resume found',
                'message': 'Please upload a resume first'
            }), 404
        
        # Get target role from request body (optional)
        data = request.get_json() or {}
        target_role = data.get('target_role')
        
        # Get parsed data
        parsed_data = resume.get_parsed_data()
        
        # Generate AI career advice
        career_advice_data = groq_ai.generate_career_advice(parsed_data, target_role)
        
        # Get O*NET career recommendations
        current_skills = parsed_data.get('skills', [])
        skill_keywords = ' '.join(current_skills[:5]) if current_skills else 'software developer'
        
        onet_careers = onet_api.search_careers(skill_keywords, limit=5)
        
        response = {
            'user_id': user_id,
            'target_role': target_role,
            'current_profile': {
                'skills_count': len(current_skills),
                'experience_count': len(parsed_data.get('experience', [])),
                'top_skills': current_skills[:5]
            },
            'ai_advice': career_advice_data,
            'recommended_careers': onet_careers,
            'next_steps': _generate_next_steps(parsed_data, target_role),
            'powered_by': 'Groq AI + O*NET Database'
        }
        
        logger.info(f"✅ Generated career advice for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Career advice error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/interview-prep/<int:resume_id>/<int:jd_id>', methods=['GET'])
def interview_prep(resume_id, jd_id):
    """
    Generate AI-powered interview preparation guide
    
    Provides likely questions, answer strategies, and tips
    """
    try:
        logger.info(f"📝 Generating interview prep: Resume {resume_id} vs JD {jd_id}")
        
        # Get resume and JD
        resume = Resume.query.get(resume_id)
        jd = JobDescription.query.get(jd_id)
        
        if not resume or not jd:
            return jsonify({'error': 'Resume or JD not found'}), 404
        
        # Get parsed data
        parsed_data = resume.get_parsed_data()
        jd_data = {
            'title': jd.title,
            'company': jd.company,
            'description': jd.description,
            'requirements': jd.requirements
        }
        
        # Generate interview prep
        interview_guide = groq_ai.generate_interview_prep(parsed_data, jd_data)
        
        # Get analysis if exists
        analysis = ResumeAnalysis.query.filter_by(
            resume_id=resume_id,
            jd_id=jd_id
        ).first()
        
        # Generate preparation checklist
        prep_checklist = _generate_prep_checklist(parsed_data, jd_data, analysis)
        
        response = {
            'resume_id': resume_id,
            'jd_id': jd_id,
            'job_title': jd.title,
            'company': jd.company,
            'interview_guide': interview_guide,
            'preparation_checklist': prep_checklist,
            'strengths_to_highlight': _identify_strengths(parsed_data, jd),
            'potential_weaknesses': _identify_weaknesses(parsed_data, jd),
            'match_score': analysis.match_score if analysis else None,
            'powered_by': 'Groq AI (Llama 3.1)'
        }
        
        logger.info(f"✅ Generated interview prep for resume {resume_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Interview prep error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/career-path/<int:user_id>', methods=['GET'])
def career_path(user_id):
    """
    Generate career path roadmap with O*NET data
    """
    try:
        logger.info(f"🗺️  Generating career path for user {user_id}")
        
        # Get latest resume
        resume = Resume.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).first()
        
        if not resume:
            return jsonify({'error': 'No resume found'}), 404
        
        parsed_data = resume.get_parsed_data()
        current_skills = parsed_data.get('skills', [])
        
        # Search for career options
        skill_query = ' '.join(current_skills[:3]) if current_skills else 'software'
        careers = onet_api.search_careers(skill_query, limit=8)
        
        # Get details for top 3 careers
        career_details = []
        for career in careers[:3]:
            if career.get('code'):
                details = onet_api.get_career_details(career['code'])
                outlook = onet_api.get_career_outlook(career['code'])
                
                career_details.append({
                    'title': career['title'],
                    'code': career['code'],
                    'description': career.get('description', details.get('description', '')),
                    'required_skills': details.get('skills', [])[:5],
                    'outlook': outlook
                })
        
        # Generate roadmap
        roadmap = _generate_career_roadmap(parsed_data, career_details)
        
        response = {
            'user_id': user_id,
            'current_skills': current_skills,
            'career_options': careers,
            'detailed_paths': career_details,
            'recommended_roadmap': roadmap,
            'data_source': 'O*NET Career Database'
        }
        
        logger.info(f"✅ Generated career path for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Career path error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/skill-recommendations/<int:resume_id>', methods=['GET'])
def skill_recommendations(resume_id):
    """
    Get AI-powered skill learning recommendations
    """
    try:
        logger.info(f"📚 Generating skill recommendations for resume {resume_id}")
        
        resume = Resume.query.get(resume_id)
        
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        parsed_data = resume.get_parsed_data()
        current_skills = parsed_data.get('skills', [])
        
        # Get recent job matches to understand market demand
        recent_analyses = ResumeAnalysis.query.filter_by(
            resume_id=resume_id
        ).order_by(ResumeAnalysis.analyzed_at.desc()).limit(5).all()
        
        # Collect missing skills from recent job matches
        missing_skills = set()
        for analysis in recent_analyses:
            gaps = analysis.get_skill_gaps()
            missing_skills.update(gaps[:5])
        
        # Generate AI recommendations for skill development
        skill_prompt = f"""Current skills: {', '.join(current_skills[:10])}
Market demand shows these missing skills: {', '.join(list(missing_skills)[:10])}

Recommend top 5 skills to learn next with reasoning."""
        
        # Use Groq for recommendations
        if groq_ai.client:
            try:
                response = groq_ai.client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a career advisor specializing in tech skills. Recommend practical skills with clear learning paths."
                        },
                        {
                            "role": "user",
                            "content": skill_prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=800
                )
                
                recommendations = response.choices[0].message.content
            except:
                recommendations = "Focus on cloud technologies, system design, and modern frameworks based on market trends."
        else:
            recommendations = "Focus on in-demand skills like cloud computing, DevOps, and system architecture."
        
        # Learning resources
        resources = _map_skill_resources(list(missing_skills)[:5])
        
        response_data = {
            'resume_id': resume_id,
            'current_skills': current_skills,
            'skill_gaps_identified': list(missing_skills),
            'ai_recommendations': recommendations,
            'learning_resources': resources,
            'priority_skills': list(missing_skills)[:5],
            'powered_by': 'Groq AI + Market Analysis'
        }
        
        logger.info(f"✅ Generated skill recommendations for resume {resume_id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Skill recommendations error: {e}")
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/optimize-for-job/<int:resume_id>/<int:jd_id>', methods=['GET'])
def optimize_for_job(resume_id, jd_id):
    """
    Get specific optimization tips for a target job
    """
    try:
        logger.info(f"🎯 Optimizing resume {resume_id} for JD {jd_id}")
        
        resume = Resume.query.get(resume_id)
        jd = JobDescription.query.get(jd_id)
        
        if not resume or not jd:
            return jsonify({'error': 'Resume or JD not found'}), 404
        
        parsed_data = resume.get_parsed_data()
        
        # Build optimization prompt
        optimization_prompt = f"""Job Title: {jd.title}
Job Description: {jd.description[:500]}

Resume Skills: {', '.join(parsed_data.get('skills', [])[:10])}

Provide 5 specific ways to optimize this resume for this exact job."""
        
        if groq_ai.client:
            try:
                response = groq_ai.client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an ATS optimization expert. Provide specific, actionable changes to improve resume-job match."
                        },
                        {
                            "role": "user",
                            "content": optimization_prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                optimizations = response.choices[0].message.content
            except:
                optimizations = "Tailor your experience descriptions to match job requirements. Add relevant keywords naturally."
        else:
            optimizations = "Focus on keywords from the job description and quantify your achievements."
        
        # Get keyword analysis
        jd_keywords = _extract_keywords(jd.description)
        resume_keywords = _extract_keywords(parsed_data.get('raw_text', ''))
        missing_keywords = [k for k in jd_keywords if k.lower() not in resume_keywords]
        
        response_data = {
            'resume_id': resume_id,
            'jd_id': jd_id,
            'job_title': jd.title,
            'optimizations': optimizations,
            'keyword_analysis': {
                'jd_keywords': jd_keywords[:10],
                'missing_from_resume': missing_keywords[:10],
                'matched_keywords': [k for k in jd_keywords if k.lower() in resume_keywords][:10]
            },
            'quick_wins': [
                f"Add keywords: {', '.join(missing_keywords[:5])}",
                "Quantify achievements with numbers",
                "Mirror job description language",
                "Emphasize relevant experience first"
            ],
            'powered_by': 'Groq AI'
        }
        
        logger.info(f"✅ Generated optimization tips for resume {resume_id}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Optimization error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== HELPER FUNCTIONS ====================

def _generate_next_steps(parsed_data, target_role):
    """Generate actionable next steps"""
    
    steps = []
    current_skills = parsed_data.get('skills', [])
    
    if len(current_skills) < 10:
        steps.append({
            'action': 'Expand Your Skills',
            'description': 'Add 3-5 more relevant technical skills',
            'timeline': '1-2 months',
            'priority': 'high'
        })
    
    if target_role:
        steps.append({
            'action': f'Research {target_role} Requirements',
            'description': 'Study job postings to identify common requirements',
            'timeline': '1 week',
            'priority': 'high'
        })
    
    steps.append({
        'action': 'Build Portfolio Projects',
        'description': 'Create 2-3 projects showcasing your skills',
        'timeline': '2-3 months',
        'priority': 'medium'
    })
    
    steps.append({
        'action': 'Network Actively',
        'description': 'Connect with professionals on LinkedIn, attend meetups',
        'timeline': 'Ongoing',
        'priority': 'medium'
    })
    
    return steps

def _generate_prep_checklist(parsed_data, jd_data, analysis):
    """Generate interview preparation checklist"""
    
    checklist = [
        {
            'item': 'Research the Company',
            'details': f'Study {jd_data.get("company", "the company")}, its products, culture, and recent news',
            'completed': False
        },
        {
            'item': 'Review Your Resume',
            'details': 'Be ready to discuss every point on your resume in detail',
            'completed': False
        },
        {
            'item': 'Prepare STAR Stories',
            'details': 'Prepare 5-7 stories using Situation-Task-Action-Result format',
            'completed': False
        },
        {
            'item': 'Technical Preparation',
            'details': 'Review core concepts related to the role',
            'completed': False
        },
        {
            'item': 'Prepare Questions',
            'details': 'Have 5+ thoughtful questions ready to ask interviewers',
            'completed': False
        },
        {
            'item': 'Practice Common Questions',
            'details': 'Practice answers to "Tell me about yourself", "Why this company?", etc.',
            'completed': False
        }
    ]
    
    if analysis and analysis.match_score:
        if analysis.match_score < 70:
            checklist.append({
                'item': 'Address Skill Gaps',
                'details': 'Prepare to discuss how you plan to address missing skills',
                'completed': False
            })
    
    return checklist

def _identify_strengths(parsed_data, jd):
    """Identify candidate strengths for the role"""
    
    resume_skills = set([s.lower() for s in parsed_data.get('skills', [])])
    jd_skills = set([s.lower() for s in jd.get_parsed_skills()])
    
    matched_skills = resume_skills.intersection(jd_skills)
    
    strengths = [
        f"Strong match on {len(matched_skills)} required skills",
        f"Relevant experience: {len(parsed_data.get('experience', []))} positions"
    ]
    
    if parsed_data.get('linkedin'):
        strengths.append("Professional online presence (LinkedIn)")
    
    if parsed_data.get('github'):
        strengths.append("Technical portfolio (GitHub)")
    
    return strengths

def _identify_weaknesses(parsed_data, jd):
    """Identify potential weaknesses to prepare for"""
    
    resume_skills = set([s.lower() for s in parsed_data.get('skills', [])])
    jd_skills = set([s.lower() for s in jd.get_parsed_skills()])
    
    missing_skills = jd_skills - resume_skills
    
    weaknesses = []
    
    if missing_skills:
        weaknesses.append(f"Missing skills: {', '.join(list(missing_skills)[:3])}")
    
    if len(parsed_data.get('experience', [])) < 2:
        weaknesses.append("Limited work experience")
    
    return weaknesses if weaknesses else ["None identified - strong candidate"]

def _generate_career_roadmap(parsed_data, career_details):
    """Generate career progression roadmap"""
    
    roadmap = {
        'current_level': 'Based on your profile',
        'short_term': [],
        'medium_term': [],
        'long_term': []
    }
    
    current_skills = len(parsed_data.get('skills', []))
    experience_count = len(parsed_data.get('experience', []))
    
    # Determine level
    if experience_count < 2:
        level = 'Entry/Junior'
    elif experience_count < 5:
        level = 'Mid-Level'
    else:
        level = 'Senior'
    
    roadmap['current_level'] = level
    
    # Short term (0-6 months)
    roadmap['short_term'] = [
        'Master current role responsibilities',
        'Expand technical skills',
        'Build portfolio projects'
    ]
    
    # Medium term (6-18 months)
    if career_details:
        first_career = career_details[0]
        roadmap['medium_term'] = [
            f'Target role: {first_career.get("title")}',
            f'Acquire skills: {", ".join(first_career.get("required_skills", [])[:3])}',
            'Network in target industry'
        ]
    else:
        roadmap['medium_term'] = [
            'Take on leadership opportunities',
            'Mentor junior team members',
            'Contribute to strategic projects'
        ]
    
    # Long term (18+ months)
    roadmap['long_term'] = [
        'Senior/Lead position',
        'Technical or people management track',
        'Industry recognition and influence'
    ]
    
    return roadmap

def _map_skill_resources(skills):
    """Map skills to learning resources"""
    
    resource_catalog = {
        'python': ['Python.org', 'Real Python', 'Codecademy'],
        'javascript': ['MDN Web Docs', 'JavaScript.info', 'freeCodeCamp'],
        'react': ['React Docs', 'freeCodeCamp React', 'Scrimba'],
        'aws': ['AWS Skill Builder', 'A Cloud Guru', 'AWS Free Tier'],
        'docker': ['Docker Docs', 'Docker Getting Started', 'Kubernetes Basics'],
        'sql': ['SQLZoo', 'Mode Analytics', 'Khan Academy SQL'],
        'machine learning': ['Coursera ML', 'fast.ai', 'Kaggle Learn'],
        'system design': ['System Design Primer', 'Grokking System Design']
    }
    
    resources = []
    for skill in skills:
        skill_lower = skill.lower()
        for key, res in resource_catalog.items():
            if key in skill_lower:
                resources.append({
                    'skill': skill,
                    'resources': res
                })
                break
    
    return resources

def _extract_keywords(text):
    """Extract important keywords from text"""
    
    # Simple keyword extraction (can be enhanced)
    common_keywords = [
        'python', 'java', 'javascript', 'react', 'node', 'sql', 
        'aws', 'docker', 'kubernetes', 'agile', 'scrum', 'git',
        'leadership', 'management', 'architecture', 'design',
        'development', 'engineering', 'testing', 'ci/cd'
    ]
    
    text_lower = text.lower()
    found_keywords = []
    
    for keyword in common_keywords:
        if keyword in text_lower:
            found_keywords.append(keyword)
    
    return found_keywords