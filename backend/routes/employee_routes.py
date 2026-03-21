"""
Employee Routes
Features for experienced professionals
Focus: Career growth, job switching, upskilling, senior roles
"""
from flask import Blueprint, request, jsonify
from models.database import db, Resume, ResumeAnalysis, JobDescription
from utils import TextProcessor, ATSScorer
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create blueprint
employee_bp = Blueprint('employee', __name__, url_prefix='/api/employee')

# Global variables (initialized from app.py)
text_processor = None
ats_scorer = None

def init_employee_routes(tp, ats):
    """Initialize with utility instances"""
    global text_processor, ats_scorer
    text_processor = tp
    ats_scorer = ats
    logger.info("✅ Employee routes initialized")

@employee_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def employee_dashboard(user_id):
    """
    Employee Dashboard - Career Growth Focus
    Shows: Resume stats, application history, growth areas, salary insights
    """
    try:
        logger.info(f"📊 Loading employee dashboard for user {user_id}")
        
        # Get user's resumes
        resumes = Resume.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).limit(10).all()
        
        # Get recent analyses
        recent_analyses = []
        if resumes:
            resume_ids = [r.id for r in resumes]
            recent_analyses = ResumeAnalysis.query.filter(
                ResumeAnalysis.resume_id.in_(resume_ids)
            ).order_by(ResumeAnalysis.analyzed_at.desc()).limit(10).all()
        
        # Calculate statistics
        total_resumes = len(resumes)
        total_analyses = len(recent_analyses)
        avg_ats_score = 0
        avg_match_score = 0
        best_resume = None
        
        if resumes:
            ats_scores = []
            for r in resumes:
                parsed = r.get_parsed_data()
                score = ats_scorer.calculate_ats_score(parsed)
                ats_scores.append(score['percentage'])
            
            avg_ats_score = sum(ats_scores) / len(ats_scores)
            best_resume = max(
                resumes, 
                key=lambda r: ats_scorer.calculate_ats_score(
                    r.get_parsed_data()
                )['percentage']
            )
        
        if recent_analyses:
            match_scores = [a.match_score for a in recent_analyses if a.match_score]
            avg_match_score = sum(match_scores) / len(match_scores) if match_scores else 0
        
        # Generate insights
        growth_recommendations = _generate_growth_recommendations(resumes, recent_analyses)
        career_insights = _generate_career_insights(best_resume, recent_analyses)
        salary_insights = _get_salary_insights(best_resume)
        
        response = {
            'user_id': user_id,
            'role': 'employee',
            'statistics': {
                'total_resumes': total_resumes,
                'average_ats_score': round(avg_ats_score, 2),
                'average_match_score': round(avg_match_score, 2),
                'total_analyses': total_analyses,
                'profile_strength': _calculate_profile_strength(best_resume)
            },
            'best_resume': {
                'id': best_resume.id,
                'filename': best_resume.filename,
                'ats_score': ats_scorer.calculate_ats_score(
                    best_resume.get_parsed_data()
                )['percentage'],
                'uploaded_at': best_resume.uploaded_at.isoformat()
            } if best_resume else None,
            'recent_resumes': [
                {
                    'id': r.id,
                    'filename': r.filename,
                    'uploaded_at': r.uploaded_at.isoformat(),
                    'ats_score': ats_scorer.calculate_ats_score(
                        r.get_parsed_data()
                    )['percentage']
                }
                for r in resumes[:5]
            ],
            'recent_analyses': [
                {
                    'id': a.id,
                    'match_score': a.match_score,
                    'ats_score': a.ats_score,
                    'jd_title': a.job_description.title if a.job_description else 'N/A',
                    'jd_company': a.job_description.company if a.job_description else 'N/A',
                    'analyzed_at': a.analyzed_at.isoformat()
                }
                for a in recent_analyses[:5]
            ],
            'growth_recommendations': growth_recommendations,
            'career_insights': career_insights,
            'salary_insights': salary_insights
        }
        
        logger.info(f"✅ Dashboard loaded for employee {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Employee dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/career-growth/<int:user_id>', methods=['GET'])
def career_growth(user_id):
    """
    Career Growth Analysis
    Suggests: Next role progression, salary growth, skill development
    """
    try:
        logger.info(f"🎯 Analyzing career growth for user {user_id}")
        
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
        
        parsed_data = resume.get_parsed_data()
        current_skills = parsed_data.get('skills', [])
        experience = parsed_data.get('experience', [])
        
        # Detect current level
        current_level = _detect_experience_level(experience)
        
        # Career progression paths
        progression_paths = _get_career_progression(current_level)
        
        # Find matching next roles using embeddings
        next_role_options = progression_paths['next_roles']
        career_matches = text_processor.find_career_matches(
            resume.raw_text,
            next_role_options,
            top_n=5
        )
        
        # Generate upskilling path for top career
        top_career = career_matches[0]['career'] if career_matches else None
        upskilling_plan = _generate_upskilling_plan(current_skills, top_career)
        
        # Get required skills for target role
        target_skills = _get_skills_for_role(top_career) if top_career else []
        skill_analysis = text_processor.calculate_skill_similarity(
            current_skills,
            target_skills
        ) if target_skills else {}
        
        response = {
            'user_id': user_id,
            'current_level': current_level,
            'current_skills': current_skills,
            'experience_count': len(experience),
            'career_progression': {
                'current': progression_paths['current'],
                'next_roles': career_matches,
                'future_paths': progression_paths['future_paths']
            },
            'top_recommendation': {
                'career': top_career,
                'fit_score': career_matches[0]['similarity'] if career_matches else 0,
                'description': _get_career_description(top_career),
                'avg_salary_range': _get_salary_range(top_career)
            } if top_career else None,
            'skill_analysis': skill_analysis,
            'upskilling_plan': upskilling_plan,
            'estimated_timeline': _estimate_transition_timeline(skill_analysis, upskilling_plan)
        }
        
        logger.info(f"✅ Career growth analysis complete for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Career growth error: {e}")
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/job-switch/<int:user_id>', methods=['GET'])
def job_switch_analysis(user_id):
    """
    Job Switch Readiness Analysis
    Analyzes if candidate is ready for senior/leadership roles
    """
    try:
        logger.info(f"🔄 Analyzing job switch readiness for user {user_id}")
        
        resume = Resume.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).first()
        
        if not resume:
            return jsonify({'error': 'No resume found'}), 404
        
        parsed = resume.get_parsed_data()
        ats_result = ats_scorer.calculate_ats_score(parsed)
        
        # Target roles for switching (senior/leadership)
        target_titles = [
            'Senior Software Engineer',
            'Staff Engineer',
            'Principal Engineer',
            'Tech Lead',
            'Engineering Manager',
            'Senior Data Scientist',
            'Lead Developer',
            'Solutions Architect'
        ]
        
        # Find best matches
        career_matches = text_processor.find_career_matches(
            resume.raw_text,
            target_titles,
            top_n=5
        )
        
        top_target = career_matches[0]['career'] if career_matches else None
        
        # Analyze skill readiness
        skill_analysis = {}
        readiness_score = 0
        
        if top_target:
            target_skills = _get_skills_for_role(top_target)
            skill_analysis = text_processor.calculate_skill_similarity(
                parsed.get('skills', []),
                target_skills
            )
            readiness_score = (
                ats_result['percentage'] * 0.3 +
                skill_analysis.get('match_percentage', 0) * 0.4 +
                career_matches[0]['similarity'] * 0.3
            )
        
        # Generate switch recommendation
        switch_recommendation = _generate_switch_recommendation(
            ats_result,
            skill_analysis,
            readiness_score
        )
        
        # Market insights
        market_insights = _get_market_insights(top_target)
        
        response = {
            'user_id': user_id,
            'current_resume': {
                'ats_score': ats_result['percentage'],
                'grade': ats_result['grade'],
                'skills_count': len(parsed.get('skills', [])),
                'experience_count': len(parsed.get('experience', []))
            },
            'target_roles': career_matches,
            'top_target': {
                'title': top_target,
                'fit_score': career_matches[0]['similarity'] if career_matches else 0
            } if top_target else None,
            'skill_analysis': skill_analysis,
            'readiness_score': round(readiness_score, 2),
            'recommendation': switch_recommendation,
            'market_insights': market_insights,
            'action_plan': _generate_action_plan(skill_analysis, switch_recommendation)
        }
        
        logger.info(f"✅ Job switch analysis complete for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Job switch analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/upskilling/<int:user_id>', methods=['GET'])
def upskilling_recommendations(user_id):
    """
    Personalized Upskilling Recommendations
    Based on career goals and market demand
    """
    try:
        logger.info(f"📚 Generating upskilling plan for user {user_id}")
        
        resume = Resume.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).first()
        
        if not resume:
            return jsonify({'error': 'No resume found'}), 404
        
        parsed = resume.get_parsed_data()
        current_skills = parsed.get('skills', [])
        
        # Get career targets
        target_careers = [
            'Senior Software Engineer',
            'Tech Lead',
            'Engineering Manager',
            'Solutions Architect',
            'Staff Engineer'
        ]
        
        career_matches = text_processor.find_career_matches(
            resume.raw_text,
            target_careers,
            top_n=3
        )
        
        target_career = career_matches[0]['career'] if career_matches else None
        
        # Generate comprehensive upskilling plan
        upskilling_plan = _generate_upskilling_plan(current_skills, target_career)
        
        # Learning resources
        resources = _map_learning_resources(upskilling_plan)
        
        # Certifications
        certifications = _recommend_certifications(current_skills, target_career)
        
        # Projects to build
        project_ideas = _suggest_projects(upskilling_plan[:3])
        
        response = {
            'user_id': user_id,
            'current_skills': current_skills,
            'skill_count': len(current_skills),
            'career_targets': career_matches,
            'primary_target': target_career,
            'upskilling_plan': upskilling_plan,
            'learning_resources': resources,
            'recommended_certifications': certifications,
            'project_ideas': project_ideas,
            'estimated_timeline': _calculate_upskilling_timeline(upskilling_plan)
        }
        
        logger.info(f"✅ Upskilling plan generated for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Upskilling recommendations error: {e}")
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/compare-market/<int:user_id>', methods=['GET'])
def compare_with_market(user_id):
    """
    Compare profile with market standards
    Shows how candidate stacks up against industry benchmarks
    """
    try:
        resume = Resume.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).first()
        
        if not resume:
            return jsonify({'error': 'No resume found'}), 404
        
        parsed = resume.get_parsed_data()
        ats_result = ats_scorer.calculate_ats_score(parsed)
        
        # Market benchmarks
        benchmarks = {
            'ats_score': {
                'user': ats_result['percentage'],
                'market_average': 72,
                'top_10_percent': 88,
                'status': 'above' if ats_result['percentage'] > 72 else 'below'
            },
            'skills_count': {
                'user': len(parsed.get('skills', [])),
                'market_average': 12,
                'top_performers': 18,
                'status': 'above' if len(parsed.get('skills', [])) > 12 else 'below'
            },
            'experience_count': {
                'user': len(parsed.get('experience', [])),
                'recommended': 3,
                'status': 'good' if len(parsed.get('experience', [])) >= 3 else 'needs_improvement'
            }
        }
        
        # Overall competitiveness
        competitiveness_score = _calculate_competitiveness(benchmarks)
        
        response = {
            'user_id': user_id,
            'benchmarks': benchmarks,
            'competitiveness_score': competitiveness_score,
            'standing': _get_market_standing(competitiveness_score),
            'improvement_areas': _identify_improvement_areas(benchmarks)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Market comparison error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== HELPER FUNCTIONS ====================

def _generate_growth_recommendations(resumes, analyses):
    """Generate personalized growth recommendations"""
    recommendations = []
    
    if not resumes:
        recommendations.append({
            'type': 'action',
            'priority': 'critical',
            'title': 'Upload Your Resume',
            'message': 'Add your latest resume to get personalized career insights',
            'action': 'Upload Resume',
            'impact': 'High'
        })
        return recommendations
    
    latest = resumes[0]
    parsed = latest.get_parsed_data()
    ats_result = ats_scorer.calculate_ats_score(parsed)
    
    # ATS score check
    if ats_result['percentage'] < 75:
        recommendations.append({
            'type': 'ats_improvement',
            'priority': 'high',
            'title': 'Improve ATS Score',
            'message': f'Your ATS score is {ats_result["percentage"]}%. Target: 80%+ for senior roles',
            'action': 'View Suggestions',
            'impact': 'High - Better visibility to recruiters'
        })
    
    # Skills check
    skills_count = len(parsed.get('skills', []))
    if skills_count < 10:
        recommendations.append({
            'type': 'skills',
            'priority': 'high',
            'title': 'Expand Your Skillset',
            'message': f'You have {skills_count} skills. Senior roles typically require 12-15+',
            'action': 'View Upskilling Plan',
            'impact': 'High - Increases job opportunities'
        })
    
    # Application activity
    if not analyses or len(analyses) < 5:
        recommendations.append({
            'type': 'applications',
            'priority': 'medium',
            'title': 'Increase Application Activity',
            'message': 'Apply to more senior positions to explore opportunities',
            'action': 'Find Senior Roles',
            'impact': 'Medium - Active job search'
        })
    
    # Experience highlighting
    experience_count = len(parsed.get('experience', []))
    if experience_count >= 3:
        recommendations.append({
            'type': 'leadership',
            'priority': 'medium',
            'title': 'Highlight Leadership Experience',
            'message': 'Emphasize team leadership, mentoring, and project ownership',
            'action': 'Update Resume',
            'impact': 'Medium - Essential for senior roles'
        })
    
    # Resume freshness
    days_old = (datetime.utcnow() - latest.uploaded_at).days
    if days_old > 90:
        recommendations.append({
            'type': 'update',
            'priority': 'medium',
            'title': 'Update Your Resume',
            'message': f'Resume is {days_old} days old. Add recent projects and achievements',
            'action': 'Upload New Version',
            'impact': 'Low - Keeps profile current'
        })
    
    return recommendations[:5]

def _generate_career_insights(resume, analyses):
    """Generate career insights"""
    if not resume:
        return {
            'current_trajectory': 'Unknown',
            'market_demand': 'Unknown',
            'growth_potential': 'Upload resume for insights'
        }
    
    parsed = resume.get_parsed_data()
    skills = parsed.get('skills', [])
    
    # Check for high-demand skills
    high_demand_skills = ['python', 'aws', 'kubernetes', 'react', 'machine learning', 'system design']
    has_demand_skills = any(skill.lower() in [s.lower() for s in skills] for skill in high_demand_skills)
    
    avg_match = 0
    if analyses:
        scores = [a.match_score for a in analyses if a.match_score]
        avg_match = sum(scores) / len(scores) if scores else 0
    
    return {
        'current_trajectory': 'Upward' if has_demand_skills else 'Stable',
        'market_demand': 'High' if has_demand_skills else 'Moderate',
        'growth_potential': 'Strong' if avg_match > 70 else 'Moderate',
        'key_strengths': [s for s in skills if s.lower() in [sk.lower() for sk in high_demand_skills]][:3]
    }

def _get_salary_insights(resume):
    """Get salary insights (stubbed for now)"""
    if not resume:
        return None
    
    parsed = resume.get_parsed_data()
    experience = parsed.get('experience', [])
    
    # Extract title from experience
    current_title = "Software Engineer"
    if experience:
        first_exp = experience[0]
        if isinstance(first_exp, dict):
            current_title = first_exp.get('title', 'Software Engineer')
    
    experience_years = len(experience)
    
    # Stubbed salary ranges (replace with real API data)
    salary_ranges = {
        'Software Engineer': '$80k - $120k',
        'Senior Software Engineer': '$120k - $180k',
        'Staff Engineer': '$180k - $250k',
        'Engineering Manager': '$140k - $200k'
    }
    
    estimated_range = salary_ranges.get(current_title, '$80k - $150k')
    
    return {
        'current_title': current_title,
        'experience_years': experience_years,
        'estimated_salary_range': estimated_range,
        'market_percentile': 'N/A (Connect salary API)',
        'growth_potential': '15-25% with role upgrade',
        'note': 'Estimates based on industry averages. Connect real salary API for accurate data.'
    }

def _calculate_profile_strength(resume):
    """Calculate overall profile strength"""
    if not resume:
        return 0
    
    parsed = resume.get_parsed_data()
    ats_result = ats_scorer.calculate_ats_score(parsed)
    
    score = 0
    max_score = 100
    
    # ATS score (40%)
    score += ats_result['percentage'] * 0.4
    
    # Skills (30%)
    skills_count = len(parsed.get('skills', []))
    skills_score = min(skills_count / 15 * 100, 100)
    score += skills_score * 0.3
    
    # Experience (20%)
    exp_count = len(parsed.get('experience', []))
    exp_score = min(exp_count / 5 * 100, 100)
    score += exp_score * 0.2
    
    # Completeness (10%)
    has_linkedin = parsed.get('linkedin') is not None
    has_github = parsed.get('github') is not None
    completeness = (has_linkedin + has_github) / 2 * 100
    score += completeness * 0.1
    
    return round(score, 2)

def _detect_experience_level(experience):
    """Detect experience level from resume"""
    exp_count = len(experience) if experience else 0
    
    if exp_count >= 8:
        return 'senior'
    elif exp_count >= 5:
        return 'mid-senior'
    elif exp_count >= 3:
        return 'mid-level'
    elif exp_count >= 1:
        return 'junior'
    else:
        return 'entry-level'

def _get_career_progression(current_level):
    """Get career progression paths"""
    progressions = {
        'entry-level': {
            'current': 'Entry-Level/Junior',
            'next_roles': [
                'Software Engineer',
                'Software Developer',
                'Full Stack Developer'
            ],
            'future_paths': ['Senior Engineer', 'Tech Lead', 'Architect']
        },
        'junior': {
            'current': 'Junior Developer',
            'next_roles': [
                'Software Engineer',
                'Mid-Level Developer',
                'Full Stack Developer'
            ],
            'future_paths': ['Senior Engineer', 'Tech Lead']
        },
        'mid-level': {
            'current': 'Mid-Level Engineer',
            'next_roles': [
                'Senior Software Engineer',
                'Staff Engineer',
                'Tech Lead'
            ],
            'future_paths': ['Principal Engineer', 'Engineering Manager', 'Architect']
        },
        'mid-senior': {
            'current': 'Mid-Senior Engineer',
            'next_roles': [
                'Staff Engineer',
                'Principal Engineer',
                'Engineering Manager'
            ],
            'future_paths': ['Distinguished Engineer', 'Director of Engineering']
        },
        'senior': {
            'current': 'Senior Engineer',
            'next_roles': [
                'Staff Engineer',
                'Principal Engineer',
                'Engineering Manager',
                'Solutions Architect'
            ],
            'future_paths': ['VP Engineering', 'CTO', 'Distinguished Engineer']
        }
    }
    
    return progressions.get(current_level, progressions['mid-level'])

def _get_skills_for_role(role_title):
    """Get typical skills required for a role"""
    if not role_title:
        return []
    
    role_skills = {
        'Senior Software Engineer': [
            'System Design', 'Architecture', 'Python', 'Java',
            'Microservices', 'AWS', 'Docker', 'Kubernetes',
            'CI/CD', 'Leadership', 'Mentoring'
        ],
        'Staff Engineer': [
            'System Architecture', 'Distributed Systems', 'Technical Leadership',
            'Cross-team Collaboration', 'Strategic Planning', 'Scalability',
            'Performance Optimization', 'Cloud Infrastructure'
        ],
        'Principal Engineer': [
            'System Architecture', 'Technical Strategy', 'Leadership',
            'Innovation', 'Scalability', 'Organization-wide Impact',
            'Technology Roadmap', 'Standards & Best Practices'
        ],
        'Tech Lead': [
            'Technical Leadership', 'Project Management', 'Architecture',
            'Code Review', 'Mentoring', 'Agile', 'Communication',
            'System Design', 'Team Coordination'
        ],
        'Engineering Manager': [
            'People Management', 'Leadership', 'Performance Management',
            'Hiring', 'Team Building', 'Strategic Planning',
            'Communication', 'Agile Methodologies', 'Budget Management'
        ],
        'Solutions Architect': [
            'System Architecture', 'Cloud Services', 'Design Patterns',
            'Security', 'Scalability', 'Technical Documentation',
            'Client Communication', 'Requirements Analysis'
        ],
        'Lead Developer': [
            'Technical Leadership', 'Architecture', 'Code Quality',
            'Mentoring', 'Project Planning', 'Agile', 'DevOps'
        ]
    }
    
    for role_key, skills in role_skills.items():
        if role_key.lower() in role_title.lower():
            return skills
    
    return ['System Design', 'Leadership', 'Architecture', 'Cloud', 'CI/CD']

def _generate_upskilling_plan(current_skills, target_career):
    """Generate upskilling recommendations"""
    if not target_career:
        return [
            {'skill': 'System Design & Architecture', 'priority': 'critical', 'time': '3-6 months', 'reason': 'Essential for senior roles'},
            {'skill': 'Leadership & Communication', 'priority': 'high', 'time': 'Ongoing', 'reason': 'Key for career growth'},
            {'skill': 'Cloud Technologies', 'priority': 'high', 'time': '2-3 months', 'reason': 'Industry demand'}
        ]
    
    upskilling_plans = {
        'Senior Software Engineer': [
            {'skill': 'System Design & Architecture', 'priority': 'critical', 'time': '3-6 months', 'reason': 'Core requirement'},
            {'skill': 'Microservices & Distributed Systems', 'priority': 'critical', 'time': '2-4 months', 'reason': 'Modern architecture'},
            {'skill': 'Cloud Services (AWS/Azure/GCP)', 'priority': 'high', 'time': '2-3 months', 'reason': 'Industry standard'},
            {'skill': 'DevOps & CI/CD', 'priority': 'high', 'time': '1-2 months', 'reason': 'Full-cycle ownership'},
            {'skill': 'Technical Leadership & Mentoring', 'priority': 'medium', 'time': 'Ongoing', 'reason': 'Team impact'}
        ],
        'Staff Engineer': [
            {'skill': 'Advanced System Architecture', 'priority': 'critical', 'time': '4-6 months', 'reason': 'Technical depth'},
            {'skill': 'Cross-team Technical Leadership', 'priority': 'critical', 'time': 'Ongoing', 'reason': 'Broader impact'},
            {'skill': 'Performance & Scalability', 'priority': 'high', 'time': '3-4 months', 'reason': 'Large-scale systems'},
            {'skill': 'Technical Strategy', 'priority': 'high', 'time': 'Ongoing', 'reason': 'Strategic thinking'}
        ],
        'Tech Lead': [
            {'skill': 'Technical Leadership', 'priority': 'critical', 'time': '3-6 months', 'reason': 'Primary responsibility'},
            {'skill': 'Project Management & Planning', 'priority': 'critical', 'time': '2-3 months', 'reason': 'Delivery ownership'},
            {'skill': 'Communication & Stakeholder Management', 'priority': 'high', 'time': 'Ongoing', 'reason': 'Cross-functional work'},
            {'skill': 'Code Review & Quality Standards', 'priority': 'high', 'time': '1-2 months', 'reason': 'Team quality'}
        ],
        'Engineering Manager': [
            {'skill': 'People Management', 'priority': 'critical', 'time': '6+ months', 'reason': 'Core responsibility'},
            {'skill': 'Performance Management & Coaching', 'priority': 'critical', 'time': '3-6 months', 'reason': 'Team development'},
            {'skill': 'Hiring & Interviewing', 'priority': 'high', 'time': '2-3 months', 'reason': 'Team building'},
            {'skill': 'Strategic Planning & OKRs', 'priority': 'high', 'time': 'Ongoing', 'reason': 'Business alignment'}
        ],
        'Solutions Architect': [
            {'skill': 'Enterprise Architecture', 'priority': 'critical', 'time': '4-6 months', 'reason': 'Large-scale design'},
            {'skill': 'Cloud Architecture Patterns', 'priority': 'critical', 'time': '3-4 months', 'reason': 'Modern solutions'},
            {'skill': 'Security & Compliance', 'priority': 'high', 'time': '2-3 months', 'reason': 'Enterprise requirements'},
            {'skill': 'Client Communication', 'priority': 'high', 'time': 'Ongoing', 'reason': 'Stakeholder management'}
        ]
    }
    
    # Find matching plan
    for career_key, plan in upskilling_plans.items():
        if career_key.lower() in target_career.lower():
            # Filter out skills already possessed
            current_lower = [s.lower() for s in current_skills]
            filtered = [
                p for p in plan
                if not any(cs in p['skill'].lower() for cs in current_lower)
            ]
            return filtered if filtered else plan
    
    # Default plan
    return upskilling_plans['Senior Software Engineer']

def _get_career_description(career):
    """Get career role description"""
    descriptions = {
        'Senior Software Engineer': 'Experienced engineer who leads technical projects, mentors junior developers, and makes architectural decisions.',
        'Staff Engineer': 'Senior technical leader working across multiple teams, setting technical direction and solving complex problems.',
        'Principal Engineer': 'Organization-wide technical leader influencing technology strategy and architecture at the highest level.',
        'Tech Lead': 'Combines technical expertise with people leadership, managing both code and team members.',
        'Engineering Manager': 'Focuses on people management, team growth, and delivery, with less hands-on coding.',
        'Solutions Architect': 'Designs large-scale technical solutions, works with clients, and bridges business and technology.',
        'Lead Developer': 'Technical leader responsible for code quality, architecture decisions, and team guidance.'
    }
    
    return descriptions.get(career, 'Senior technical role with increased responsibility and impact')

def _get_salary_range(career):
    """Get estimated salary range (stubbed)"""
    ranges = {
        'Senior Software Engineer': '$120k - $180k',
        'Staff Engineer': '$180k - $250k',
        'Principal Engineer': '$250k - $350k+',
        'Tech Lead': '$130k - $190k',
        'Engineering Manager': '$140k - $200k',
        'Solutions Architect': '$130k - $200k',
        'Lead Developer': '$110k - $170k'
    }
    
    return ranges.get(career, '$100k - $150k')

def _estimate_transition_timeline(skill_analysis, upskilling_plan):
    """Estimate time to transition"""
    if not skill_analysis or not upskilling_plan:
        return 'Unable to estimate'
    
    skill_match = skill_analysis.get('match_percentage', 0)
    critical_skills = [p for p in upskilling_plan if p.get('priority') == 'critical']
    
    if skill_match >= 80:
        return '3-6 months with focused preparation'
    elif skill_match >= 60:
        return '6-12 months with consistent upskilling'
    elif skill_match >= 40:
        return '12-18 months with dedicated learning'
    else:
        return '18-24 months - consider intermediate steps'

def _generate_switch_recommendation(ats_result, skill_analysis, readiness_score):
    """Generate job switch recommendation"""
    ats_score = ats_result['percentage']
    skill_match = skill_analysis.get('match_percentage', 0) if skill_analysis else 0
    
    if readiness_score >= 75:
        return {
            'status': 'Ready to Apply',
            'confidence': 'high',
            'message': 'Your profile is strong for target roles. Start applying!',
            'next_steps': [
                'Tailor resume for specific roles',
                'Prepare for technical interviews',
                'Network with people in target companies'
            ]
        }
    elif readiness_score >= 60:
        return {
            'status': 'Almost Ready',
            'confidence': 'medium',
            'message': 'Close a few gaps to be competitive',
            'next_steps': [
                f'Improve ATS score to 80%+ (current: {ats_score}%)',
                f'Acquire {3-int(skill_match/20)} key missing skills',
                'Add leadership examples to resume'
            ]
        }
    elif readiness_score >= 45:
        return {
            'status': 'Preparation Needed',
            'confidence': 'medium-low',
            'message': 'Invest 3-6 months in targeted preparation',
            'next_steps': [
                'Follow upskilling plan',
                'Build portfolio projects',
                'Improve resume quality',
                'Consider internal promotion first'
            ]
        }
    else:
        return {
            'status': 'Significant Gap',
            'confidence': 'low',
            'message': 'Focus on foundational skills and experience',
            'next_steps': [
                'Gain 1-2 more years of experience',
                'Master core technical skills',
                'Take on leadership opportunities',
                'Consider intermediate roles'
            ]
        }

def _get_market_insights(target_role):
    """Get market insights for role (stubbed)"""
    if not target_role:
        return None
    
    return {
        'demand': 'High',
        'growth_rate': '15-20% annually',
        'top_hiring_companies': ['FAANG', 'Startups', 'Enterprise'],
        'key_requirements': ['System Design', 'Leadership', 'Cloud'],
        'avg_time_to_hire': '30-45 days',
        'competition_level': 'Moderate to High',
        'note': 'Based on industry trends. Connect job market API for real-time data.'
    }

def _generate_action_plan(skill_analysis, recommendation):
    """Generate action plan"""
    missing_skills = skill_analysis.get('unmatched_jd_skills', [])[:5] if skill_analysis else []
    
    actions = []
    
    if recommendation['confidence'] in ['high', 'medium']:
        actions.append({
            'phase': 'Immediate (Next 2 weeks)',
            'tasks': [
                'Update resume with latest achievements',
                'Create LinkedIn profile optimization',
                'Start applying to target roles'
            ]
        })
    
    if missing_skills:
        actions.append({
            'phase': 'Short-term (1-3 months)',
            'tasks': [
                f'Learn {", ".join(missing_skills[:3])}',
                'Build portfolio project demonstrating skills',
                'Complete relevant certifications'
            ]
        })
    
    actions.append({
        'phase': 'Ongoing',
        'tasks': [
            'Network with professionals in target roles',
            'Stay updated with industry trends',
            'Practice technical interviews',
            'Contribute to open source or side projects'
        ]
    })
    
    return actions

def _map_learning_resources(upskilling_plan):
    """Map learning resources to skills"""
    resource_catalog = {
        'system design': [
            'System Design Primer (GitHub)',
            'Grokking the System Design Interview',
            'Designing Data-Intensive Applications (Book)'
        ],
        'architecture': [
            'Software Architecture Patterns (O\'Reilly)',
            'Clean Architecture (Book)',
            'Martin Fowler\'s Blog'
        ],
        'microservices': [
            'Microservices Patterns (Book)',
            'Building Microservices (Book)',
            'Spring Boot Documentation'
        ],
        'cloud': [
            'AWS Certified Solutions Architect',
            'Azure Fundamentals',
            'Google Cloud Skill Boost'
        ],
        'kubernetes': [
            'Kubernetes Official Docs',
            'Kubernetes in Action (Book)',
            'CKAD Certification'
        ],
        'leadership': [
            'The Manager\'s Path (Book)',
            'Crucial Conversations (Book)',
            'LinkedIn Learning - Leadership Courses'
        ],
        'devops': [
            'DevOps Handbook',
            'The Phoenix Project (Book)',
            'Jenkins Documentation'
        ]
    }
    
    resources = []
    for skill_item in upskilling_plan[:5]:
        skill = skill_item['skill'].lower()
        for key, res in resource_catalog.items():
            if key in skill:
                resources.append({
                    'skill': skill_item['skill'],
                    'priority': skill_item['priority'],
                    'resources': res
                })
                break
    
    return resources

def _recommend_certifications(current_skills, target_career):
    """Recommend relevant certifications"""
    cert_map = {
        'Senior Software Engineer': [
            {'name': 'AWS Certified Solutions Architect', 'provider': 'Amazon', 'value': 'High'},
            {'name': 'Google Cloud Professional', 'provider': 'Google', 'value': 'High'},
            {'name': 'Certified Kubernetes Administrator', 'provider': 'CNCF', 'value': 'Medium'}
        ],
        'Engineering Manager': [
            {'name': 'Certified Scrum Master', 'provider': 'Scrum Alliance', 'value': 'High'},
            {'name': 'PMI-ACP', 'provider': 'PMI', 'value': 'Medium'},
            {'name': 'Engineering Leadership', 'provider': 'Coursera', 'value': 'Medium'}
        ],
        'Solutions Architect': [
            {'name': 'AWS Certified Solutions Architect - Professional', 'provider': 'Amazon', 'value': 'Critical'},
            {'name': 'TOGAF Certification', 'provider': 'Open Group', 'value': 'High'},
            {'name': 'Azure Solutions Architect Expert', 'provider': 'Microsoft', 'value': 'High'}
        ]
    }
    
    if target_career:
        for career_key, certs in cert_map.items():
            if career_key.lower() in target_career.lower():
                return certs
    
    return cert_map['Senior Software Engineer']

def _suggest_projects(top_skills):
    """Suggest projects to build"""
    projects = []
    
    for skill_item in top_skills:
        skill = skill_item['skill'].lower()
        
        if 'system design' in skill or 'architecture' in skill:
            projects.append({
                'title': 'Scalable URL Shortener',
                'description': 'Build a distributed URL shortening service with high availability',
                'skills_demonstrated': ['System Design', 'Microservices', 'Caching', 'Load Balancing'],
                'estimated_time': '2-3 weeks'
            })
        
        elif 'cloud' in skill or 'kubernetes' in skill:
            projects.append({
                'title': 'Auto-scaling Web Application',
                'description': 'Deploy a containerized app with auto-scaling on Kubernetes',
                'skills_demonstrated': ['Kubernetes', 'Docker', 'Cloud', 'DevOps'],
                'estimated_time': '1-2 weeks'
            })
        
        elif 'microservices' in skill:
            projects.append({
                'title': 'E-commerce Microservices Platform',
                'description': 'Build separate services for user, product, order, payment',
                'skills_demonstrated': ['Microservices', 'API Design', 'Event-Driven', 'Docker'],
                'estimated_time': '3-4 weeks'
            })
    
    return projects[:3] if projects else [
        {
            'title': 'Full-Stack Application',
            'description': 'Build a complete application showcasing your skills',
            'skills_demonstrated': ['Architecture', 'Full-Stack', 'Database', 'Deployment'],
            'estimated_time': '2-3 weeks'
        }
    ]

def _calculate_upskilling_timeline(upskilling_plan):
    """Calculate estimated timeline for upskilling"""
    if not upskilling_plan:
        return 'N/A'
    
    total_months = 0
    for skill in upskilling_plan:
        time_str = skill.get('time', '0 months')
        if 'month' in time_str.lower():
            # Extract number of months
            parts = time_str.split()
            for i, part in enumerate(parts):
                if part.isdigit():
                    total_months += int(part)
                elif '-' in part:
                    # Handle ranges like "2-3 months"
                    nums = part.split('-')
                    if nums[0].isdigit():
                        total_months += int(nums[0])
                    break
    
    if total_months == 0:
        return '6-12 months (with ongoing learning)'
    elif total_months <= 6:
        return f'{total_months} months'
    else:
        return f'{total_months} months (can be done in parallel)'

def _calculate_competitiveness(benchmarks):
    """Calculate overall competitiveness score"""
    score = 0
    
    # ATS score comparison
    if benchmarks['ats_score']['status'] == 'above':
        score += 40
    else:
        score += 20
    
    # Skills count comparison
    if benchmarks['skills_count']['status'] == 'above':
        score += 35
    else:
        score += 15
    
    # Experience comparison
    if benchmarks['experience_count']['status'] == 'good':
        score += 25
    else:
        score += 10
    
    return round(score, 2)

def _get_market_standing(competitiveness_score):
    """Get market standing description"""
    if competitiveness_score >= 80:
        return {
            'level': 'Top Tier',
            'percentile': 'Top 10%',
            'description': 'Highly competitive profile. Strong candidate for senior roles.'
        }
    elif competitiveness_score >= 60:
        return {
            'level': 'Strong',
            'percentile': 'Top 25%',
            'description': 'Competitive profile. Good chances with target companies.'
        }
    elif competitiveness_score >= 40:
        return {
            'level': 'Average',
            'percentile': 'Top 50%',
            'description': 'Decent profile. Focus on key improvements for better opportunities.'
        }
    else:
        return {
            'level': 'Below Average',
            'percentile': 'Below 50%',
            'description': 'Needs improvement. Invest in upskilling and profile optimization.'
        }

def _identify_improvement_areas(benchmarks):
    """Identify specific areas for improvement"""
    areas = []
    
    if benchmarks['ats_score']['status'] == 'below':
        gap = benchmarks['ats_score']['market_average'] - benchmarks['ats_score']['user']
        areas.append({
            'area': 'ATS Score',
            'current': benchmarks['ats_score']['user'],
            'target': benchmarks['ats_score']['top_10_percent'],
            'gap': round(gap, 2),
            'priority': 'high',
            'action': 'Improve resume formatting and content completeness'
        })
    
    if benchmarks['skills_count']['status'] == 'below':
        gap = benchmarks['skills_count']['market_average'] - benchmarks['skills_count']['user']
        areas.append({
            'area': 'Skills',
            'current': benchmarks['skills_count']['user'],
            'target': benchmarks['skills_count']['top_performers'],
            'gap': int(gap),
            'priority': 'high',
            'action': 'Add more technical and leadership skills'
        })
    
    if benchmarks['experience_count']['status'] != 'good':
        areas.append({
            'area': 'Experience',
            'current': benchmarks['experience_count']['user'],
            'target': benchmarks['experience_count']['recommended'],
            'gap': benchmarks['experience_count']['recommended'] - benchmarks['experience_count']['user'],
            'priority': 'medium',
            'action': 'Add more work experience or significant projects'
        })
    
    return areas