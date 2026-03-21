"""
Database models for Resume Analyzer
All SQLAlchemy models are defined here
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    """
    User model for authentication and profile management
    Supports three roles: student, employee, hr
    """
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Authentication fields
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Profile fields
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'employee', 'hr'
    
    # Role-specific fields
    experience_level = db.Column(db.String(50))  # 'fresher', 'junior', 'mid', 'senior'
    company_name = db.Column(db.String(200))  # For HR users
    department = db.Column(db.String(100))  # For HR users
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    resumes = db.relationship('Resume', backref='user', lazy='dynamic', 
                            cascade='all, delete-orphan')
    job_descriptions = db.relationship('JobDescription', backref='user', lazy='dynamic',
                                      cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'experience_level': self.experience_level,
            'company_name': self.company_name,
            'department': self.department,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    @staticmethod
    def validate_role(role):
        """Validate user role"""
        valid_roles = ['student', 'employee', 'hr']
        return role in valid_roles

class Resume(db.Model):
    """
    Resume model to store uploaded resumes and parsed data
    Stores embeddings for fast semantic matching
    """
    __tablename__ = 'resumes'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    
    # Resume content
    raw_text = db.Column(db.Text)
    parsed_data = db.Column(db.Text)  # JSON string
    
    # Embeddings (for fast semantic search)
    embedding = db.Column(db.Text)  # JSON array of floats
    
    # Metadata
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_analyzed = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    analyses = db.relationship('ResumeAnalysis', backref='resume', lazy='dynamic',
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Resume {self.filename}>'
    
    def set_parsed_data(self, data):
        """Store parsed data as JSON"""
        self.parsed_data = json.dumps(data, ensure_ascii=False)
    
    def get_parsed_data(self):
        """Retrieve parsed data from JSON"""
        if self.parsed_data:
            try:
                return json.loads(self.parsed_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_embedding(self, embedding):
        """Store embedding vector as JSON"""
        import numpy as np
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        self.embedding = json.dumps(embedding)
    
    def get_embedding(self):
        """Retrieve embedding vector"""
        if self.embedding:
            try:
                import numpy as np
                return np.array(json.loads(self.embedding))
            except json.JSONDecodeError:
                return None
        return None
    
    def to_dict(self, include_text=False):
        """Convert resume to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'is_active': self.is_active,
            'parsed_data': self.get_parsed_data()
        }
        if include_text:
            data['raw_text'] = self.raw_text
        return data

class JobDescription(db.Model):
    """
    Job Description model
    Stores JDs posted by users (especially HR)
    """
    __tablename__ = 'job_descriptions'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Job details
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200))
    location = db.Column(db.String(200))
    employment_type = db.Column(db.String(50))  # 'full-time', 'part-time', 'contract', 'internship'
    experience_required = db.Column(db.String(50))  # '0-1', '1-3', '3-5', '5+'
    
    # Description
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    responsibilities = db.Column(db.Text)
    benefits = db.Column(db.Text)
    
    # Parsed data
    parsed_skills = db.Column(db.Text)  # JSON array
    
    # Embeddings
    embedding = db.Column(db.Text)  # JSON array
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analyses = db.relationship('ResumeAnalysis', backref='job_description', lazy='dynamic')
    
    def __repr__(self):
        return f'<JobDescription {self.title}>'
    
    def set_parsed_skills(self, skills):
        """Store skills as JSON"""
        self.parsed_skills = json.dumps(skills, ensure_ascii=False)
    
    def get_parsed_skills(self):
        """Retrieve skills from JSON"""
        if self.parsed_skills:
            try:
                return json.loads(self.parsed_skills)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_embedding(self, embedding):
        """Store embedding vector"""
        import numpy as np
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
        self.embedding = json.dumps(embedding)
    
    def get_embedding(self):
        """Retrieve embedding vector"""
        if self.embedding:
            try:
                import numpy as np
                return np.array(json.loads(self.embedding))
            except json.JSONDecodeError:
                return None
        return None
    
    def to_dict(self):
        """Convert JD to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'employment_type': self.employment_type,
            'experience_required': self.experience_required,
            'description': self.description,
            'requirements': self.requirements,
            'responsibilities': self.responsibilities,
            'benefits': self.benefits,
            'parsed_skills': self.get_parsed_skills(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ResumeAnalysis(db.Model):
    """
    Analysis results from matching resumes with job descriptions
    Stores all scoring and recommendation data
    """
    __tablename__ = 'resume_analyses'
    
    # Primary key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    resume_id = db.Column(db.Integer, db.ForeignKey('resumes.id'), nullable=False, index=True)
    jd_id = db.Column(db.Integer, db.ForeignKey('job_descriptions.id'), index=True)
    
    # Scores
    ats_score = db.Column(db.Float)  # 0-100
    match_score = db.Column(db.Float)  # 0-100 (semantic similarity)
    semantic_score = db.Column(db.Float)  # 0-100 (from embeddings)
    
    # Detailed analysis results (JSON)
    skill_gaps = db.Column(db.Text)  # Missing skills
    suggestions = db.Column(db.Text)  # Improvement suggestions
    career_recommendations = db.Column(db.Text)  # Career path suggestions
    section_scores = db.Column(db.Text)  # Section-wise breakdown
    
    # Metadata
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Analysis Resume:{self.resume_id} JD:{self.jd_id}>'
    
    def set_skill_gaps(self, gaps):
        """Store skill gaps as JSON"""
        self.skill_gaps = json.dumps(gaps, ensure_ascii=False)
    
    def get_skill_gaps(self):
        """Retrieve skill gaps"""
        if self.skill_gaps:
            try:
                return json.loads(self.skill_gaps)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_suggestions(self, suggestions):
        """Store suggestions as JSON"""
        self.suggestions = json.dumps(suggestions, ensure_ascii=False)
    
    def get_suggestions(self):
        """Retrieve suggestions"""
        if self.suggestions:
            try:
                return json.loads(self.suggestions)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_career_recommendations(self, recommendations):
        """Store career recommendations as JSON"""
        self.career_recommendations = json.dumps(recommendations, ensure_ascii=False)
    
    def get_career_recommendations(self):
        """Retrieve career recommendations"""
        if self.career_recommendations:
            try:
                return json.loads(self.career_recommendations)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_section_scores(self, scores):
        """Store section scores as JSON"""
        self.section_scores = json.dumps(scores, ensure_ascii=False)
    
    def get_section_scores(self):
        """Retrieve section scores"""
        if self.section_scores:
            try:
                return json.loads(self.section_scores)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def to_dict(self):
        """Convert analysis to dictionary"""
        return {
            'id': self.id,
            'resume_id': self.resume_id,
            'jd_id': self.jd_id,
            'ats_score': self.ats_score,
            'match_score': self.match_score,
            'semantic_score': self.semantic_score,
            'skill_gaps': self.get_skill_gaps(),
            'suggestions': self.get_suggestions(),
            'career_recommendations': self.get_career_recommendations(),
            'section_scores': self.get_section_scores(),
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None
        }

# Helper function to initialize database
def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")

def reset_db(app):
    """Reset database (use with caution!)"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Database reset successfully!")