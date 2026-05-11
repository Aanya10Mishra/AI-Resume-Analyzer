"""
Main Flask Application
Resume Analyzer API with Sentence Transformers
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import logging
import threading
import uuid

from config import get_config
from models.database import db, User, Resume, JobDescription, ResumeAnalysis
from utils import ResumeParser, TextProcessor, ATSScorer

# Role-specific blueprints
from routes.student_routes import student_bp, init_student_routes
from routes.employee_routes import employee_bp, init_employee_routes
from routes.hr_routes import recruiter_bp, init_recruiter_routes

# AI routes
from routes.ai_routes import ai_bp, init_ai_routes

# Authentication routes
from routes.auth_routes import auth_bp

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_app(config_name="development"):
    """Application factory"""

    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Create upload folder
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize utilities
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Initializing Resume Analyzer with Sentence Transformers")
    logger.info("=" * 60 + "\n")

    resume_parser = ResumeParser()
    text_processor = TextProcessor(app.config["EMBEDDING_MODEL"])
    ats_scorer = ATSScorer()
    
    # In-memory async analysis job store
    analysis_jobs = {}
    analysis_jobs_lock = threading.Lock()
    analysis_job_ttl = timedelta(minutes=30)

    # ==================== REGISTER ROLE-BASED ROUTES ====================
    
    logger.info("📋 Registering role-based routes...")
    
    # Initialize role blueprints with shared utils
    init_student_routes(text_processor, ats_scorer)
    init_employee_routes(text_processor, ats_scorer)
    init_recruiter_routes(text_processor, ats_scorer)

    # Register blueprints
    app.register_blueprint(student_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(recruiter_bp)
    
    logger.info("✅ Role-based routes registered!")

    # ==================== REGISTER AI ROUTES ====================
    
    logger.info("🤖 Registering AI-powered routes...")
    
    # Initialize AI routes
    init_ai_routes(ats_scorer)
    
    # Register AI blueprint
    app.register_blueprint(ai_bp)
    
    logger.info("✅ AI routes registered!")
    logger.info("   - Resume improvement: /api/ai/improve-resume/<resume_id>")
    logger.info("   - Career advice: /api/ai/career-advice/<user_id>")
    logger.info("   - Interview prep: /api/ai/interview-prep/<resume_id>/<jd_id>")
    logger.info("   - Career path: /api/ai/career-path/<user_id>")
    logger.info("   - Skill recommendations: /api/ai/skill-recommendations/<resume_id>")
    logger.info("   - Job optimization: /api/ai/optimize-for-job/<resume_id>/<jd_id>\n")

    # ==================== REGISTER AUTHENTICATION ROUTES ====================
    
    logger.info("🔐 Registering authentication routes...")
    
    # Register authentication blueprint
    app.register_blueprint(auth_bp)
    
    logger.info("✅ Authentication routes registered!")
    logger.info("   - Signup: POST /api/auth/signup")
    logger.info("   - Login: POST /api/auth/login")
    logger.info("   - Forgot password: POST /api/auth/forgot-password")
    logger.info("   - Reset password: POST /api/auth/reset-password")
    logger.info("   - Change password: POST /api/auth/change-password/<user_id>")
    logger.info("   - Get user: GET /api/auth/user/<user_id>")
    logger.info("   - Update user: PUT /api/auth/user/<user_id>\n")

    logger.info("\n✅ All systems ready!\n")

    # Helper functions
    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    
    def prune_expired_analysis_jobs():
        """Clean up stale analysis jobs from memory."""
        cutoff = datetime.utcnow() - analysis_job_ttl
        with analysis_jobs_lock:
            stale_ids = [
                job_id for job_id, job in analysis_jobs.items()
                if datetime.fromisoformat(job["updated_at"]) < cutoff
            ]
            for job_id in stale_ids:
                analysis_jobs.pop(job_id, None)
    
    def update_analysis_job(job_id, **updates):
        """Thread-safe update for an async analysis job."""
        with analysis_jobs_lock:
            job = analysis_jobs.get(job_id)
            if not job:
                return
            job.update(updates)
            job["updated_at"] = datetime.utcnow().isoformat()
    
    def perform_analysis(resume_id: int, jd_id: int, progress_callback=None):
        """
        Shared analysis logic used by both sync and async endpoints.
        Returns the same payload shape as the legacy sync endpoint.
        """
        if progress_callback:
            progress_callback("Loading resume and job description...", 10)
        
        resume = Resume.query.get(resume_id)
        jd = JobDescription.query.get(jd_id)

        if not resume or not jd:
            raise ValueError("Resume or JD not found")

        logger.info(f"\n🔍 Analyzing: Resume {resume.id} vs JD {jd.id}")

        if progress_callback:
            progress_callback("Running semantic and skill matching...", 45)
        
        detailed_match = text_processor.calculate_detailed_match(
            resume.raw_text,
            jd.description
        )

        if progress_callback:
            progress_callback("Computing ATS score and improvement suggestions...", 75)
        
        parsed_data = resume.get_parsed_data()
        ats_result = ats_scorer.calculate_ats_score(parsed_data)
        skill_analysis = detailed_match.get("skill_analysis", {})
        
        suggestions = text_processor.get_improvement_suggestions(
            resume.raw_text,
            jd.description,
            detailed_match
        )
        recommendations = generate_recommendations(detailed_match)

        if progress_callback:
            progress_callback("Saving analysis result...", 90)
        
        analysis = ResumeAnalysis(
            resume_id=resume.id,
            jd_id=jd.id,
            ats_score=ats_result["percentage"],
            match_score=detailed_match["overall_match"],
            semantic_score=detailed_match.get("semantic_similarity", detailed_match["overall_match"])
        )
        analysis.set_skill_gaps(skill_analysis.get("unmatched_jd_skills", []))
        analysis.set_section_scores(detailed_match.get("section_scores", {}))

        db.session.add(analysis)
        db.session.commit()

        logger.info(f"✅ Analysis complete! Match: {detailed_match['overall_match']}%\n")
        
        return {
            "analysis_id": analysis.id,
            
            # Main scores
            "match_score": detailed_match["overall_match"],
            "ats_score": ats_result,
            
            # Detailed breakdown
            "score_breakdown": {
                "semantic_similarity": detailed_match.get("semantic_similarity", 0),
                "skill_match": detailed_match.get("skill_match", 0),
                "experience_match": detailed_match.get("experience_match", 0),
                "keyword_match": detailed_match.get("keyword_match", 0)
            },
            
            # Weights used
            "scoring_weights": detailed_match.get("weights", {}),
            
            # Skills analysis
            "matched_skills": skill_analysis.get("matched_skills", []),
            "missing_skills": skill_analysis.get("unmatched_jd_skills", []),
            "extra_skills": skill_analysis.get("extra_resume_skills", []),
            
            # Experience analysis
            "experience_analysis": detailed_match.get("experience_analysis", {}),
            
            # Section scores
            "section_scores": detailed_match.get("section_scores", {}),
            
            # Improvement suggestions
            "suggestions": suggestions,
            
            # Recommendations
            "recommendations": recommendations,
            
            # Legacy support (keep for backward compatibility)
            "match_details": detailed_match,
            "skill_analysis": skill_analysis
        }
    
    def run_analysis_job(job_id: str, resume_id: int, jd_id: int):
        """Background worker for async analysis endpoint."""
        try:
            update_analysis_job(
                job_id,
                status="running",
                progress=15,
                message="Analysis started..."
            )
            
            with app.app_context():
                result = perform_analysis(
                    resume_id,
                    jd_id,
                    progress_callback=lambda message, progress: update_analysis_job(
                        job_id,
                        status="running",
                        message=message,
                        progress=progress
                    )
                )
                
                update_analysis_job(
                    job_id,
                    status="completed",
                    progress=100,
                    message="Analysis complete",
                    completed_at=datetime.utcnow().isoformat(),
                    result=result
                )
        except Exception as e:
            with app.app_context():
                db.session.rollback()
            logger.error(f"❌ Async analysis error ({job_id}): {e}")
            update_analysis_job(
                job_id,
                status="failed",
                progress=100,
                message="Analysis failed",
                error=str(e)
            )

    # ==================== HEALTH CHECK ====================

    @app.route("/", methods=["GET"])
    def home():
        """Home endpoint"""
        return jsonify({
            "name": "Resume Analyzer API",
            "version": "2.0.0",
            "status": "running",
            "features": [
                "Resume Parsing (PDF/DOCX)",
                "Semantic Matching (Sentence Transformers)",
                "ATS Scoring",
                "Skill Gap Analysis",
                "Career Recommendations",
                "Role-Based Dashboards",
                "AI-Powered Suggestions (Groq)",
                "Career Data (O*NET)"
            ],
            "embedding_model": app.config["EMBEDDING_MODEL"],
            "endpoints": {
                "auth": "/api/auth/*",
                "resume": "/api/resume/*",
                "jd": "/api/jd/*",
                "analysis": "/api/analyze/*",
                "student": "/api/student/*",
                "employee": "/api/employee/*",
                "recruiter": "/api/recruiter/*",
                "ai": "/api/ai/*"
            },
            "ai_powered": True
        }), 200

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        stats = text_processor.get_stats()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "embedding_model": app.config["EMBEDDING_MODEL"],
            "cache_stats": stats
        }), 200

    # ==================== AUTHENTICATION ====================

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        """Register new user"""
        try:
            data = request.get_json()

            required_fields = ["email", "password", "full_name", "role"]
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing required fields"}), 400

            if not User.validate_role(data["role"]):
                return jsonify({"error": "Invalid role. Must be: student, employee, or hr"}), 400

            if User.query.filter_by(email=data["email"]).first():
                return jsonify({"error": "Email already registered"}), 400

            user = User(
                email=data["email"],
                password_hash=generate_password_hash(data["password"]),
                full_name=data["full_name"],
                role=data["role"],
                experience_level=data.get("experience_level"),
                company_name=data.get("company_name"),
                department=data.get("department")
            )

            db.session.add(user)
            db.session.commit()

            logger.info(f"✅ New user registered: {user.email} ({user.role})")

            return jsonify({
                "message": "User registered successfully",
                "user": user.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Registration error: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        """Login user"""
        try:
            data = request.get_json()

            if not all(k in data for k in ["email", "password"]):
                return jsonify({"error": "Missing email or password"}), 400

            user = User.query.filter_by(email=data["email"]).first()

            if not user or not check_password_hash(user.password_hash, data["password"]):
                return jsonify({"error": "Invalid credentials"}), 401

            user.last_login = datetime.utcnow()
            db.session.commit()

            logger.info(f"✅ User logged in: {user.email}")

            return jsonify({
                "message": "Login successful",
                "user": user.to_dict()
            }), 200

        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return jsonify({"error": str(e)}), 500

    # ==================== RESUME OPERATIONS ====================

    @app.route("/api/resume/upload", methods=["POST"])
    def upload_resume():
        """Upload and parse resume"""
        try:
            if "file" not in request.files:
                return jsonify({"error": "No file provided"}), 400

            file = request.files["file"]
            user_id = request.form.get("user_id")

            if not user_id:
                return jsonify({"error": "User ID required"}), 400
            
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid user ID"}), 400
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400
            if not allowed_file(file.filename):
                return jsonify({"error": "Invalid file type. Only PDF and DOCX allowed"}), 400

            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{user_id}_{timestamp}_{filename}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
            file.save(file_path)

            file_size = os.path.getsize(file_path)

            logger.info(f"📄 Parsing resume: {filename} ({file_size} bytes)")
            logger.info(f"   User ID: {user_id} (type: {type(user_id).__name__})")

            parsed_data = resume_parser.parse(file_path)
            ats_result = ats_scorer.calculate_ats_score(parsed_data)

            logger.info("🧠 Generating embedding...")
            embedding = text_processor.get_embedding(parsed_data["raw_text"])

            resume = Resume(
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                raw_text=parsed_data["raw_text"],
                last_analyzed=datetime.utcnow()
            )
            resume.set_parsed_data(parsed_data)
            resume.set_embedding(embedding)

            db.session.add(resume)
            db.session.commit()

            logger.info(f"✅ Resume saved with ID: {resume.id}\n")

            return jsonify({
                "message": "Resume uploaded and parsed successfully",
                "resume_id": resume.id,
                "filename": filename,
                "parsed_data": {
                    "name": parsed_data.get("name"),
                    "email": parsed_data.get("email"),
                    "phone": parsed_data.get("phone"),
                    "linkedin": parsed_data.get("linkedin"),
                    "github": parsed_data.get("github"),
                    "skills": parsed_data.get("skills", []),
                    "experience_count": len(parsed_data.get("experience", [])),
                    "education_count": len(parsed_data.get("education", []))
                },
                "ats_score": ats_result
            }), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error uploading resume: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/resume/<int:resume_id>", methods=["GET"])
    def get_resume(resume_id):
        """Get resume details"""
        try:
            resume = Resume.query.get(resume_id)

            if not resume:
                return jsonify({"error": "Resume not found"}), 404

            parsed_data = resume.get_parsed_data()
            ats_result = ats_scorer.calculate_ats_score(parsed_data)

            return jsonify({
                "resume": resume.to_dict(),
                "ats_score": ats_result
            }), 200

        except Exception as e:
            logger.error(f"❌ Error getting resume: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/resume/user/<int:user_id>", methods=["GET"])
    def get_user_resumes(user_id):
        """Get all resumes for a user"""
        try:
            resumes = Resume.query.filter_by(user_id=user_id, is_active=True).order_by(
                Resume.uploaded_at.desc()
            ).all()

            return jsonify({
                "resumes": [resume.to_dict() for resume in resumes],
                "total": len(resumes)
            }), 200

        except Exception as e:
            logger.error(f"❌ Error getting user resumes: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/resume/<int:resume_id>", methods=["DELETE"])
    def delete_resume(resume_id):
        """Delete resume (soft delete)"""
        try:
            resume = Resume.query.get(resume_id)

            if not resume:
                return jsonify({"error": "Resume not found"}), 404

            resume.is_active = False
            db.session.commit()

            logger.info(f"🗑️ Resume {resume_id} deleted")

            return jsonify({"message": "Resume deleted successfully"}), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error deleting resume: {e}")
            return jsonify({"error": str(e)}), 500

    # ==================== JOB DESCRIPTION OPERATIONS ====================

    @app.route("/api/jd/create", methods=["POST"])
    def create_jd():
        """Create job description"""
        try:
            data = request.get_json()

            required_fields = ["user_id", "title", "description"]
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing required fields"}), 400

            logger.info(f"📋 Creating JD: {data['title']}")

            skills = resume_parser.extract_skills(data["description"])

            logger.info("🧠 Generating JD embedding...")
            embedding = text_processor.get_embedding(data["description"])

            jd = JobDescription(
                user_id=data["user_id"],
                title=data["title"],
                company=data.get("company", ""),
                location=data.get("location", ""),
                employment_type=data.get("employment_type", ""),
                experience_required=data.get("experience_required", ""),
                description=data["description"],
                requirements=data.get("requirements", ""),
                responsibilities=data.get("responsibilities", ""),
                benefits=data.get("benefits", "")
            )
            jd.set_parsed_skills(skills)
            jd.set_embedding(embedding)

            db.session.add(jd)
            db.session.commit()

            logger.info(f"✅ JD saved with ID: {jd.id}\n")

            return jsonify({
                "message": "Job description created successfully",
                "jd": jd.to_dict()
            }), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating JD: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jd/<int:jd_id>", methods=["GET"])
    def get_jd(jd_id):
        """Get job description"""
        try:
            jd = JobDescription.query.get(jd_id)

            if not jd:
                return jsonify({"error": "Job description not found"}), 404

            return jsonify({"jd": jd.to_dict()}), 200

        except Exception as e:
            logger.error(f"❌ Error getting JD: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/jd/user/<int:user_id>", methods=["GET"])
    def get_user_jds(user_id):
        """Get user's job descriptions"""
        try:
            jds = JobDescription.query.filter_by(user_id=user_id, is_active=True).order_by(
                JobDescription.created_at.desc()
            ).all()

            return jsonify({
                "job_descriptions": [jd.to_dict() for jd in jds],
                "total": len(jds)
            }), 200

        except Exception as e:
            logger.error(f"❌ Error getting JDs: {e}")
            return jsonify({"error": str(e)}), 500

               # ==================== ANALYSIS ====================

    @app.route("/api/analyze/match", methods=["POST"])
    def analyze_match():
        """Analyze resume vs JD with detailed scoring"""
        try:
            data = request.get_json(silent=True) or {}

            if not all(k in data for k in ["resume_id", "jd_id"]):
                return jsonify({"error": "Missing resume_id or jd_id"}), 400
            
            try:
                resume_id = int(data["resume_id"])
                jd_id = int(data["jd_id"])
            except (TypeError, ValueError):
                return jsonify({"error": "resume_id and jd_id must be integers"}), 400
            
            result = perform_analysis(resume_id, jd_id)
            return jsonify(result), 200

        except ValueError as e:
            if str(e) == "Resume or JD not found":
                return jsonify({"error": str(e)}), 404
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Analysis error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/analyze/match/async", methods=["POST"])
    def analyze_match_async():
        """Start async resume vs JD analysis and return job id immediately."""
        try:
            prune_expired_analysis_jobs()
            data = request.get_json(silent=True) or {}

            if not all(k in data for k in ["resume_id", "jd_id"]):
                return jsonify({"error": "Missing resume_id or jd_id"}), 400
            
            try:
                resume_id = int(data["resume_id"])
                jd_id = int(data["jd_id"])
            except (TypeError, ValueError):
                return jsonify({"error": "resume_id and jd_id must be integers"}), 400
            
            if not Resume.query.get(resume_id) or not JobDescription.query.get(jd_id):
                return jsonify({"error": "Resume or JD not found"}), 404
            
            job_id = uuid.uuid4().hex
            now_iso = datetime.utcnow().isoformat()

            with analysis_jobs_lock:
                analysis_jobs[job_id] = {
                    "job_id": job_id,
                    "status": "queued",
                    "progress": 5,
                    "message": "Analysis queued",
                    "resume_id": resume_id,
                    "jd_id": jd_id,
                    "created_at": now_iso,
                    "updated_at": now_iso
                }
            
            worker = threading.Thread(
                target=run_analysis_job,
                args=(job_id, resume_id, jd_id),
                daemon=True
            )
            worker.start()
            
            return jsonify({
                "job_id": job_id,
                "status": "queued",
                "message": "Analysis job started",
                "poll_interval_ms": 1200
            }), 202
        except Exception as e:
            logger.error(f"❌ Failed to start async analysis: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/analyze/match/status/<string:job_id>", methods=["GET"])
    def analyze_match_status(job_id):
        """Get status/progress (and final result) for an async analysis job."""
        prune_expired_analysis_jobs()
        
        with analysis_jobs_lock:
            job = analysis_jobs.get(job_id)
            if not job:
                return jsonify({"error": "Analysis job not found or expired"}), 404
            payload = dict(job)
        
        # Only include heavy result payload when completed
        if payload.get("status") != "completed":
            payload.pop("result", None)
        
        return jsonify(payload), 200

    def generate_recommendations(match_data: dict) -> list:
        """Generate actionable recommendations based on match analysis"""
        recommendations = []
        
        overall = match_data.get("overall_match", 0)
        skill_match = match_data.get("skill_match", 0)
        semantic = match_data.get("semantic_similarity", 0)
        experience = match_data.get("experience_match", 0)
        keywords = match_data.get("keyword_match", 0)
        
        # Overall assessment
        if overall >= 80:
            recommendations.append("🎉 Excellent match! Your resume aligns very well with this position.")
        elif overall >= 60:
            recommendations.append("👍 Good match! A few improvements could make your application stronger.")
        elif overall >= 40:
            recommendations.append("⚠️ Moderate match. Consider tailoring your resume more specifically for this role.")
        else:
            recommendations.append("🔴 Low match. This role may require significant skill development or resume revision.")
        
        # Skill-based recommendations
        if skill_match < 50:
            recommendations.append("📚 Focus on acquiring the missing technical skills through courses or projects.")
        elif skill_match < 75:
            recommendations.append("💡 Add a few more relevant skills to strengthen your technical profile.")
        
        # Semantic similarity recommendations
        if semantic < 60:
            recommendations.append("✍️ Rewrite your resume using similar language and terminology from the job description.")
        
        # Experience recommendations
        if experience < 100:
            exp_analysis = match_data.get("experience_analysis", {})
            years_gap = exp_analysis.get("years_gap", 0)
            if years_gap > 0:
                recommendations.append(f"📈 Highlight relevant projects, internships, or freelance work to bridge the {years_gap}-year experience gap.")
        
        # Keyword recommendations
        if keywords < 70:
            recommendations.append("🔑 Include more industry-specific keywords from the job posting in your resume.")
        
        # Section-specific recommendations
        section_scores = match_data.get("section_scores", {})
        
        if section_scores.get("projects", 0) < 40:
            recommendations.append("🛠️ Add or enhance your projects section with work relevant to this position.")
        
        if section_scores.get("summary", 0) < 40:
            recommendations.append("📝 Write a compelling summary/objective tailored to this specific role.")
        
        return recommendations

    return app


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()
        logger.info("\n✅ Database tables created!\n")

    logger.info("=" * 60)
    logger.info("🚀 Resume Analyzer API")
    logger.info("📍 http://localhost:5000")
    logger.info("=" * 60 + "\n")

    app.run(debug=True, port=5000, host="0.0.0.0")
