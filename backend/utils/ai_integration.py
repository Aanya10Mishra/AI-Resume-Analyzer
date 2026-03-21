"""
AI Integration
Groq API for AI-powered suggestions and Onet API for career data
"""
import os
import requests
from groq import Groq
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class GroqAI:
    """
    Groq AI Integration for resume suggestions
    Uses Llama 3 model for fast, high-quality responses
    """
    
    def __init__(self):
        """Initialize Groq client"""
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            logger.warning("⚠️  GROQ_API_KEY not found in environment variables")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=api_key)
                logger.info("✅ Groq AI client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Groq client: {e}")
                self.client = None
    
    def generate_resume_suggestions(self, resume_data: Dict, ats_score: Dict) -> List[Dict]:
        """
        Generate AI-powered resume improvement suggestions
        
        Args:
            resume_data: Parsed resume data
            ats_score: ATS score breakdown
            
        Returns:
            List of actionable suggestions
        """
        if not self.client:
            return self._fallback_suggestions(resume_data, ats_score)
        
        try:
            # Prepare context
            prompt = self._build_resume_improvement_prompt(resume_data, ats_score)
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Fast and powerful
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume consultant and career advisor. Provide specific, actionable advice to improve resumes for better ATS scores and job matches."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            # Parse response
            suggestions = self._parse_ai_suggestions(response.choices[0].message.content)
            
            logger.info(f"✅ Generated {len(suggestions)} AI suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Groq API error: {e}")
            return self._fallback_suggestions(resume_data, ats_score)
    
    def generate_career_advice(self, resume_data: Dict, target_role: str = None) -> Dict:
        """
        Generate personalized career advice
        
        Args:
            resume_data: Parsed resume data
            target_role: Optional target career
            
        Returns:
            Career advice dictionary
        """
        if not self.client:
            return self._fallback_career_advice()
        
        try:
            prompt = self._build_career_advice_prompt(resume_data, target_role)
            
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a career counselor with expertise in technology careers. Provide realistic, actionable career guidance."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            advice = self._parse_career_advice(response.choices[0].message.content)
            
            logger.info("✅ Generated career advice")
            return advice
            
        except Exception as e:
            logger.error(f"❌ Career advice error: {e}")
            return self._fallback_career_advice()
    
    def generate_interview_prep(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """
        Generate interview preparation tips
        
        Args:
            resume_data: Parsed resume data
            jd_data: Job description data
            
        Returns:
            Interview preparation guide
        """
        if not self.client:
            return self._fallback_interview_prep()
        
        try:
            prompt = self._build_interview_prep_prompt(resume_data, jd_data)
            
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an interview coach. Provide specific questions and preparation strategies based on the candidate's profile and job requirements."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            prep = self._parse_interview_prep(response.choices[0].message.content)
            
            logger.info("✅ Generated interview prep")
            return prep
            
        except Exception as e:
            logger.error(f"❌ Interview prep error: {e}")
            return self._fallback_interview_prep()
    
    # ========== PROMPT BUILDERS ==========
    
    def _build_resume_improvement_prompt(self, resume_data: Dict, ats_score: Dict) -> str:
        """Build prompt for resume improvement"""
        
        skills = resume_data.get('skills', [])
        experience = resume_data.get('experience', [])
        education = resume_data.get('education', [])
        
        prompt = f"""Analyze this resume and provide 5 specific, actionable improvement suggestions.

**Current Resume Details:**
- ATS Score: {ats_score.get('percentage', 0)}%
- Skills Count: {len(skills)}
- Skills: {', '.join(skills[:10]) if skills else 'None listed'}
- Experience Entries: {len(experience)}
- Education Entries: {len(education)}
- Has Email: {'Yes' if resume_data.get('email') else 'No'}
- Has Phone: {'Yes' if resume_data.get('phone') else 'No'}
- Has LinkedIn: {'Yes' if resume_data.get('linkedin') else 'No'}

**ATS Score Breakdown:**
{ats_score.get('breakdown', {})}

Provide exactly 5 suggestions in this format:
1. [Category] Suggestion text
2. [Category] Suggestion text
...

Categories should be: Skills, Experience, Format, Content, or Keywords."""

        return prompt
    
    def _build_career_advice_prompt(self, resume_data: Dict, target_role: str) -> str:
        """Build prompt for career advice"""
        
        skills = resume_data.get('skills', [])
        experience = resume_data.get('experience', [])
        
        prompt = f"""Provide career guidance for this professional.

**Current Profile:**
- Skills: {', '.join(skills[:15]) if skills else 'Not specified'}
- Experience Level: {len(experience)} positions
- Target Role: {target_role if target_role else 'Career exploration'}

Provide advice in these areas:
1. Next Career Steps (2-3 options)
2. Skills to Develop (Top 5)
3. Timeline Expectations (realistic)
4. Action Plan (immediate next steps)

Be specific and realistic."""

        return prompt
    
    def _build_interview_prep_prompt(self, resume_data: Dict, jd_data: Dict) -> str:
        """Build prompt for interview preparation"""
        
        skills = resume_data.get('skills', [])
        jd_title = jd_data.get('title', 'Position')
        jd_description = jd_data.get('description', '')[:500]  # Limit length
        
        prompt = f"""Prepare this candidate for an interview.

**Job:** {jd_title}

**Job Requirements:**
{jd_description}

**Candidate Skills:**
{', '.join(skills[:10]) if skills else 'Not specified'}

Provide:
1. Top 5 likely interview questions
2. How to answer each (brief tips)
3. 3 questions candidate should ask
4. Key points to emphasize from their background

Keep it practical and specific to this role."""

        return prompt
    
    # ========== RESPONSE PARSERS ==========
    
    def _parse_ai_suggestions(self, response_text: str) -> List[Dict]:
        """Parse AI response into structured suggestions"""
        
        suggestions = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Try to extract numbered suggestions
            if line[0].isdigit() and '.' in line[:3]:
                # Remove number prefix
                content = line.split('.', 1)[1].strip()
                
                # Try to extract category
                category = 'General'
                if '[' in content and ']' in content:
                    category = content[content.find('[')+1:content.find(']')]
                    content = content[content.find(']')+1:].strip()
                
                suggestions.append({
                    'category': category,
                    'suggestion': content,
                    'priority': 'high' if len(suggestions) < 2 else 'medium'
                })
        
        # Fallback if parsing fails
        if not suggestions:
            suggestions = [
                {
                    'category': 'General',
                    'suggestion': response_text[:200],
                    'priority': 'medium'
                }
            ]
        
        return suggestions[:5]  # Top 5
    
    def _parse_career_advice(self, response_text: str) -> Dict:
        """Parse career advice response"""
        
        return {
            'advice': response_text,
            'key_points': self._extract_key_points(response_text),
            'generated_at': 'AI-powered by Groq (Llama 3)'
        }
    
    def _parse_interview_prep(self, response_text: str) -> Dict:
        """Parse interview prep response"""
        
        return {
            'preparation_guide': response_text,
            'key_areas': self._extract_key_points(response_text)[:5],
            'generated_at': 'AI-powered by Groq (Llama 3)'
        }
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text"""
        
        points = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered or bulleted items
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up
                cleaned = line.lstrip('0123456789.-•* ').strip()
                if len(cleaned) > 20:
                    points.append(cleaned)
        
        return points[:8]  # Top 8 points
    
    # ========== FALLBACK METHODS ==========
    
    def _fallback_suggestions(self, resume_data: Dict, ats_score: Dict) -> List[Dict]:
        """Fallback suggestions when API unavailable"""
        
        suggestions = []
        
        if ats_score.get('percentage', 0) < 70:
            suggestions.append({
                'category': 'ATS Score',
                'suggestion': 'Improve your ATS score to 75%+ by adding more skills and experience details',
                'priority': 'high'
            })
        
        if len(resume_data.get('skills', [])) < 8:
            suggestions.append({
                'category': 'Skills',
                'suggestion': 'Add 3-5 more relevant technical skills to strengthen your profile',
                'priority': 'high'
            })
        
        if not resume_data.get('linkedin'):
            suggestions.append({
                'category': 'Contact',
                'suggestion': 'Include your LinkedIn profile URL for better credibility',
                'priority': 'medium'
            })
        
        suggestions.append({
            'category': 'Content',
            'suggestion': 'Use action verbs (developed, led, improved) to describe your experience',
            'priority': 'medium'
        })
        
        suggestions.append({
            'category': 'Format',
            'suggestion': 'Ensure consistent formatting and clear section headers',
            'priority': 'low'
        })
        
        return suggestions[:5]
    
    def _fallback_career_advice(self) -> Dict:
        """Fallback career advice"""
        return {
            'advice': 'Focus on developing in-demand skills, building projects, and networking in your target industry.',
            'key_points': [
                'Identify your strengths and interests',
                'Research target roles and requirements',
                'Develop missing technical skills',
                'Build a portfolio of projects',
                'Network with professionals in your field'
            ],
            'generated_at': 'Default advice (API unavailable)'
        }
    
    def _fallback_interview_prep(self) -> Dict:
        """Fallback interview prep"""
        return {
            'preparation_guide': 'Research the company, practice common questions, and prepare examples from your experience.',
            'key_areas': [
                'Tell me about yourself',
                'Why this company?',
                'Describe a challenging project',
                'Your technical skills',
                'Questions for the interviewer'
            ],
            'generated_at': 'Default prep (API unavailable)'
        }


class OnetAPI:
    """
    O*NET Career Information API Integration
    Provides career data, skills, salaries, job outlook
    """
    
    def __init__(self):
        """Initialize O*NET API client"""
        self.base_url = os.getenv('ONET_API_BASE_URL', 'https://services.onetcenter.org/ws/')
        self.username = os.getenv('ONET_USERNAME', '')
        self.password = os.getenv('ONET_PASSWORD', '')
        
        if self.username and self.password:
            self.auth = (self.username, self.password)
            logger.info("✅ O*NET API configured with authentication")
        else:
            self.auth = None
            logger.warning("⚠️  O*NET API credentials not found (using public access)")
    
    def search_careers(self, keywords: str, limit: int = 10) -> List[Dict]:
        """
        Search for careers by keywords
        
        Args:
            keywords: Search terms (e.g., "software developer")
            limit: Maximum results
            
        Returns:
            List of career options
        """
        try:
            url = f"{self.base_url}online/search"
            params = {
                'keyword': keywords,
                'end': limit
            }
            
            response = requests.get(url, params=params, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                careers = self._parse_career_search(data)
                logger.info(f"✅ Found {len(careers)} careers for '{keywords}'")
                return careers
            else:
                logger.warning(f"⚠️  O*NET API returned {response.status_code}")
                return self._fallback_careers(keywords)
                
        except Exception as e:
            logger.error(f"❌ O*NET search error: {e}")
            return self._fallback_careers(keywords)
    
    def get_career_details(self, onet_code: str) -> Dict:
        """
        Get detailed information about a specific career
        
        Args:
            onet_code: O*NET occupation code (e.g., "15-1252.00")
            
        Returns:
            Career details including skills, tasks, salary
        """
        try:
            url = f"{self.base_url}online/occupations/{onet_code}"
            
            response = requests.get(url, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                details = self._parse_career_details(data)
                logger.info(f"✅ Retrieved details for {onet_code}")
                return details
            else:
                return self._fallback_career_details()
                
        except Exception as e:
            logger.error(f"❌ Career details error: {e}")
            return self._fallback_career_details()
    
    def get_career_outlook(self, onet_code: str) -> Dict:
        """
        Get career outlook and salary information
        
        Args:
            onet_code: O*NET occupation code
            
        Returns:
            Outlook and salary data
        """
        try:
            # This is a simplified version
            # Real implementation would call multiple O*NET endpoints
            
            return {
                'growth_rate': 'Faster than average',
                'outlook': 'Excellent',
                'median_salary': 'Varies by role and location',
                'note': 'Connect paid API for detailed salary data',
                'source': 'O*NET Database'
            }
            
        except Exception as e:
            logger.error(f"❌ Career outlook error: {e}")
            return {}
    
    # ========== PARSERS ==========
    
    def _parse_career_search(self, data: Dict) -> List[Dict]:
        """Parse O*NET search results"""
        
        careers = []
        occupations = data.get('occupation', [])
        
        for occ in occupations[:10]:
            careers.append({
                'code': occ.get('code'),
                'title': occ.get('title'),
                'description': occ.get('description', '')[:200]
            })
        
        return careers
    
    def _parse_career_details(self, data: Dict) -> Dict:
        """Parse career details"""
        
        return {
            'title': data.get('title'),
            'description': data.get('description'),
            'tasks': data.get('tasks', [])[:5],
            'skills': data.get('skills', [])[:10],
            'knowledge': data.get('knowledge', [])[:10],
            'source': 'O*NET Database'
        }
    
    # ========== FALLBACKS ==========
    
    def _fallback_careers(self, keywords: str) -> List[Dict]:
        """Fallback career list"""
        
        # Common tech careers
        common_careers = {
            'software': [
                {'code': '15-1252.00', 'title': 'Software Developer', 'description': 'Develop software applications'},
                {'code': '15-1299.08', 'title': 'Web Developer', 'description': 'Create websites and web applications'},
            ],
            'data': [
                {'code': '15-2051.00', 'title': 'Data Scientist', 'description': 'Analyze complex data'},
                {'code': '15-2041.00', 'title': 'Data Analyst', 'description': 'Interpret data and create reports'},
            ]
        }
        
        for key in common_careers:
            if key in keywords.lower():
                return common_careers[key]
        
        return [
            {'code': '15-1252.00', 'title': 'Software Developer', 'description': 'Develop and maintain software'},
            {'code': '15-2051.00', 'title': 'Data Scientist', 'description': 'Analyze and interpret complex data'}
        ]
    
    def _fallback_career_details(self) -> Dict:
        """Fallback career details"""
        return {
            'title': 'Career Information',
            'description': 'Career details unavailable',
            'tasks': ['Various job-related tasks'],
            'skills': ['Technical skills', 'Communication', 'Problem solving'],
            'source': 'Default data (API unavailable)'
        }