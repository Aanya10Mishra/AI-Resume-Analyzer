"""
Student Routes
Features for college students and freshers
Focus: Learning, career guidance, entry-level jobs
"""
from flask import Blueprint, request, jsonify
from models.database import db, Resume, ResumeAnalysis, JobDescription
from utils import TextProcessor, ATSScorer
import logging

logger = logging.getLogger(__name__)

# Create blueprint
student_bp = Blueprint('student', __name__, url_prefix='/api/student')

# These will be initialized from app.py
text_processor = None
ats_scorer = None

def init_student_routes(tp, ats):
    """Initialize with utility instances"""
    global text_processor, ats_scorer
    text_processor = tp
    ats_scorer = ats
    logger.info("✅ Student routes initialized")

@student_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def student_dashboard(user_id):
    """
    Student Dashboard
    Shows: Resume stats, ATS scores, recent analyses, learning recommendations
    """
    try:
        logger.info(f"📊 Loading student dashboard for user {user_id}")
        
        # Get user's resumes
        resumes = Resume.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).limit(10).all()
        
        # Get recent analyses
        if resumes:
            resume_ids = [r.id for r in resumes]
            recent_analyses = ResumeAnalysis.query.filter(
                ResumeAnalysis.resume_id.in_(resume_ids)
            ).order_by(ResumeAnalysis.analyzed_at.desc()).limit(5).all()
        else:
            recent_analyses = []
        
        # Calculate statistics
        total_resumes = len(resumes)
        avg_ats_score = 0
        total_applications = len(recent_analyses)
        
        if resumes:
            ats_scores = []
            for resume in resumes:
                parsed = resume.get_parsed_data()
                score = ats_scorer.calculate_ats_score(parsed)
                ats_scores.append(score['percentage'])
            avg_ats_score = sum(ats_scores) / len(ats_scores) if ats_scores else 0
        
        # Get best performing resume
        best_resume = None
        if resumes:
            best_resume = max(resumes, key=lambda r: ats_scorer.calculate_ats_score(
                r.get_parsed_data()
            )['percentage'])
        
        # Generate recommendations
        recommendations = _generate_student_recommendations(
            user_id, 
            resumes, 
            recent_analyses
        )
        
        response = {
            'user_id': user_id,
            'role': 'student',
            'statistics': {
                'total_resumes': total_resumes,
                'average_ats_score': round(avg_ats_score, 2),
                'total_applications': total_applications,
                'profile_completeness': _calculate_profile_completeness(resumes)
            },
            'best_resume': {
                'id': best_resume.id,
                'filename': best_resume.filename,
                'ats_score': ats_scorer.calculate_ats_score(
                    best_resume.get_parsed_data()
                )['percentage']
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
                    'analyzed_at': a.analyzed_at.isoformat()
                }
                for a in recent_analyses
            ],
            'recommendations': recommendations
        }
        
        logger.info(f"✅ Dashboard loaded for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

@student_bp.route('/career-guidance/<int:user_id>', methods=['GET'])
def career_guidance(user_id):
    """
    Career Guidance for Students
    Suggests: Entry-level careers, skill roadmap, certifications
    """
    try:
        logger.info(f"🎯 Generating career guidance for user {user_id}")
        
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
        
        # Entry-level career options
        entry_careers = [
            'Junior Software Developer',
            'Frontend Developer Intern',
            'Backend Developer Intern',
            'Data Analyst Intern',
            'QA Engineer Trainee',
            'Technical Support Engineer',
            'Junior DevOps Engineer',
            'UI/UX Designer Intern',
            'Business Analyst Trainee',
            'Cloud Engineer Associate'
        ]
        
        # Find matching careers using embeddings
        career_matches = text_processor.find_career_matches(
            resume.raw_text,
            entry_careers,
            top_n=5
        )
        
        # Generate skill roadmap for top career
        top_career = career_matches[0]['career'] if career_matches else None
        skill_roadmap = _generate_skill_roadmap(current_skills, top_career)
        
        # Suggest certifications
        certifications = _suggest_certifications(current_skills, top_career)
        
        # Learning resources
        learning_paths = _get_learning_resources(skill_roadmap)
        
        response = {
            'user_id': user_id,
            'current_skills': current_skills,
            'skill_count': len(current_skills),
            'career_matches': career_matches,
            'top_recommendation': {
                'career': top_career,
                'fit_score': career_matches[0]['similarity'] if career_matches else 0,
                'description': _get_career_description(top_career)
            },
            'skill_roadmap': skill_roadmap,
            'recommended_certifications': certifications,
            'learning_paths': learning_paths
        }
        
        logger.info(f"✅ Career guidance generated for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Career guidance error: {e}")
        return jsonify({'error': str(e)}), 500

@student_bp.route('/job-matches/<int:user_id>', methods=['GET'])
def find_job_matches(user_id):
    """
    Find Entry-Level Job Matches
    Filters: Internships, Junior roles, Trainee positions
    """
    try:
        logger.info(f"🔍 Finding job matches for user {user_id}")
        
        # Get latest resume
        resume = Resume.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(Resume.uploaded_at.desc()).first()
        
        if not resume:
            return jsonify({'error': 'No resume found'}), 404
        
        # Get entry-level job descriptions
        entry_level_keywords = ['junior', 'intern', 'trainee', 'entry', 'fresher', 'graduate']
        
        jds = JobDescription.query.filter(
            JobDescription.is_active == True
        ).filter(
            db.or_(*[
                JobDescription.title.ilike(f'%{keyword}%')
                for keyword in entry_level_keywords
            ])
        ).limit(20).all()
        
        if not jds:
            # If no entry-level JDs, get all and filter later
            jds = JobDescription.query.filter_by(is_active=True).limit(20).all()
        
        # Calculate matches
        matches = []
        resume_skills = resume.get_parsed_data().get('skills', [])
        
        for jd in jds:
            # Calculate semantic match
            match_score = text_processor.calculate_similarity(
                resume.raw_text,
                jd.description
            )
            
            # Calculate skill match
            jd_skills = jd.get_parsed_skills()
            skill_analysis = text_processor.calculate_skill_similarity(
                resume_skills,
                jd_skills
            )
            
            matches.append({
                'jd_id': jd.id,
                'title': jd.title,
                'company': jd.company,
                'location': jd.location,
                'employment_type': jd.employment_type,
                'match_score': match_score,
                'skill_match_percentage': skill_analysis['match_percentage'],
                'matched_skills': skill_analysis['matched_pairs'][:5],  # Top 5
                'missing_skills': skill_analysis['unmatched_jd_skills'][:5],
                'recommendation': _get_application_recommendation(match_score, skill_analysis)
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Categorize matches
        excellent = [m for m in matches if m['match_score'] >= 75]
        good = [m for m in matches if 60 <= m['match_score'] < 75]
        moderate = [m for m in matches if 45 <= m['match_score'] < 60]
        
        response = {
            'user_id': user_id,
            'total_matches': len(matches),
            'categories': {
                'excellent_matches': {
                    'count': len(excellent),
                    'jobs': excellent[:5]
                },
                'good_matches': {
                    'count': len(good),
                    'jobs': good[:5]
                },
                'growth_opportunities': {
                    'count': len(moderate),
                    'jobs': moderate[:5],
                    'note': 'These roles may require some upskilling'
                }
            },
            'all_matches': matches[:15]  # Top 15
        }
        
        logger.info(f"✅ Found {len(matches)} job matches for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Job matching error: {e}")
        return jsonify({'error': str(e)}), 500

@student_bp.route('/improve-resume/<int:resume_id>', methods=['GET'])
def improve_resume(resume_id):
    """
    Get Resume Improvement Suggestions
    """
    try:
        resume = Resume.query.get(resume_id)
        
        if not resume:
            return jsonify({'error': 'Resume not found'}), 404
        
        parsed_data = resume.get_parsed_data()
        ats_result = ats_scorer.calculate_ats_score(parsed_data)
        
        # Generate detailed suggestions
        suggestions = []
        
        # ATS suggestions (already in ats_result)
        suggestions.extend(ats_result.get('suggestions', []))
        
        # Skill suggestions
        current_skills = parsed_data.get('skills', [])
        if len(current_skills) < 8:
            suggestions.append({
                'category': 'Skills',
                'priority': 'high',
                'suggestion': f'Add more technical skills (currently: {len(current_skills)})',
                'tips': [
                    'Include programming languages',
                    'Add frameworks and tools',
                    'Mention soft skills'
                ]
            })
        
        # Experience suggestions
        experience = parsed_data.get('experience', [])
        if len(experience) < 2:
            suggestions.append({
                'category': 'Experience',
                'priority': 'high',
                'suggestion': 'Add more experience entries or projects',
                'tips': [
                    'Include internships',
                    'Add personal projects',
                    'Mention academic projects',
                    'Include volunteer work'
                ]
            })
        
        # Contact info
        if not parsed_data.get('linkedin'):
            suggestions.append({
                'category': 'Contact',
                'priority': 'medium',
                'suggestion': 'Add LinkedIn profile URL',
                'tips': ['Increases credibility', 'Shows professional network']
            })
        
        if not parsed_data.get('github'):
            suggestions.append({
                'category': 'Contact',
                'priority': 'medium',
                'suggestion': 'Add GitHub profile (for technical roles)',
                'tips': ['Showcases your code', 'Demonstrates practical skills']
            })
        
        response = {
            'resume_id': resume_id,
            'current_ats_score': ats_result['percentage'],
            'grade': ats_result['grade'],
            'potential_score': min(ats_result['percentage'] + len(suggestions) * 5, 100),
            'total_suggestions': len(suggestions),
            'suggestions': suggestions,
            'quick_wins': [s for s in suggestions if s.get('priority') == 'high'][:3]
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Improvement suggestions error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== HELPER FUNCTIONS ====================

def _generate_student_recommendations(user_id, resumes, analyses):
    """Generate personalized recommendations for students"""
    recommendations = []
    
    if not resumes:
        recommendations.append({
            'type': 'action_required',
            'priority': 'critical',
            'title': 'Upload Your Resume',
            'message': 'Get started by uploading your resume to receive personalized insights',
            'action': 'Upload Resume'
        })
        return recommendations
    
    latest_resume = resumes[0]
    parsed_data = latest_resume.get_parsed_data()
    ats_result = ats_scorer.calculate_ats_score(parsed_data)
    
    # Low ATS score
    if ats_result['percentage'] < 60:
        recommendations.append({
            'type': 'ats_improvement',
            'priority': 'high',
            'title': 'Improve Your ATS Score',
            'message': f'Your ATS score is {ats_result["percentage"]}%. Target: 75%+',
            'action': 'View Suggestions',
            'impact': 'High - Better chance of passing automated screening'
        })
    
    # Few skills
    skills_count = len(parsed_data.get('skills', []))
    if skills_count < 7:
        recommendations.append({
            'type': 'skills',
            'priority': 'high',
            'title': 'Add More Skills',
            'message': f'You have {skills_count} skills listed. Aim for 8-12.',
            'action': 'Learn New Skills',
            'impact': 'Medium - Increases job matches'
        })
    
    # No recent applications
    if not analyses or len(analyses) < 3:
        recommendations.append({
            'type': 'applications',
            'priority': 'medium',
            'title': 'Start Applying',
            'message': 'Match your resume with job descriptions to find opportunities',
            'action': 'Find Jobs',
            'impact': 'High - Active job search'
        })
    
    # Missing LinkedIn
    if not parsed_data.get('linkedin'):
        recommendations.append({
            'type': 'profile',
            'priority': 'low',
            'title': 'Add LinkedIn Profile',
            'message': 'Including your LinkedIn URL improves credibility',
            'action': 'Update Resume',
            'impact': 'Low - Professional presentation'
        })
    
    return recommendations[:5]  # Top 5 recommendations

def _calculate_profile_completeness(resumes):
    """Calculate overall profile completeness"""
    if not resumes:
        return 0
    
    latest = resumes[0]
    parsed = latest.get_parsed_data()
    
    score = 0
    max_score = 100
    
    # Contact info (20 pts)
    if parsed.get('email'): score += 10
    if parsed.get('phone'): score += 10
    
    # Skills (25 pts)
    skills_count = len(parsed.get('skills', []))
    score += min(skills_count * 2.5, 25)
    
    # Experience (25 pts)
    exp_count = len(parsed.get('experience', []))
    score += min(exp_count * 8, 25)
    
    # Education (15 pts)
    if parsed.get('education'): score += 15
    
    # Links (15 pts)
    if parsed.get('linkedin'): score += 7.5
    if parsed.get('github'): score += 7.5
    
    return round(score, 2)

def _generate_skill_roadmap(current_skills, target_career):
    """Generate learning roadmap based on career goal"""
    
    roadmaps = {
        'Junior Software Developer': [
            {'skill': 'Python or Java', 'priority': 'critical', 'time': '2-3 months'},
            {'skill': 'Data Structures & Algorithms', 'priority': 'critical', 'time': '2-3 months'},
            {'skill': 'Git & Version Control', 'priority': 'high', 'time': '1 month'},
            {'skill': 'SQL & Databases', 'priority': 'high', 'time': '1-2 months'},
            {'skill': 'REST APIs', 'priority': 'medium', 'time': '1 month'}
        ],
        'Data Analyst Intern': [
            {'skill': 'Python (Pandas, NumPy)', 'priority': 'critical', 'time': '2 months'},
            {'skill': 'SQL', 'priority': 'critical', 'time': '1-2 months'},
            {'skill': 'Excel (Advanced)', 'priority': 'high', 'time': '1 month'},
            {'skill': 'Data Visualization (Tableau/PowerBI)', 'priority': 'high', 'time': '1 month'},
            {'skill': 'Statistics Basics', 'priority': 'medium', 'time': '2 months'}
        ],
        'Frontend Developer Intern': [
            {'skill': 'HTML, CSS, JavaScript', 'priority': 'critical', 'time': '2-3 months'},
            {'skill': 'React or Vue', 'priority': 'critical', 'time': '2 months'},
            {'skill': 'Responsive Design', 'priority': 'high', 'time': '1 month'},
            {'skill': 'Git & GitHub', 'priority': 'high', 'time': '1 month'},
            {'skill': 'REST API Integration', 'priority': 'medium', 'time': '1 month'}
        ]
    }
    
    # Find matching roadmap
    for career_key, roadmap in roadmaps.items():
        if target_career and career_key.lower() in target_career.lower():
            # Filter out skills user already has
            current_lower = [s.lower() for s in current_skills]
            filtered = [
                r for r in roadmap 
                if not any(cs in r['skill'].lower() for cs in current_lower)
            ]
            return filtered if filtered else roadmap
    
    # Default roadmap
    return [
        {'skill': 'Programming Fundamentals', 'priority': 'critical', 'time': '2 months'},
        {'skill': 'Problem Solving', 'priority': 'critical', 'time': 'Ongoing'},
        {'skill': 'Communication Skills', 'priority': 'high', 'time': 'Ongoing'}
    ]

def _suggest_certifications(current_skills, target_career):
    """Suggest relevant certifications"""
    
    cert_map = {
        'Developer': [
            {'name': 'AWS Certified Cloud Practitioner', 'provider': 'Amazon', 'level': 'Beginner'},
            {'name': 'Python Certification', 'provider': 'Python Institute', 'level': 'Beginner'},
            {'name': 'GitHub Foundations', 'provider': 'GitHub', 'level': 'Beginner'}
        ],
        'Data Analyst': [
            {'name': 'Google Data Analytics Certificate', 'provider': 'Google', 'level': 'Beginner'},
            {'name': 'SQL for Data Science', 'provider': 'Coursera', 'level': 'Beginner'},
            {'name': 'Tableau Desktop Specialist', 'provider': 'Tableau', 'level': 'Beginner'}
        ],
        'Frontend': [
            {'name': 'Meta Front-End Developer', 'provider': 'Meta', 'level': 'Beginner'},
            {'name': 'React Basics', 'provider': 'Coursera', 'level': 'Beginner'},
            {'name': 'Responsive Web Design', 'provider': 'freeCodeCamp', 'level': 'Beginner'}
        ]
    }
    
    if target_career:
        for key, certs in cert_map.items():
            if key.lower() in target_career.lower():
                return certs
    
    return cert_map['Developer']  # Default

def _get_learning_resources(skill_roadmap):
    """Get learning resources for skills"""
    resources = {
        'python': ['Python.org', 'Real Python', 'Codecademy Python'],
        'javascript': ['MDN Web Docs', 'JavaScript.info', 'freeCodeCamp'],
        'sql': ['SQLZoo', 'Mode Analytics', 'Khan Academy SQL'],
        'react': ['React Docs', 'freeCodeCamp React', 'Scrimba'],
        'git': ['Git Documentation', 'GitHub Learning Lab', 'Atlassian Git'],
        'data': ['Kaggle', 'DataCamp', 'Google Data Analytics']
    }
    
    result = []
    for skill_item in skill_roadmap[:5]:  # Top 5 skills
        skill = skill_item['skill'].lower()
        for key, res in resources.items():
            if key in skill:
                result.append({
                    'skill': skill_item['skill'],
                    'resources': res,
                    'priority': skill_item['priority']
                })
                break
    
    return result

def _get_career_description(career):
    """Get career description"""
    descriptions = {
        'Junior Software Developer': 'Entry-level programming role focusing on coding, debugging, and learning from senior developers.',
        'Data Analyst Intern': 'Analyze data, create reports, and support business decisions through data insights.',
        'Frontend Developer Intern': 'Build user interfaces, work with designers, and create responsive web applications.'
    }
    return descriptions.get(career, 'Entry-level position with growth opportunities')

def _get_application_recommendation(match_score, skill_analysis):
    """Get application recommendation"""
    skill_match = skill_analysis['match_percentage']
    
    if match_score >= 75 and skill_match >= 70:
        return {'status': 'Apply Now', 'confidence': 'High', 'color': 'green'}
    elif match_score >= 60 and skill_match >= 50:
        return {'status': 'Good Fit', 'confidence': 'Medium', 'color': 'blue'}
    elif match_score >= 45:
        return {'status': 'Consider with Upskilling', 'confidence': 'Low', 'color': 'yellow'}
    else:
        return {'status': 'Focus on Better Matches', 'confidence': 'Very Low', 'color': 'red'}