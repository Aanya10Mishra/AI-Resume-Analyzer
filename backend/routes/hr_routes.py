"""
HR/Recruiter Routes
Features for recruiters and hiring managers
Focus: Bulk screening, candidate ranking, recruitment metrics
"""
from flask import Blueprint, request, jsonify
from models.database import db, Resume, ResumeAnalysis, JobDescription, User
from utils import TextProcessor, ATSScorer
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Create blueprint
recruiter_bp = Blueprint('recruiter', __name__, url_prefix='/api/recruiter')

# Global variables (initialized from app.py)
text_processor = None
ats_scorer = None

def init_recruiter_routes(tp, ats):
    """Initialize with utility instances"""
    global text_processor, ats_scorer
    text_processor = tp
    ats_scorer = ats
    logger.info("✅ Recruiter routes initialized")

@recruiter_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def recruiter_dashboard(user_id):
    """
    Recruiter Dashboard
    Shows: Active JDs, candidate pipeline, hiring metrics
    """
    try:
        logger.info(f"📊 Loading recruiter dashboard for user {user_id}")
        
        # Get HR user's job descriptions
        active_jds = JobDescription.query.filter_by(
            user_id=user_id,
            is_active=True
        ).order_by(desc(JobDescription.created_at)).all()
        
        # Get all analyses for this HR's JDs
        jd_ids = [jd.id for jd in active_jds]
        
        total_candidates_reviewed = 0
        shortlisted_candidates = 0
        recent_analyses = []
        
        if jd_ids:
            total_candidates_reviewed = ResumeAnalysis.query.filter(
                ResumeAnalysis.jd_id.in_(jd_ids)
            ).count()
            
            shortlisted_candidates = ResumeAnalysis.query.filter(
                ResumeAnalysis.jd_id.in_(jd_ids),
                ResumeAnalysis.match_score >= 70
            ).count()
            
            recent_analyses = ResumeAnalysis.query.filter(
                ResumeAnalysis.jd_id.in_(jd_ids)
            ).order_by(desc(ResumeAnalysis.analyzed_at)).limit(10).all()
        
        # Calculate metrics
        avg_match_score = 0
        avg_ats_score = 0
        if recent_analyses:
            match_scores = [a.match_score for a in recent_analyses if a.match_score]
            ats_scores = [a.ats_score for a in recent_analyses if a.ats_score]
            avg_match_score = sum(match_scores) / len(match_scores) if match_scores else 0
            avg_ats_score = sum(ats_scores) / len(ats_scores) if ats_scores else 0
        
        # Top performing JDs
        jd_performance = _calculate_jd_performance(jd_ids)
        
        response = {
            'user_id': user_id,
            'role': 'recruiter',
            'metrics': {
                'active_job_descriptions': len(active_jds),
                'total_candidates_reviewed': total_candidates_reviewed,
                'shortlisted_candidates': shortlisted_candidates,
                'average_match_score': round(avg_match_score, 2),
                'average_ats_score': round(avg_ats_score, 2),
                'conversion_rate': round(
                    (shortlisted_candidates / total_candidates_reviewed * 100)
                    if total_candidates_reviewed > 0 else 0,
                    2
                )
            },
            'active_job_descriptions': [
                {
                    'id': jd.id,
                    'title': jd.title,
                    'company': jd.company,
                    'location': jd.location,
                    'applicants': _count_applicants(jd.id),
                    'shortlisted': _count_shortlisted(jd.id),
                    'created_at': jd.created_at.isoformat()
                }
                for jd in active_jds[:10]
            ],
            'recent_reviews': [
                {
                    'id': a.id,
                    'candidate_name': a.resume.get_parsed_data().get('name', 'Unknown'),
                    'jd_title': a.job_description.title,
                    'match_score': a.match_score,
                    'ats_score': a.ats_score,
                    'status': _get_candidate_status(a.match_score, a.ats_score),
                    'reviewed_at': a.analyzed_at.isoformat()
                }
                for a in recent_analyses
            ],
            'top_performing_jds': jd_performance[:5],
            'insights': _generate_recruiter_insights(active_jds, total_candidates_reviewed, shortlisted_candidates)
        }
        
        logger.info(f"✅ Recruiter dashboard loaded for user {user_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Recruiter dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

@recruiter_bp.route('/bulk-screen', methods=['POST'])
def bulk_screen():
    """
    Bulk Resume Screening
    Screen multiple resumes against a job description
    Body: { "jd_id": int, "resume_ids": [int], "auto_save": bool }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        jd_id = data.get('jd_id')
        resume_ids = data.get('resume_ids', [])
        auto_save = data.get('auto_save', True)
        
        if not jd_id or not resume_ids:
            return jsonify({'error': 'jd_id and resume_ids are required'}), 400
        
        logger.info(f"🔍 Bulk screening: {len(resume_ids)} resumes for JD {jd_id}")
        
        # Get job description
        jd = JobDescription.query.get(jd_id)
        if not jd:
            return jsonify({'error': 'Job description not found'}), 404
        
        # Get resumes
        resumes = Resume.query.filter(Resume.id.in_(resume_ids)).all()
        
        if not resumes:
            return jsonify({'error': 'No resumes found'}), 404
        
        # Screen each resume
        results = []
        for resume in resumes:
            try:
                parsed = resume.get_parsed_data()
                
                # Calculate match score using embeddings
                match_score = text_processor.calculate_similarity(
                    resume.raw_text,
                    jd.description
                )
                
                # Calculate ATS score
                ats_result = ats_scorer.calculate_ats_score(parsed)
                
                # Calculate skill similarity
                resume_skills = parsed.get('skills', [])
                jd_skills = jd.get_parsed_skills()
                skill_analysis = text_processor.calculate_skill_similarity(
                    resume_skills,
                    jd_skills
                )
                
                # Generate recommendation
                recommendation = _generate_screening_recommendation(
                    match_score,
                    ats_result['percentage'],
                    skill_analysis
                )
                
                result = {
                    'resume_id': resume.id,
                    'candidate_name': parsed.get('name', 'Unknown'),
                    'candidate_email': parsed.get('email', 'N/A'),
                    'candidate_phone': parsed.get('phone', 'N/A'),
                    'filename': resume.filename,
                    'match_score': match_score,
                    'ats_score': ats_result['percentage'],
                    'skill_match_percentage': skill_analysis['match_percentage'],
                    'matched_skills': skill_analysis['matched_pairs'][:5],
                    'missing_skills': skill_analysis['unmatched_jd_skills'][:5],
                    'recommendation': recommendation,
                    'experience_count': len(parsed.get('experience', [])),
                    'education_count': len(parsed.get('education', []))
                }
                
                results.append(result)
                
                # Save analysis if auto_save is true
                if auto_save:
                    analysis = ResumeAnalysis.query.filter_by(
                        resume_id=resume.id,
                        jd_id=jd_id
                    ).first()
                    
                    if not analysis:
                        analysis = ResumeAnalysis(
                            resume_id=resume.id,
                            jd_id=jd_id
                        )
                    
                    analysis.match_score = match_score
                    analysis.ats_score = ats_result['percentage']
                    analysis.semantic_score = match_score
                    analysis.set_skill_gaps(skill_analysis['unmatched_jd_skills'])
                    analysis.analyzed_at = datetime.utcnow()
                    
                    db.session.add(analysis)
                
            except Exception as e:
                logger.error(f"Error screening resume {resume.id}: {e}")
                results.append({
                    'resume_id': resume.id,
                    'error': str(e),
                    'filename': resume.filename
                })
        
        if auto_save:
            db.session.commit()
        
        # Rank candidates
        ranked = sorted(
            [r for r in results if 'error' not in r],
            key=lambda x: (x['match_score'], x['skill_match_percentage'], x['ats_score']),
            reverse=True
        )
        
        # Add rank numbers
        for i, candidate in enumerate(ranked, 1):
            candidate['rank'] = i
        
        # Categorize candidates
        excellent = [c for c in ranked if c['recommendation']['tier'] == 'excellent']
        good = [c for c in ranked if c['recommendation']['tier'] == 'good']
        moderate = [c for c in ranked if c['recommendation']['tier'] == 'moderate']
        low = [c for c in ranked if c['recommendation']['tier'] == 'low']
        
        response = {
            'jd_id': jd_id,
            'jd_title': jd.title,
            'total_screened': len(results),
            'successful_screens': len(ranked),
            'failed_screens': len(results) - len(ranked),
            'categories': {
                'excellent': {
                    'count': len(excellent),
                    'candidates': excellent,
                    'description': 'Strong match - Highly recommended for interview'
                },
                'good': {
                    'count': len(good),
                    'candidates': good,
                    'description': 'Good match - Consider for interview'
                },
                'moderate': {
                    'count': len(moderate),
                    'candidates': moderate,
                    'description': 'Moderate match - Review carefully'
                },
                'low': {
                    'count': len(low),
                    'candidates': low,
                    'description': 'Low match - Not recommended'
                }
            },
            'ranked_candidates': ranked,
            'top_10_candidates': ranked[:10]
        }
        
        logger.info(f"✅ Bulk screening complete: {len(ranked)} candidates ranked")
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Bulk screening error: {e}")
        return jsonify({'error': str(e)}), 500

@recruiter_bp.route('/candidate-details/<int:resume_id>/<int:jd_id>', methods=['GET'])
def get_candidate_details(resume_id, jd_id):
    """
    Get detailed candidate profile for review
    """
    try:
        resume = Resume.query.get(resume_id)
        jd = JobDescription.query.get(jd_id)
        
        if not resume or not jd:
            return jsonify({'error': 'Resume or JD not found'}), 404
        
        # Get or create analysis
        analysis = ResumeAnalysis.query.filter_by(
            resume_id=resume_id,
            jd_id=jd_id
        ).first()
        
        parsed = resume.get_parsed_data()
        
        if not analysis:
            # Create new analysis
            match_score = text_processor.calculate_similarity(
                resume.raw_text,
                jd.description
            )
            
            ats_result = ats_scorer.calculate_ats_score(parsed)
            
            skill_analysis = text_processor.calculate_skill_similarity(
                parsed.get('skills', []),
                jd.get_parsed_skills()
            )
            
            analysis = ResumeAnalysis(
                resume_id=resume_id,
                jd_id=jd_id,
                match_score=match_score,
                ats_score=ats_result['percentage'],
                semantic_score=match_score
            )
            analysis.set_skill_gaps(skill_analysis['unmatched_jd_skills'])
            
            db.session.add(analysis)
            db.session.commit()
        else:
            ats_result = ats_scorer.calculate_ats_score(parsed)
            skill_analysis = text_processor.calculate_skill_similarity(
                parsed.get('skills', []),
                jd.get_parsed_skills()
            )
        
        # Generate hiring decision support
        hiring_decision = _generate_hiring_decision(
            analysis.match_score,
            analysis.ats_score,
            skill_analysis
        )
        
        response = {
            'candidate': {
                'name': parsed.get('name', 'Unknown'),
                'email': parsed.get('email', 'N/A'),
                'phone': parsed.get('phone', 'N/A'),
                'linkedin': parsed.get('linkedin', 'N/A'),
                'github': parsed.get('github', 'N/A'),
                'skills': parsed.get('skills', []),
                'experience': parsed.get('experience', []),
                'education': parsed.get('education', []),
                'word_count': parsed.get('word_count', 0)
            },
            'scores': {
                'match_score': analysis.match_score,
                'ats_score': analysis.ats_score,
                'skill_match_percentage': skill_analysis['match_percentage'],
                'overall_rating': _calculate_overall_rating(analysis.match_score, analysis.ats_score, skill_analysis)
            },
            'skill_analysis': {
                'matched_skills': skill_analysis['matched_pairs'],
                'missing_skills': skill_analysis['unmatched_jd_skills'],
                'strong_matches': skill_analysis['strong_matches'],
                'weak_matches': skill_analysis['weak_matches']
            },
            'hiring_decision': hiring_decision,
            'analysis_date': analysis.analyzed_at.isoformat(),
            'job_description': {
                'id': jd.id,
                'title': jd.title,
                'company': jd.company
            }
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Candidate details error: {e}")
        return jsonify({'error': str(e)}), 500

@recruiter_bp.route('/export-shortlist/<int:jd_id>', methods=['GET'])
def export_shortlist(jd_id):
    """
    Export shortlisted candidates for a JD
    Query params: ?threshold=70 (minimum match score)
    """
    try:
        threshold = request.args.get('threshold', 70, type=float)
        
        jd = JobDescription.query.get(jd_id)
        if not jd:
            return jsonify({'error': 'Job description not found'}), 404
        
        # Get shortlisted candidates
        shortlisted = ResumeAnalysis.query.filter(
            ResumeAnalysis.jd_id == jd_id,
            ResumeAnalysis.match_score >= threshold
        ).order_by(desc(ResumeAnalysis.match_score)).all()
        
        if not shortlisted:
            return jsonify({
                'message': 'No candidates meet the threshold',
                'threshold': threshold
            }), 200
        
        # Format export data
        candidates = []
        for i, analysis in enumerate(shortlisted, 1):
            parsed = analysis.resume.get_parsed_data()
            
            candidates.append({
                'rank': i,
                'name': parsed.get('name', 'Unknown'),
                'email': parsed.get('email', 'N/A'),
                'phone': parsed.get('phone', 'N/A'),
                'linkedin': parsed.get('linkedin', 'N/A'),
                'match_score': analysis.match_score,
                'ats_score': analysis.ats_score,
                'skills': ', '.join(parsed.get('skills', [])[:10]),
                'experience_years': len(parsed.get('experience', [])),
                'recommendation': _get_quick_recommendation(analysis.match_score, analysis.ats_score),
                'analyzed_at': analysis.analyzed_at.isoformat()
            })
        
        response = {
            'jd_id': jd_id,
            'jd_title': jd.title,
            'jd_company': jd.company,
            'threshold_used': threshold,
            'total_shortlisted': len(candidates),
            'exported_at': datetime.utcnow().isoformat(),
            'candidates': candidates,
            'summary': {
                'excellent_candidates': len([c for c in candidates if c['match_score'] >= 85]),
                'good_candidates': len([c for c in candidates if 70 <= c['match_score'] < 85]),
                'average_match_score': round(sum(c['match_score'] for c in candidates) / len(candidates), 2),
                'average_ats_score': round(sum(c['ats_score'] for c in candidates) / len(candidates), 2)
            }
        }
        
        logger.info(f"✅ Exported {len(candidates)} candidates for JD {jd_id}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Export shortlist error: {e}")
        return jsonify({'error': str(e)}), 500

@recruiter_bp.route('/compare-candidates', methods=['POST'])
def compare_candidates():
    """
    Compare multiple candidates side-by-side
    Body: { "resume_ids": [int], "jd_id": int }
    """
    try:
        data = request.get_json()
        
        resume_ids = data.get('resume_ids', [])
        jd_id = data.get('jd_id')
        
        if not resume_ids or not jd_id:
            return jsonify({'error': 'resume_ids and jd_id are required'}), 400
        
        if len(resume_ids) > 5:
            return jsonify({'error': 'Maximum 5 candidates can be compared at once'}), 400
        
        jd = JobDescription.query.get(jd_id)
        if not jd:
            return jsonify({'error': 'Job description not found'}), 404
        
        # Get all candidates
        comparisons = []
        for resume_id in resume_ids:
            resume = Resume.query.get(resume_id)
            if not resume:
                continue
            
            analysis = ResumeAnalysis.query.filter_by(
                resume_id=resume_id,
                jd_id=jd_id
            ).first()
            
            parsed = resume.get_parsed_data()
            
            if not analysis:
                # Quick analysis
                match_score = text_processor.calculate_similarity(resume.raw_text, jd.description)
                ats_result = ats_scorer.calculate_ats_score(parsed)
                ats_score = ats_result['percentage']
            else:
                match_score = analysis.match_score
                ats_score = analysis.ats_score
            
            comparisons.append({
                'resume_id': resume_id,
                'name': parsed.get('name', 'Unknown'),
                'match_score': match_score,
                'ats_score': ats_score,
                'skills_count': len(parsed.get('skills', [])),
                'experience_count': len(parsed.get('experience', [])),
                'key_skills': parsed.get('skills', [])[:5],
                'overall_rating': _calculate_overall_rating(match_score, ats_score, {})
            })
        
        # Sort by match score
        comparisons.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add comparative insights
        if comparisons:
            best_candidate = comparisons[0]
            insights = {
                'best_match': best_candidate['name'],
                'best_match_score': best_candidate['match_score'],
                'score_range': {
                    'highest': comparisons[0]['match_score'],
                    'lowest': comparisons[-1]['match_score'],
                    'spread': comparisons[0]['match_score'] - comparisons[-1]['match_score']
                }
            }
        else:
            insights = {}
        
        response = {
            'jd_title': jd.title,
            'candidates_compared': len(comparisons),
            'comparisons': comparisons,
            'insights': insights
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Compare candidates error: {e}")
        return jsonify({'error': str(e)}), 500

@recruiter_bp.route('/analytics/<int:user_id>', methods=['GET'])
def get_analytics(user_id):
    """
    Recruitment analytics and insights
    """
    try:
        # Time range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get user's JDs
        jd_ids = [jd.id for jd in JobDescription.query.filter_by(user_id=user_id, is_active=True).all()]
        
        if not jd_ids:
            return jsonify({
                'message': 'No active job descriptions found',
                'analytics': {}
            }), 200
        
        # Get analyses in time range
        analyses = ResumeAnalysis.query.filter(
            ResumeAnalysis.jd_id.in_(jd_ids),
            ResumeAnalysis.analyzed_at >= start_date
        ).all()
        
        if not analyses:
            return jsonify({
                'message': f'No candidates reviewed in the last {days} days',
                'analytics': {}
            }), 200
        
        # Calculate analytics
        total_reviewed = len(analyses)
        shortlisted = len([a for a in analyses if a.match_score >= 70])
        excellent = len([a for a in analyses if a.match_score >= 85])
        
        match_scores = [a.match_score for a in analyses if a.match_score]
        ats_scores = [a.ats_score for a in analyses if a.ats_score]
        
        analytics = {
            'time_period': f'Last {days} days',
            'overview': {
                'total_candidates_reviewed': total_reviewed,
                'shortlisted_candidates': shortlisted,
                'excellent_candidates': excellent,
                'shortlist_rate': round((shortlisted / total_reviewed * 100) if total_reviewed > 0 else 0, 2)
            },
            'score_statistics': {
                'match_scores': {
                    'average': round(sum(match_scores) / len(match_scores), 2) if match_scores else 0,
                    'highest': max(match_scores) if match_scores else 0,
                    'lowest': min(match_scores) if match_scores else 0
                },
                'ats_scores': {
                    'average': round(sum(ats_scores) / len(ats_scores), 2) if ats_scores else 0,
                    'highest': max(ats_scores) if ats_scores else 0,
                    'lowest': min(ats_scores) if ats_scores else 0
                }
            },
            'trends': _calculate_trends(analyses, days),
            'top_skills_found': _get_top_skills_from_analyses(analyses),
            'recommendations': _generate_analytics_recommendations(analytics if 'analytics' in locals() else {}, total_reviewed, shortlisted)
        }
        
        return jsonify(analytics), 200
        
    except Exception as e:
        logger.error(f"❌ Analytics error: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== HELPER FUNCTIONS ====================

def _count_applicants(jd_id):
    """Count total applicants for a JD"""
    return ResumeAnalysis.query.filter_by(jd_id=jd_id).count()

def _count_shortlisted(jd_id):
    """Count shortlisted candidates for a JD"""
    return ResumeAnalysis.query.filter(
        ResumeAnalysis.jd_id == jd_id,
        ResumeAnalysis.match_score >= 70
    ).count()

def _get_candidate_status(match_score, ats_score):
    """Get candidate status"""
    if match_score >= 85 and ats_score >= 80:
        return {'status': 'Excellent', 'color': 'green', 'priority': 'high'}
    elif match_score >= 70 and ats_score >= 65:
        return {'status': 'Good', 'color': 'blue', 'priority': 'medium'}
    elif match_score >= 55:
        return {'status': 'Moderate', 'color': 'yellow', 'priority': 'low'}
    else:
        return {'status': 'Low Fit', 'color': 'red', 'priority': 'none'}

def _calculate_jd_performance(jd_ids):
    """Calculate performance metrics for JDs"""
    if not jd_ids:
        return []
    
    performance = []
    for jd_id in jd_ids:
        jd = JobDescription.query.get(jd_id)
        if not jd:
            continue
        
        total = _count_applicants(jd_id)
        shortlisted = _count_shortlisted(jd_id)
        
        analyses = ResumeAnalysis.query.filter_by(jd_id=jd_id).all()
        avg_match = 0
        if analyses:
            scores = [a.match_score for a in analyses if a.match_score]
            avg_match = sum(scores) / len(scores) if scores else 0
        
        performance.append({
            'jd_id': jd_id,
            'title': jd.title,
            'total_applicants': total,
            'shortlisted': shortlisted,
            'shortlist_rate': round((shortlisted / total * 100) if total > 0 else 0, 2),
            'average_match_score': round(avg_match, 2)
        })
    
    # Sort by shortlist rate
    performance.sort(key=lambda x: x['shortlist_rate'], reverse=True)
    return performance

def _generate_recruiter_insights(active_jds, total_reviewed, shortlisted):
    """Generate insights for recruiter"""
    insights = []
    
    if len(active_jds) == 0:
        insights.append({
            'type': 'action',
            'priority': 'high',
            'message': 'Create job descriptions to start screening candidates'
        })
    
    if total_reviewed > 0:
        shortlist_rate = (shortlisted / total_reviewed * 100)
        if shortlist_rate < 10:
            insights.append({
                'type': 'quality',
                'priority': 'medium',
                'message': f'Low shortlist rate ({shortlist_rate:.1f}%). Consider refining job requirements or sourcing strategy.'
            })
        elif shortlist_rate > 50:
            insights.append({
                'type': 'efficiency',
                'priority': 'low',
                'message': f'High shortlist rate ({shortlist_rate:.1f}%). You may want to raise the bar for screening.'
            })
    
    if total_reviewed < 10 and len(active_jds) > 0:
        insights.append({
            'type': 'sourcing',
            'priority': 'high',
            'message': 'Low candidate flow. Increase sourcing efforts to build a stronger pipeline.'
        })
    
    return insights

def _generate_screening_recommendation(match_score, ats_score, skill_analysis):
    """Generate screening recommendation"""
    skill_match = skill_analysis.get('match_percentage', 0)
    
    # Determine tier
    if match_score >= 80 and ats_score >= 75 and skill_match >= 70:
        tier = 'excellent'
        decision = 'Strong Hire - Schedule Interview ASAP'
        color = 'green'
        priority = 'high'
    elif match_score >= 70 and ats_score >= 65 and skill_match >= 55:
        tier = 'good'
        decision = 'Good Fit - Consider for Interview'
        color = 'blue'
        priority = 'medium'
    elif match_score >= 55 and skill_match >= 40:
        tier = 'moderate'
        decision = 'Moderate Fit - Review Carefully'
        color = 'yellow'
        priority = 'low'
    else:
        tier = 'low'
        decision = 'Low Fit - Not Recommended'
        color = 'red'
        priority = 'none'
    
    return {
        'tier': tier,
        'decision': decision,
        'color': color,
        'priority': priority,
        'confidence': _calculate_confidence(match_score, ats_score, skill_match)
    }

def _calculate_confidence(match_score, ats_score, skill_match):
    """Calculate recommendation confidence"""
    avg = (match_score + ats_score + skill_match) / 3
    
    if avg >= 75:
        return 'High'
    elif avg >= 60:
        return 'Medium'
    else:
        return 'Low'

def _generate_hiring_decision(match_score, ats_score, skill_analysis):
    """Generate detailed hiring decision"""
    skill_match = skill_analysis.get('match_percentage', 0)
    
    if match_score >= 85 and ats_score >= 80 and skill_match >= 75:
        return {
            'decision': 'Strong Hire',
            'confidence': 'High',
            'next_steps': [
                'Schedule technical interview immediately',
                'Check references',
                'Prepare offer discussion'
            ],
            'rationale': 'Excellent fit across all dimensions. Top candidate for the role.'
        }
    elif match_score >= 70 and ats_score >= 65 and skill_match >= 60:
        return {
            'decision': 'Consider for Interview',
            'confidence': 'Medium-High',
            'next_steps': [
                'Phone screen to assess interest',
                'Technical assessment',
                'In-person/video interview if passes'
            ],
            'rationale': 'Good overall fit with some minor gaps. Worth interviewing.'
        }
    elif match_score >= 55:
        return {
            'decision': 'Maybe - Review Carefully',
            'confidence': 'Medium-Low',
            'next_steps': [
                'Detailed resume review',
                'Assess potential vs requirements',
                'Consider for junior role if applicable'
            ],
            'rationale': 'Moderate fit with noticeable gaps. May be suitable with training.'
        }
    else:
        return {
            'decision': 'Pass',
            'confidence': 'High',
            'next_steps': [
                'Send rejection email (if required)',
                'Keep in talent pool for other roles',
                'Encourage reapplication after upskilling'
            ],
            'rationale': 'Significant gaps between requirements and candidate profile.'
        }

def _calculate_overall_rating(match_score, ats_score, skill_analysis):
    """Calculate overall candidate rating"""
    skill_match = skill_analysis.get('match_percentage', 0) if skill_analysis else 0
    
    # Weighted average
    overall = (match_score * 0.4 + ats_score * 0.3 + skill_match * 0.3)
    
    if overall >= 80:
        return {'rating': 'A+', 'score': round(overall, 2), 'label': 'Excellent'}
    elif overall >= 70:
        return {'rating': 'A', 'score': round(overall, 2), 'label': 'Very Good'}
    elif overall >= 60:
        return {'rating': 'B+', 'score': round(overall, 2), 'label': 'Good'}
    elif overall >= 50:
        return {'rating': 'B', 'score': round(overall, 2), 'label': 'Fair'}
    else:
        return {'rating': 'C', 'score': round(overall, 2), 'label': 'Below Average'}

def _get_quick_recommendation(match_score, ats_score):
    """Quick recommendation text"""
    if match_score >= 85 and ats_score >= 80:
        return 'Excellent - Interview Now'
    elif match_score >= 75 and ats_score >= 70:
        return 'Strong - Schedule Interview'
    elif match_score >= 65:
        return 'Good - Consider'
    elif match_score >= 55:
        return 'Moderate - Review'
    else:
        return 'Low Fit - Pass'

def _calculate_trends(analyses, days):
    """Calculate recruitment trends"""
    if not analyses or days < 7:
        return {}
    
    # Split into two halves
    mid_point = datetime.utcnow() - timedelta(days=days/2)
    
    first_half = [a for a in analyses if a.analyzed_at < mid_point]
    second_half = [a for a in analyses if a.analyzed_at >= mid_point]
    
    if not first_half or not second_half:
        return {}
    
    # Compare volumes
    volume_change = ((len(second_half) - len(first_half)) / len(first_half) * 100)
    
    # Compare quality (match scores)
    first_avg = sum(a.match_score for a in first_half if a.match_score) / len(first_half)
    second_avg = sum(a.match_score for a in second_half if a.match_score) / len(second_half)
    quality_change = second_avg - first_avg
    
    return {
        'candidate_volume': {
            'change_percentage': round(volume_change, 2),
            'trend': 'increasing' if volume_change > 0 else 'decreasing'
        },
        'candidate_quality': {
            'change_points': round(quality_change, 2),
            'trend': 'improving' if quality_change > 0 else 'declining'
        }
    }

def _get_top_skills_from_analyses(analyses):
    """Get most common skills from analyzed candidates"""
    if not analyses:
        return []
    
    skill_count = {}
    
    for analysis in analyses:
        if analysis.resume:
            parsed = analysis.resume.get_parsed_data()
            skills = parsed.get('skills', [])
            for skill in skills:
                skill_lower = skill.lower()
                skill_count[skill_lower] = skill_count.get(skill_lower, 0) + 1
    
    # Sort by frequency
    sorted_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)
    
    return [
        {'skill': skill.title(), 'frequency': count}
        for skill, count in sorted_skills[:10]
    ]

def _generate_analytics_recommendations(analytics, total_reviewed, shortlisted):
    """Generate recommendations based on analytics"""
    recommendations = []
    
    if total_reviewed > 0:
        shortlist_rate = (shortlisted / total_reviewed * 100)
        
        if shortlist_rate < 15:
            recommendations.append({
                'title': 'Improve Candidate Sourcing',
                'message': 'Low shortlist rate indicates quality issues with candidate pipeline',
                'action': 'Review sourcing channels and refine targeting'
            })
        
        if shortlist_rate > 60:
            recommendations.append({
                'title': 'Raise Screening Bar',
                'message': 'Very high shortlist rate may indicate lenient screening',
                'action': 'Consider increasing threshold or being more selective'
            })
    
    if total_reviewed < 20:
        recommendations.append({
            'title': 'Increase Candidate Flow',
            'message': 'Low number of candidates reviewed',
            'action': 'Expand sourcing efforts and promote open positions'
        })
    
    return recommendations