"""
AI Integration
Groq API for AI-powered suggestions and Onet API for career data
"""
import os
import requests
from groq import Groq
import logging
from typing import Dict, List, Optional
import json
import re
import signal
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class TimeoutException(Exception):
    pass

@contextmanager
def timeout(seconds):
    """Context manager for timeout handling"""
    def signal_handler(signum, frame):
        raise TimeoutException(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and alarm
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Disable the alarm
        signal.alarm(0)

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
            
            logger.info("🔄 Calling Groq API for resume suggestions (timeout: 20s, max_tokens: 1500)...")
            
            # Call Groq API - Generate detailed suggestions
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Fast and powerful
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume consultant and career advisor. Provide detailed, specific, actionable advice to improve resumes for better ATS scores and job matches. Be thorough and comprehensive."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500,  # Increased for detailed analysis
                timeout=20  # 20 second timeout
            )
            
            # Parse response
            suggestions = self._parse_ai_suggestions(response.choices[0].message.content)
            
            logger.info(f"✅ Generated {len(suggestions)} AI suggestions")
            return suggestions
            
        except Exception as e:
            logger.warning(f"⚠️  Resume suggestions error ({type(e).__name__}): {e}, using fallback")
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
            
            logger.info("🔄 Calling Groq API for career advice (timeout: 20s, max_tokens: 1500)...")
            
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a career counselor with expertise in technology careers. Provide detailed, realistic, actionable career guidance and recommendations. Be comprehensive and thorough."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500,  # Increased for detailed analysis
                timeout=20  # 20 second timeout
            )
            
            advice = self._parse_career_advice(response.choices[0].message.content)
            
            logger.info("✅ Generated career advice")
            return advice
            
        except Exception as e:
            logger.warning(f"⚠️  Career advice error ({type(e).__name__}): {e}, using fallback")
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
            logger.warning("⚠️  Groq client not available, using fallback")
            return self._fallback_interview_prep()
        
        try:
            prompt = self._build_interview_prep_prompt(resume_data, jd_data)
            
            logger.info("🔄 Calling Groq API for interview prep (timeout: 18s, max_tokens: 1400)...")
            
            # Call Groq API - Generate detailed interview preparation
            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert interview coach. Provide detailed, specific interview questions, comprehensive preparation strategies, and actionable tips based on the candidate's profile and job requirements. Be thorough and comprehensive."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1400,
                timeout=18
            )
            
            prep = self._parse_interview_prep(response.choices[0].message.content)
            logger.info("✅ Generated interview prep successfully")
            return prep
            
        except TimeoutException as e:
            logger.warning(f"⏱️  Interview prep timeout: {e}, using fallback")
            return self._fallback_interview_prep()
        except Exception as e:
            logger.warning(f"⚠️  Interview prep error ({type(e).__name__}): {e}, using fallback")
            return self._fallback_interview_prep()

    def generate_cover_letter(self, resume_data: Dict, jd_data: Dict, tone: str = "professional") -> Dict:
        """
        Generate a tailored cover letter for a specific job.
        """
        candidate_name = (resume_data.get("name") or "Candidate").strip() or "Candidate"

        if not self.client:
            return self._fallback_cover_letter(jd_data, candidate_name)

        try:
            prompt = self._build_cover_letter_prompt(resume_data, jd_data, tone)

            logger.info("🔄 Calling Groq API for cover letter (timeout: 20s, max_tokens: 1200)...")

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career writer. Create personalized, specific, ATS-aligned cover letters with concrete relevance to the job."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1200,
                timeout=20
            )

            letter_text = response.choices[0].message.content.strip()
            letter_text = self._ensure_cover_letter_signature(letter_text, candidate_name)
            return {
                "tone": tone,
                "cover_letter": letter_text,
                "key_alignment_points": self._extract_key_points(letter_text)[:8],
                "candidate_name": candidate_name,
                "generated_at": "AI-powered by Groq (Llama 3)"
            }

        except Exception as e:
            logger.warning(f"⚠️  Cover letter error ({type(e).__name__}): {e}, using fallback")
            return self._fallback_cover_letter(jd_data, candidate_name)

    def generate_tailored_resume(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """
        Generate one-click tailored resume content for a target JD.
        """
        if not self.client:
            return self._heuristic_tailored_resume(resume_data, jd_data)

        try:
            prompt = self._build_tailored_resume_prompt(resume_data, jd_data)

            logger.info("🔄 Calling Groq API for tailored resume (timeout: 22s, max_tokens: 1500)...")

            response = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an ATS and resume optimization expert. Rewrite resume sections to maximize role relevance while staying truthful."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=1500,
                timeout=22
            )

            tailored_text = response.choices[0].message.content.strip()
            output = {
                "tailored_resume": tailored_text,
                "keyword_alignment": self._extract_key_points(tailored_text)[:10],
                "generated_at": "AI-powered by Groq (Llama 3)",
                "generation_mode": "ai"
            }
            # Guardrail: if model returns too-short/generic output, use richer local generation.
            if len((tailored_text or "").strip()) < 500:
                return self._heuristic_tailored_resume(resume_data, jd_data)
            return output
        except Exception as e:
            logger.warning(f"⚠️  Tailored resume error ({type(e).__name__}): {e}, using fallback")
            return self._heuristic_tailored_resume(resume_data, jd_data)
    
    # ========== PROMPT BUILDERS ==========
    
    def _build_resume_improvement_prompt(self, resume_data: Dict, ats_score: Dict) -> str:
        """Build prompt for resume improvement"""
        
        skills = resume_data.get('skills', [])
        experience = resume_data.get('experience', [])
        education = resume_data.get('education', [])
        
        prompt = f"""Analyze this resume and provide deep, structured improvement analysis.

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

Return only valid JSON in this exact schema:
{{
  "overall_summary": "2-4 sentence summary",
  "priority_order": ["high", "medium", "low"],
  "suggestions": [
    {{
      "category": "Skills|Experience|Format|Content|Keywords|Projects|Achievements|Branding",
      "priority": "high|medium|low",
      "suggestion": "What to change",
      "why_it_matters": "Why this improves ATS/hiring outcomes",
      "action_steps": ["step 1", "step 2", "step 3"],
      "example_rewrite": "optional concrete rewrite example",
      "estimated_impact": "Expected impact in score/interview chances"
    }}
  ]
}}

Rules:
- Provide 7 to 10 suggestions.
- Each suggestion must include at least 3 action_steps.
- Keep language practical and role-focused.
- No markdown. JSON only."""

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

    def _build_cover_letter_prompt(self, resume_data: Dict, jd_data: Dict, tone: str) -> str:
        """Build prompt for cover letter generation."""
        name = resume_data.get("name", "Candidate")
        skills = resume_data.get("skills", [])
        experience = resume_data.get("experience", [])
        education = resume_data.get("education", [])
        jd_title = jd_data.get("title", "this role")
        company = jd_data.get("company", "your company")
        jd_description = jd_data.get("description", "")[:1200]

        prompt = f"""Write a detailed and role-specific cover letter.

Candidate Name: {name}
Target Role: {jd_title}
Company: {company}
Tone: {tone}
Top Skills: {', '.join(skills[:12]) if skills else 'Not specified'}
Experience Count: {len(experience)}
Education Count: {len(education)}

Job Description:
{jd_description}

Instructions:
- Keep it authentic and specific to this role.
- Include strong hook, role-fit paragraph, impact paragraph, and closing call-to-action.
- Mention 3-5 concrete alignment points between candidate background and role.
- Length: 320-450 words.
- Output plain text only."""
        return prompt

    def _build_tailored_resume_prompt(self, resume_data: Dict, jd_data: Dict) -> str:
        """Build prompt for one-click tailored resume output."""
        skills = resume_data.get("skills", [])
        raw_text = resume_data.get("raw_text", "")[:2200]
        jd_title = jd_data.get("title", "this role")
        company = jd_data.get("company", "this company")
        jd_description = jd_data.get("description", "")[:1500]
        jd_requirements = (jd_data.get("requirements") or "")[:800]

        prompt = f"""Create a one-click tailored resume draft for this candidate.

Target Role: {jd_title}
Company: {company}
Candidate Skills: {', '.join(skills[:15]) if skills else 'Not specified'}

Original Resume Excerpt:
{raw_text}

Job Description:
{jd_description}

Job Requirements:
{jd_requirements}

Output format (plain text):
1) TARGETED PROFESSIONAL SUMMARY (4-6 lines)
2) CORE SKILLS TO HIGHLIGHT (12-18 bullets)
3) REWRITTEN EXPERIENCE BULLETS (8-12 impact bullets with numbers where possible)
4) PROJECTS TO EMPHASIZE (3-5 bullets)
5) ATS KEYWORDS TO INCLUDE (15-25 keywords)
6) QUICK EDIT CHECKLIST (6-10 actionable edits)

Important:
- Do not fabricate facts.
- Reframe existing profile to match role language.
- Keep output practical and ready to paste into resume."""
        return prompt
    
    # ========== RESPONSE PARSERS ==========
    
    def _parse_ai_suggestions(self, response_text: str) -> List[Dict]:
        """Parse AI response into structured suggestions"""
        # First try strict JSON parsing
        parsed_json = None
        cleaned_text = response_text.strip()
        if cleaned_text.startswith("```"):
            cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()

        try:
            parsed_json = json.loads(cleaned_text)
        except json.JSONDecodeError:
            parsed_json = None

        if isinstance(parsed_json, dict) and isinstance(parsed_json.get("suggestions"), list):
            suggestions = []
            for item in parsed_json.get("suggestions", []):
                if not isinstance(item, dict):
                    continue
                suggestion_text = item.get("suggestion", "")
                if not suggestion_text:
                    continue
                suggestions.append({
                    "category": item.get("category", "General"),
                    "suggestion": suggestion_text,
                    "priority": item.get("priority", "medium"),
                    "why_it_matters": item.get("why_it_matters", ""),
                    "action_steps": item.get("action_steps", []),
                    "example_rewrite": item.get("example_rewrite", ""),
                    "estimated_impact": item.get("estimated_impact", "")
                })
            if suggestions:
                return suggestions[:10]

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
                    'priority': 'high' if len(suggestions) < 3 else 'medium',
                    'why_it_matters': '',
                    'action_steps': [],
                    'example_rewrite': '',
                    'estimated_impact': ''
                })
        
        # Fallback if parsing fails
        if not suggestions:
            suggestions = [
                {
                    'category': 'General',
                    'suggestion': response_text[:200],
                    'priority': 'medium',
                    'why_it_matters': '',
                    'action_steps': [],
                    'example_rewrite': '',
                    'estimated_impact': ''
                }
            ]
        
        return suggestions[:10]
    
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
                'priority': 'high',
                'why_it_matters': 'Higher ATS alignment improves shortlist probability.',
                'action_steps': [
                    'Add missing role-relevant keywords from target job descriptions.',
                    'Strengthen measurable achievements in recent experience.',
                    'Use clear section headings and consistent formatting.'
                ],
                'example_rewrite': '',
                'estimated_impact': 'High'
            })
        
        if len(resume_data.get('skills', [])) < 8:
            suggestions.append({
                'category': 'Skills',
                'suggestion': 'Add 3-5 more relevant technical skills to strengthen your profile',
                'priority': 'high',
                'why_it_matters': 'Skill coverage improves both ATS match and recruiter confidence.',
                'action_steps': [
                    'Map required skills from top 5 target roles.',
                    'Add only skills you can defend in interviews.',
                    'Group tools and frameworks by domain for readability.'
                ],
                'example_rewrite': '',
                'estimated_impact': 'High'
            })
        
        if not resume_data.get('linkedin'):
            suggestions.append({
                'category': 'Contact',
                'suggestion': 'Include your LinkedIn profile URL for better credibility',
                'priority': 'medium',
                'why_it_matters': 'Recruiters often verify consistency across resume and online profile.',
                'action_steps': [
                    'Add a custom LinkedIn URL in contact section.',
                    'Ensure headline reflects your target role.',
                    'Align summary and achievements with resume.'
                ],
                'example_rewrite': '',
                'estimated_impact': 'Medium'
            })
        
        suggestions.append({
            'category': 'Content',
            'suggestion': 'Use action verbs (developed, led, improved) to describe your experience',
            'priority': 'medium',
            'why_it_matters': 'Action-oriented language highlights ownership and results.',
            'action_steps': [
                'Start bullets with strong action verbs.',
                'Attach outcomes with metrics where possible.',
                'Remove passive or generic phrasing.'
            ],
            'example_rewrite': '',
            'estimated_impact': 'Medium'
        })
        
        suggestions.append({
            'category': 'Format',
            'suggestion': 'Ensure consistent formatting and clear section headers',
            'priority': 'low',
            'why_it_matters': 'Cleaner formatting improves readability and ATS parsing quality.',
            'action_steps': [
                'Keep date format consistent throughout.',
                'Use standard section names like Experience and Skills.',
                'Maintain one font family and predictable spacing.'
            ],
            'example_rewrite': '',
            'estimated_impact': 'Low'
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

    def _fallback_cover_letter(self, jd_data: Dict, candidate_name: str = "Candidate") -> Dict:
        """Fallback cover letter when API is unavailable."""
        title = jd_data.get("title", "the role")
        company = jd_data.get("company", "your company")
        letter = (
            f"Dear Hiring Manager,\n\n"
            f"I am excited to apply for {title} at {company}. My background includes relevant technical "
            "skills, project execution, and continuous learning aligned with this opportunity.\n\n"
            "In my recent work, I have focused on delivering measurable outcomes, collaborating with teams, "
            "and improving systems with a practical, user-focused mindset. I am confident I can contribute "
            "meaningfully to your team's goals.\n\n"
            "I would welcome the opportunity to discuss how my profile aligns with your requirements. "
            "Thank you for your time and consideration.\n\n"
            "Sincerely,\n"
            f"{candidate_name}"
        )
        return {
            "tone": "professional",
            "cover_letter": letter,
            "key_alignment_points": [
                "Role-focused motivation",
                "Relevant technical capability",
                "Impact-oriented mindset",
                "Strong collaboration and execution"
            ],
            "candidate_name": candidate_name,
            "generated_at": "Default letter (API unavailable)"
        }

    def _ensure_cover_letter_signature(self, letter_text: str, candidate_name: str) -> str:
        """
        Ensure cover letter ends with a proper signature containing candidate name.
        """
        text = (letter_text or "").strip()
        name = (candidate_name or "Candidate").strip() or "Candidate"

        # If candidate name already appears in the last lines, keep as is.
        tail = "\n".join(text.splitlines()[-6:]).lower()
        if name.lower() in tail:
            return text

        # If letter ends with "Sincerely" or "Sincerely,", append name on next line.
        if re.search(r"sincerely,?\s*$", text, flags=re.IGNORECASE):
            return text + "\n" + name

        # Otherwise add a full closing block.
        return text + "\n\nSincerely,\n" + name

    def _fallback_tailored_resume(self, jd_data: Dict) -> Dict:
        """Fallback tailored resume guidance when API is unavailable."""
        title = jd_data.get("title", "target role")
        content = (
            f"TARGETED PROFESSIONAL SUMMARY\n"
            f"- Tailor your summary specifically for {title} and align it with the top requirements.\n\n"
            f"CORE SKILLS TO HIGHLIGHT\n"
            f"- Add role-relevant tools, frameworks, and domain keywords from the JD.\n\n"
            f"REWRITTEN EXPERIENCE BULLETS\n"
            f"- Use action verbs and measurable outcomes (%, time saved, revenue impact).\n\n"
            f"PROJECTS TO EMPHASIZE\n"
            f"- Bring role-matching projects to top and describe business impact.\n\n"
            f"ATS KEYWORDS TO INCLUDE\n"
            f"- Mirror exact wording from the JD in a truthful way.\n\n"
            f"QUICK EDIT CHECKLIST\n"
            f"- Keep formatting consistent.\n"
            f"- Prioritize recent and relevant achievements.\n"
            f"- Remove generic statements."
        )
        return {
            "tailored_resume": content,
            "keyword_alignment": [
                "Match job title phrasing",
                "Align skills with JD terms",
                "Quantify impact in experience bullets",
                "Prioritize relevant projects"
            ],
            "generated_at": "Default tailored guidance (API unavailable)",
            "generation_mode": "fallback"
        }

    def _heuristic_tailored_resume(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """
        Rich local generator for tailored resume when LLM is unavailable/weak.
        Uses resume structure + JD keywords to produce practical, non-generic output.
        """
        title = jd_data.get("title", "Target Role")
        company = jd_data.get("company", "Target Company")
        skills = resume_data.get("skills", []) or []
        experience = resume_data.get("experience", []) or []
        education = resume_data.get("education", []) or []

        jd_keywords = self._extract_jd_keywords(jd_data, limit=24)
        matched_keywords = [kw for kw in jd_keywords if kw.lower() in {s.lower() for s in skills}]
        missing_keywords = [kw for kw in jd_keywords if kw.lower() not in {s.lower() for s in skills}]

        summary_lines = [
            f"Results-driven candidate targeting {title} at {company}.",
            f"Brings {len(skills)} identified technical/functional skills with focus on role-aligned delivery.",
            "Strong emphasis on measurable impact, ownership, and collaboration across cross-functional teams.",
            "Ready to contribute quickly by aligning prior experience with the role's core priorities."
        ]

        skill_lines = []
        prioritized_skills = matched_keywords[:12] + [s for s in skills if s not in matched_keywords][:8]
        for s in prioritized_skills[:18]:
            skill_lines.append(f"- {s}")

        rewritten_bullets = self._build_experience_bullets(experience, title, jd_keywords)
        project_lines = self._build_project_emphasis(resume_data, jd_keywords)
        keyword_lines = [f"- {k}" for k in jd_keywords[:25]]

        checklist = [
            "- Move the strongest role-relevant project/experience to top third of resume.",
            "- Replace generic duties with outcome bullets (%, time saved, quality, revenue, scale).",
            "- Mirror JD terminology in skills and experience while staying truthful.",
            "- Ensure every major requirement has evidence in at least one bullet.",
            "- Keep summary targeted to this exact role and company context.",
            "- Keep resume to clean ATS-friendly formatting (simple headings, consistent dates).",
            "- Add 5-10 missing JD keywords where genuinely applicable."
        ]
        if missing_keywords:
            checklist.append(f"- Consider adding evidence for missing keywords: {', '.join(missing_keywords[:8])}.")

        content = (
            "TARGETED PROFESSIONAL SUMMARY\n"
            + "\n".join(summary_lines)
            + "\n\nCORE SKILLS TO HIGHLIGHT\n"
            + ("\n".join(skill_lines) if skill_lines else "- Add role-relevant skills from your background.")
            + "\n\nREWRITTEN EXPERIENCE BULLETS\n"
            + ("\n".join(rewritten_bullets) if rewritten_bullets else "- Add impact-focused bullets with numbers and outcomes.")
            + "\n\nPROJECTS TO EMPHASIZE\n"
            + ("\n".join(project_lines) if project_lines else "- Highlight role-aligned projects with measurable impact.")
            + "\n\nATS KEYWORDS TO INCLUDE\n"
            + ("\n".join(keyword_lines) if keyword_lines else "- Extract 15-25 keywords directly from target JD.")
            + "\n\nQUICK EDIT CHECKLIST\n"
            + "\n".join(checklist)
        )

        keyword_alignment = []
        if matched_keywords:
            keyword_alignment.append(f"Already aligned keywords: {', '.join(matched_keywords[:10])}")
        if missing_keywords:
            keyword_alignment.append(f"Potentially missing keywords: {', '.join(missing_keywords[:10])}")
        keyword_alignment.extend([
            "Match job title phrasing in summary and headline.",
            "Quantify impact in rewritten experience bullets.",
            "Prioritize most relevant projects near top."
        ])

        return {
            "tailored_resume": content,
            "keyword_alignment": keyword_alignment[:12],
            "generated_at": "Heuristic tailored output (local generation)",
            "generation_mode": "heuristic"
        }

    def _extract_jd_keywords(self, jd_data: Dict, limit: int = 24) -> List[str]:
        """Extract likely ATS keywords from JD text with light normalization."""
        text = " ".join([
            str(jd_data.get("title", "")),
            str(jd_data.get("description", "")),
            str(jd_data.get("requirements", "")),
        ]).lower()

        # Keep important symbols for tech words like c++, c#, node.js
        raw_tokens = re.findall(r"[a-z0-9\+\#\.\-]{2,}", text)
        stop = {
            "and", "the", "for", "with", "that", "this", "you", "your", "will", "are", "our",
            "have", "has", "from", "into", "able", "using", "use", "plus", "year", "years",
            "role", "team", "work", "required", "preferred", "experience", "including", "about"
        }
        freq = {}
        for t in raw_tokens:
            if t in stop or t.isdigit() or len(t) < 3:
                continue
            freq[t] = freq.get(t, 0) + 1

        # Prefer known technical terms if present
        priority_terms = [
            "python", "java", "javascript", "react", "node.js", "node", "sql", "aws", "azure",
            "docker", "kubernetes", "mongodb", "postgresql", "mysql", "typescript", "flask",
            "django", "api", "rest", "microservices", "ci/cd", "git", "linux", "agile", "scrum",
            "machine", "learning", "data", "analytics", "devops", "system", "design"
        ]
        keywords = []
        for p in priority_terms:
            if p in text:
                keywords.append(p)

        remaining = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        for token, _ in remaining:
            if token not in keywords:
                keywords.append(token)
            if len(keywords) >= limit:
                break
        return keywords[:limit]

    def _build_experience_bullets(self, experience: List, title: str, jd_keywords: List[str]) -> List[str]:
        """Create rewritten bullet suggestions from parsed experience content."""
        bullets = []
        focus = ", ".join(jd_keywords[:5]) if jd_keywords else title
        for item in experience[:6]:
            if isinstance(item, dict):
                role = item.get("position") or item.get("title") or "Role"
                company = item.get("company") or "Organization"
                desc = item.get("description") or item.get("details") or ""
                desc = re.sub(r"\s+", " ", str(desc)).strip()
                if len(desc) > 140:
                    desc = desc[:140].rsplit(" ", 1)[0] + "..."
                bullets.append(f"- As {role} at {company}, delivered outcomes aligned to {focus}; optimized workflows and improved execution quality.")
                if desc:
                    bullets.append(f"- Reframe prior work: {desc}")
            else:
                txt = re.sub(r"\s+", " ", str(item)).strip()
                if txt:
                    bullets.append(f"- Reframe experience to emphasize {focus}: {txt[:130]}")
            if len(bullets) >= 12:
                break
        return bullets[:12]

    def _build_project_emphasis(self, resume_data: Dict, jd_keywords: List[str]) -> List[str]:
        """Project emphasis suggestions based on available resume text."""
        lines = []
        raw_text = str(resume_data.get("raw_text", ""))[:1600].lower()
        project_hint = "projects" in raw_text
        focus = ", ".join(jd_keywords[:4]) if jd_keywords else "target role skills"
        if project_hint:
            lines.append(f"- Move project bullets demonstrating {focus} to the top of the Projects section.")
            lines.append("- Add measurable outputs per project (latency reduction, throughput, adoption, accuracy, etc.).")
            lines.append("- Mention tools/stack explicitly in each bullet for ATS matching.")
        else:
            lines.append(f"- Add 2-3 concise projects aligned with {focus}.")
            lines.append("- For each project, use Problem -> Action -> Result format.")
            lines.append("- Quantify impact and include relevant technologies in each bullet.")
        return lines


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
