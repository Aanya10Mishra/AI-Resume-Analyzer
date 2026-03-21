"""
Routes Package
Exports all route blueprints and initialization functions
"""
from .student_routes import student_bp, init_student_routes
from .employee_routes import employee_bp, init_employee_routes
from .hr_routes import recruiter_bp, init_recruiter_routes
from .ai_routes import ai_bp, init_ai_routes

__all__ = [
    # Blueprints
    'student_bp',
    'employee_bp', 
    'recruiter_bp',
    'ai_bp',
    
    # Initialization functions
    'init_student_routes',
    'init_employee_routes',
    'init_recruiter_routes',
    'init_ai_routes'
]