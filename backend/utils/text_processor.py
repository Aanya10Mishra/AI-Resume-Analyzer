"""
Text Processor
High-level interface for text processing and similarity calculations
Enhanced with detailed matching and skill gap analysis
"""
from typing import List, Dict, Optional, Tuple
from .embedding_matcher import EmbeddingMatcher
import logging
import re

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Enhanced Text processing with embeddings
    Provides clean interface to embedding functionality with advanced matching
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize with embedding model
        
        Args:
            model_name: Sentence transformer model name
        """
        logger.info("🚀 Initializing TextProcessor with Sentence Transformers...")
        self.embedding_matcher = EmbeddingMatcher(model_name)
        
        # Scoring weights for match calculation
        self.scoring_weights = {
            'semantic': 0.40,      # 40% - Overall meaning similarity
            'skills': 0.35,        # 35% - Technical skills match
            'experience': 0.15,    # 15% - Experience level match
            'keywords': 0.10       # 10% - Keyword density match
        }
        
        # Skills database organized by category with importance weights
        self.skills_database = {
            'programming': {
                'weight': 1.5,
                'skills': [
                    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c',
                    'go', 'golang', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala',
                    'r', 'matlab', 'perl', 'shell', 'bash', 'powershell', 'lua',
                    'objective-c', 'dart', 'elixir', 'clojure', 'haskell', 'julia'
                ]
            },
            'web_frameworks': {
                'weight': 1.3,
                'skills': [
                    'react', 'reactjs', 'angular', 'vue', 'vuejs', 'svelte', 'nextjs',
                    'next.js', 'nuxt', 'nuxtjs', 'gatsby', 'remix', 'django', 'flask',
                    'fastapi', 'spring', 'spring boot', 'express', 'expressjs', 'nestjs',
                    'rails', 'ruby on rails', 'laravel', 'symfony', 'asp.net', '.net',
                    'node.js', 'nodejs', 'deno', 'jquery', 'bootstrap', 'tailwind',
                    'tailwindcss', 'material ui', 'chakra ui', 'ant design'
                ]
            },
            'data_science': {
                'weight': 1.4,
                'skills': [
                    'machine learning', 'deep learning', 'artificial intelligence', 'ai',
                    'ml', 'neural networks', 'nlp', 'natural language processing',
                    'computer vision', 'tensorflow', 'pytorch', 'keras', 'scikit-learn',
                    'sklearn', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn',
                    'plotly', 'tableau', 'power bi', 'data analysis', 'data science',
                    'data mining', 'data visualization', 'statistics', 'statistical analysis',
                    'regression', 'classification', 'clustering', 'opencv', 'huggingface',
                    'transformers', 'bert', 'gpt', 'llm', 'large language models',
                    'rag', 'langchain', 'vector database', 'embeddings'
                ]
            },
            'databases': {
                'weight': 1.2,
                'skills': [
                    'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis',
                    'elasticsearch', 'cassandra', 'dynamodb', 'oracle', 'sqlite',
                    'mariadb', 'neo4j', 'graphql', 'firebase', 'supabase', 'prisma',
                    'sequelize', 'typeorm', 'mongoose', 'sqlalchemy', 'nosql',
                    'database design', 'data modeling', 'etl', 'data warehouse',
                    'snowflake', 'bigquery', 'redshift', 'apache spark', 'hadoop',
                    'hive', 'kafka', 'rabbitmq', 'apache airflow', 'dbt'
                ]
            },
            'cloud_devops': {
                'weight': 1.3,
                'skills': [
                    'aws', 'amazon web services', 'azure', 'microsoft azure', 'gcp',
                    'google cloud', 'google cloud platform', 'docker', 'kubernetes',
                    'k8s', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'cicd',
                    'github actions', 'gitlab ci', 'circleci', 'travis ci', 'devops',
                    'linux', 'unix', 'nginx', 'apache', 'heroku', 'vercel', 'netlify',
                    'digitalocean', 'cloudflare', 'serverless', 'lambda', 'microservices',
                    'api gateway', 'load balancing', 'containerization', 'orchestration',
                    'monitoring', 'prometheus', 'grafana', 'datadog', 'new relic',
                    'elk stack', 'logstash', 'kibana', 'helm', 'argocd', 'istio'
                ]
            },
            'mobile': {
                'weight': 1.2,
                'skills': [
                    'android', 'ios', 'react native', 'flutter', 'swift', 'kotlin',
                    'objective-c', 'xamarin', 'ionic', 'cordova', 'mobile development',
                    'app development', 'swiftui', 'jetpack compose', 'expo'
                ]
            },
            'tools': {
                'weight': 1.0,
                'skills': [
                    'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence',
                    'slack', 'trello', 'asana', 'notion', 'vscode', 'visual studio',
                    'intellij', 'pycharm', 'eclipse', 'postman', 'insomnia', 'swagger',
                    'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
                    'webpack', 'vite', 'babel', 'eslint', 'prettier', 'npm', 'yarn',
                    'pip', 'conda', 'poetry', 'maven', 'gradle', 'make', 'cmake'
                ]
            },
            'soft_skills': {
                'weight': 0.8,
                'skills': [
                    'communication', 'leadership', 'teamwork', 'team player',
                    'problem solving', 'problem-solving', 'critical thinking',
                    'time management', 'adaptability', 'creativity', 'innovation',
                    'collaboration', 'project management', 'analytical', 'analysis',
                    'attention to detail', 'detail oriented', 'detail-oriented',
                    'self motivated', 'self-motivated', 'proactive', 'initiative',
                    'presentation', 'public speaking', 'negotiation', 'conflict resolution',
                    'mentoring', 'coaching', 'strategic thinking', 'decision making'
                ]
            },
            'methodologies': {
                'weight': 0.9,
                'skills': [
                    'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma',
                    'tdd', 'test driven development', 'bdd', 'behavior driven development',
                    'pair programming', 'code review', 'continuous integration',
                    'continuous deployment', 'design patterns', 'solid principles',
                    'clean code', 'clean architecture', 'microservices architecture',
                    'domain driven design', 'ddd', 'event driven', 'rest', 'restful',
                    'api design', 'system design', 'software architecture'
                ]
            },
            'security': {
                'weight': 1.2,
                'skills': [
                    'cybersecurity', 'security', 'penetration testing', 'ethical hacking',
                    'owasp', 'encryption', 'ssl', 'tls', 'oauth', 'jwt', 'authentication',
                    'authorization', 'identity management', 'sso', 'single sign on',
                    'vulnerability assessment', 'security audit', 'compliance',
                    'gdpr', 'hipaa', 'soc2', 'iso 27001'
                ]
            }
        }
        
        # Common stop words for keyword analysis
        self.stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'will',
            'with', 'this', 'that', 'from', 'they', 'would', 'there', 'their',
            'what', 'about', 'which', 'when', 'make', 'like', 'time', 'just',
            'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some',
            'could', 'them', 'than', 'then', 'now', 'look', 'only', 'come',
            'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two',
            'how', 'work', 'first', 'well', 'way', 'even', 'new', 'want',
            'because', 'any', 'these', 'give', 'day', 'most', 'must', 'should',
            'being', 'such', 'through', 'during', 'each', 'before', 'between',
            'under', 'again', 'further', 'once', 'here', 'where', 'why', 'while',
            'both', 'same', 'other', 'more', 'very', 'able', 'using', 'used'
        }
        
        logger.info("✅ TextProcessor ready with enhanced matching!")
    
    # ==================== CORE METHODS ====================
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-100)
        """
        return self.embedding_matcher.calculate_similarity(text1, text2)
    
    def get_embedding(self, text: str):
        """
        Get embedding vector for text
        
        Args:
            text: Input text
            
        Returns:
            Numpy array embedding
        """
        return self.embedding_matcher.get_embedding(text)
    
    def get_stats(self) -> Dict:
        """Get processing statistics"""
        return self.embedding_matcher.get_cache_stats()
    
    # ==================== SKILL EXTRACTION ====================
    
    def extract_skills(self, text: str) -> List[str]:
        """
        Extract all skills from text
        
        Args:
            text: Input text
            
        Returns:
            List of found skills
        """
        text_lower = text.lower()
        found_skills = []
        
        for category_data in self.skills_database.values():
            for skill in category_data['skills']:
                # Use word boundary matching for accuracy
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    # Capitalize properly
                    found_skills.append(skill.title())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        return unique_skills
    
    def extract_skills_by_category(self, text: str) -> Dict[str, List[str]]:
        """
        Extract skills organized by category
        
        Args:
            text: Input text
            
        Returns:
            Dictionary of skills by category
        """
        text_lower = text.lower()
        categorized_skills = {}
        
        for category, category_data in self.skills_database.items():
            found = []
            for skill in category_data['skills']:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text_lower):
                    found.append(skill.title())
            
            if found:
                categorized_skills[category] = list(set(found))
        
        return categorized_skills
    
    def get_skill_category(self, skill: str) -> Optional[str]:
        """
        Get the category of a skill
        
        Args:
            skill: Skill name
            
        Returns:
            Category name or None
        """
        skill_lower = skill.lower()
        for category, category_data in self.skills_database.items():
            if skill_lower in category_data['skills']:
                return category
        return None
    
    def get_skill_weight(self, skill: str) -> float:
        """
        Get importance weight for a skill
        
        Args:
            skill: Skill name
            
        Returns:
            Weight value (default 1.0)
        """
        category = self.get_skill_category(skill)
        if category:
            return self.skills_database[category]['weight']
        return 1.0
    
    # ==================== EXPERIENCE EXTRACTION ====================
    
    def extract_experience_years(self, text: str) -> int:
        """
        Extract years of experience from text
        
        Args:
            text: Input text
            
        Returns:
            Years of experience (0 if not found)
        """
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
            r'experience\s*[:\-]?\s*(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|working|professional)',
            r'minimum\s+(?:of\s+)?(\d+)\s*(?:years?|yrs?)',
            r'at\s+least\s+(\d+)\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:in|with)',
            r'over\s+(\d+)\s*(?:years?|yrs?)'
        ]
        
        max_years = 0
        text_lower = text.lower()
        
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years = int(match)
                    if years <= 50:  # Sanity check
                        max_years = max(max_years, years)
                except ValueError:
                    continue
        
        return max_years
    
    def extract_education_level(self, text: str) -> Dict:
        """
        Extract education level from text
        
        Args:
            text: Input text
            
        Returns:
            Education information
        """
        text_lower = text.lower()
        
        education_levels = {
            'phd': ['phd', 'ph.d', 'doctorate', 'doctoral'],
            'masters': ['master', 'masters', 'mba', 'm.s.', 'm.sc', 'mtech', 'm.tech'],
            'bachelors': ['bachelor', 'bachelors', 'b.s.', 'b.sc', 'btech', 'b.tech', 'b.e.', 'undergraduate'],
            'associate': ['associate', 'diploma', 'a.s.', 'a.a.'],
            'high_school': ['high school', 'secondary', 'hsc', '12th']
        }
        
        found_levels = []
        for level, keywords in education_levels.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_levels.append(level)
                    break
        
        # Return highest education level
        level_order = ['phd', 'masters', 'bachelors', 'associate', 'high_school']
        highest = None
        for level in level_order:
            if level in found_levels:
                highest = level
                break
        
        return {
            'highest_level': highest,
            'all_levels': list(set(found_levels))
        }
    
    # ==================== KEYWORD ANALYSIS ====================
    
    def extract_keywords(self, text: str, min_length: int = 3) -> List[str]:
        """
        Extract meaningful keywords from text
        
        Args:
            text: Input text
            min_length: Minimum keyword length
            
        Returns:
            List of keywords
        """
        # Extract words
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + r',}\b', text.lower())
        
        # Remove stop words
        keywords = [w for w in words if w not in self.stop_words]
        
        return list(set(keywords))
    
    def calculate_keyword_overlap(self, text1: str, text2: str) -> Dict:
        """
        Calculate keyword overlap between two texts
        
        Args:
            text1: First text (e.g., resume)
            text2: Second text (e.g., job description)
            
        Returns:
            Keyword analysis results
        """
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        common = keywords1 & keywords2
        only_in_text1 = keywords1 - keywords2
        only_in_text2 = keywords2 - keywords1
        
        overlap_percentage = 0
        if len(keywords2) > 0:
            overlap_percentage = (len(common) / len(keywords2)) * 100
        
        return {
            'common_keywords': list(common),
            'unique_to_resume': list(only_in_text1),
            'missing_from_resume': list(only_in_text2),
            'overlap_percentage': round(min(overlap_percentage, 100), 2),
            'total_jd_keywords': len(keywords2),
            'matched_count': len(common)
        }
    
    # ==================== SKILL SIMILARITY ====================
    
    def calculate_skill_similarity(
        self, 
        resume_skills: List[str], 
        jd_skills: List[str]
    ) -> Dict:
        """
        Advanced skill matching with semantic similarity for unmatched skills
        
        Args:
            resume_skills: Skills from resume
            jd_skills: Required skills from JD
            
        Returns:
            Comprehensive skill analysis
        """
        # Normalize skills
        resume_skills_lower = [s.lower().strip() for s in resume_skills]
        jd_skills_lower = [s.lower().strip() for s in jd_skills]
        
        # Exact matches
        matched_skills = []
        unmatched_jd_skills = []
        
        for skill in jd_skills:
            skill_lower = skill.lower().strip()
            if skill_lower in resume_skills_lower:
                matched_skills.append(skill)
            else:
                # Check for similar skills using embeddings
                similar_found = False
                for resume_skill in resume_skills:
                    similarity = self.embedding_matcher.calculate_similarity(
                        skill_lower, 
                        resume_skill.lower()
                    )
                    if similarity > 80:  # High similarity threshold
                        matched_skills.append(f"{skill} (matched with {resume_skill})")
                        similar_found = True
                        break
                
                if not similar_found:
                    unmatched_jd_skills.append(skill)
        
        # Extra skills in resume
        extra_resume_skills = [
            s for s in resume_skills 
            if s.lower().strip() not in jd_skills_lower
        ]
        
        # Calculate weighted match score
        if len(jd_skills) > 0:
            total_weight = 0
            matched_weight = 0
            
            for skill in jd_skills:
                weight = self.get_skill_weight(skill)
                total_weight += weight
                if skill in matched_skills or any(skill in m for m in matched_skills):
                    matched_weight += weight
            
            weighted_percentage = (matched_weight / total_weight) * 100 if total_weight > 0 else 0
            simple_percentage = (len(matched_skills) / len(jd_skills)) * 100
        else:
            weighted_percentage = 100
            simple_percentage = 100
        
        # Categorize missing skills
        missing_by_category = {}
        for skill in unmatched_jd_skills:
            category = self.get_skill_category(skill) or 'other'
            if category not in missing_by_category:
                missing_by_category[category] = []
            missing_by_category[category].append(skill)
        
        return {
            'matched_skills': matched_skills,
            'unmatched_jd_skills': unmatched_jd_skills,
            'extra_resume_skills': extra_resume_skills,
            'missing_by_category': missing_by_category,
            'total_jd_skills': len(jd_skills),
            'total_resume_skills': len(resume_skills),
            'matched_count': len(matched_skills),
            'skill_match_percentage': round(simple_percentage, 2),
            'weighted_skill_percentage': round(weighted_percentage, 2)
        }
    
    # ==================== EXPERIENCE MATCHING ====================
    
    def calculate_experience_match(self, resume_text: str, jd_text: str) -> Dict:
        """
        Calculate experience level match
        
        Args:
            resume_text: Resume text
            jd_text: Job description text
            
        Returns:
            Experience match analysis
        """
        resume_years = self.extract_experience_years(resume_text)
        required_years = self.extract_experience_years(jd_text)
        
        if required_years == 0:
            return {
                'resume_years': resume_years,
                'required_years': 0,
                'match_percentage': 100,
                'status': 'No specific experience requirement',
                'meets_requirement': True
            }
        
        if resume_years >= required_years:
            match_pct = 100
            status = 'Meets or exceeds requirement'
            meets = True
        elif resume_years >= required_years * 0.75:
            # Close enough - 75% of required
            match_pct = 85
            status = f'Slightly below requirement ({required_years - resume_years} years gap)'
            meets = False
        elif resume_years >= required_years * 0.5:
            match_pct = 70
            status = f'Below requirement ({required_years - resume_years} years gap)'
            meets = False
        else:
            match_pct = (resume_years / required_years) * 100
            status = f'Significant experience gap ({required_years - resume_years} years needed)'
            meets = False
        
        return {
            'resume_years': resume_years,
            'required_years': required_years,
            'match_percentage': round(match_pct, 2),
            'status': status,
            'meets_requirement': meets,
            'years_gap': max(0, required_years - resume_years)
        }
    
    # ==================== SECTION ANALYSIS ====================
    
    def calculate_section_scores(self, resume_text: str, jd_text: str) -> Dict:
        """
        Calculate match scores for different resume sections
        
        Args:
            resume_text: Full resume text
            jd_text: Job description text
            
        Returns:
            Section-wise scores
        """
        sections = self._extract_resume_sections(resume_text)
        section_scores = {}
        
        for section_name, section_text in sections.items():
            if section_text and len(section_text.strip()) > 20:
                try:
                    score = self.embedding_matcher.calculate_similarity(
                        section_text, 
                        jd_text
                    )
                    section_scores[section_name] = round(score, 2)
                except Exception as e:
                    logger.warning(f"Error calculating section score for {section_name}: {e}")
                    section_scores[section_name] = 0
            else:
                section_scores[section_name] = 0
        
        return section_scores
    
    def _extract_resume_sections(self, text: str) -> Dict[str, str]:
        """
        Extract different sections from resume text
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary of sections
        """
        sections = {
            'skills': '',
            'experience': '',
            'education': '',
            'projects': '',
            'summary': '',
            'certifications': ''
        }
        
        section_keywords = {
            'skills': ['skills', 'technical skills', 'technologies', 'tools', 'competencies'],
            'experience': ['experience', 'work experience', 'employment', 'professional experience', 'work history'],
            'education': ['education', 'academic', 'qualifications', 'degrees'],
            'projects': ['projects', 'portfolio', 'personal projects', 'academic projects'],
            'summary': ['summary', 'objective', 'profile', 'about me', 'professional summary'],
            'certifications': ['certifications', 'certificates', 'licenses', 'credentials']
        }
        
        text_lower = text.lower()
        
        for section, keywords in section_keywords.items():
            for keyword in keywords:
                # Look for section headers
                pattern = rf'(?:^|\n)\s*{keyword}[:\s]*\n(.*?)(?=\n\s*[A-Z][a-z]+[:\s]*\n|\Z)'
                match = re.search(pattern, text_lower, re.DOTALL | re.IGNORECASE)
                if match:
                    sections[section] = match.group(1).strip()
                    break
        
        return sections
    
    # ==================== DETAILED MATCH CALCULATION ====================
    
    def calculate_detailed_match(
        self, 
        resume_text: str, 
        jd_text: str
    ) -> Dict:
        """
        Calculate comprehensive match score with detailed breakdown
        
        Weights:
        - Semantic Similarity: 40%
        - Skill Match: 35%
        - Experience Match: 15%
        - Keyword Density: 10%
        
        Args:
            resume_text: Full resume text
            jd_text: Job description text
            
        Returns:
            Comprehensive match analysis
        """
        logger.info("📊 Calculating detailed match score...")
        
        try:
            # 1. Semantic Similarity (40%)
            semantic_score = self.embedding_matcher.calculate_similarity(
                resume_text, 
                jd_text
            )
            logger.info(f"   ├── Semantic Similarity: {semantic_score:.2f}%")
            
            # 2. Skill Match (35%)
            resume_skills = self.extract_skills(resume_text)
            jd_skills = self.extract_skills(jd_text)
            
            skill_analysis = self.calculate_skill_similarity(resume_skills, jd_skills)
            skill_score = skill_analysis['weighted_skill_percentage']
            logger.info(f"   ├── Skill Match: {skill_score:.2f}% ({skill_analysis['matched_count']}/{skill_analysis['total_jd_skills']} skills)")
            
            # 3. Experience Match (15%)
            experience_analysis = self.calculate_experience_match(resume_text, jd_text)
            experience_score = experience_analysis['match_percentage']
            logger.info(f"   ├── Experience Match: {experience_score:.2f}%")
            
            # 4. Keyword Match (10%)
            keyword_analysis = self.calculate_keyword_overlap(resume_text, jd_text)
            keyword_score = keyword_analysis['overlap_percentage']
            logger.info(f"   ├── Keyword Match: {keyword_score:.2f}%")
            
            # 5. Section Scores
            section_scores = self.calculate_section_scores(resume_text, jd_text)
            
            # Calculate weighted overall score
            overall_match = (
                (semantic_score * self.scoring_weights['semantic']) +
                (skill_score * self.scoring_weights['skills']) +
                (experience_score * self.scoring_weights['experience']) +
                (keyword_score * self.scoring_weights['keywords'])
            )
            
            logger.info(f"   └── 📈 Overall Match: {overall_match:.2f}%")
            
            return {
                'overall_match': round(overall_match, 2),
                
                # Individual scores
                'semantic_similarity': round(semantic_score, 2),
                'skill_match': round(skill_score, 2),
                'experience_match': round(experience_score, 2),
                'keyword_match': round(keyword_score, 2),
                
                # Section scores
                'section_scores': section_scores,
                
                # Detailed analyses
                'skill_analysis': skill_analysis,
                'experience_analysis': experience_analysis,
                'keyword_analysis': keyword_analysis,
                
                # Weights used
                'weights': {
                    'semantic': f"{int(self.scoring_weights['semantic'] * 100)}%",
                    'skills': f"{int(self.scoring_weights['skills'] * 100)}%",
                    'experience': f"{int(self.scoring_weights['experience'] * 100)}%",
                    'keywords': f"{int(self.scoring_weights['keywords'] * 100)}%"
                },
                
                # Quick stats
                'resume_skills_count': len(resume_skills),
                'jd_skills_count': len(jd_skills),
                'matched_skills_count': skill_analysis['matched_count']
            }
            
        except Exception as e:
            logger.error(f"Error in detailed match calculation: {e}")
            # Fallback to basic semantic matching
            basic_score = self.embedding_matcher.calculate_similarity(resume_text, jd_text)
            return {
                'overall_match': round(basic_score, 2),
                'semantic_similarity': round(basic_score, 2),
                'skill_match': 0,
                'experience_match': 0,
                'keyword_match': 0,
                'section_scores': {},
                'error': str(e)
            }
    
    # ==================== IMPROVEMENT SUGGESTIONS ====================
    
    def get_improvement_suggestions(
        self, 
        resume_text: str, 
        jd_text: str,
        match_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Generate actionable suggestions to improve resume match
        
        Args:
            resume_text: Resume text
            jd_text: Job description text
            match_data: Optional pre-calculated match data
            
        Returns:
            List of improvement suggestions
        """
        if match_data is None:
            match_data = self.calculate_detailed_match(resume_text, jd_text)
        
        suggestions = []
        
        # Skill gap suggestions
        skill_analysis = match_data.get('skill_analysis', {})
        missing_skills = skill_analysis.get('unmatched_jd_skills', [])
        
        if missing_skills:
            # Group by category
            missing_by_category = skill_analysis.get('missing_by_category', {})
            
            for category, skills in missing_by_category.items():
                if skills:
                    priority = 'high' if category in ['programming', 'data_science', 'cloud_devops'] else 'medium'
                    suggestions.append({
                        'category': f'Missing {category.replace("_", " ").title()} Skills',
                        'priority': priority,
                        'skills': skills[:5],  # Top 5
                        'suggestion': f"Add these {category.replace('_', ' ')} skills if you have experience with them: {', '.join(skills[:5])}",
                        'impact': '+10-15% match score'
                    })
        
        # Experience suggestions
        experience_analysis = match_data.get('experience_analysis', {})
        if not experience_analysis.get('meets_requirement', True):
            years_gap = experience_analysis.get('years_gap', 0)
            suggestions.append({
                'category': 'Experience Gap',
                'priority': 'medium',
                'suggestion': f"You're {years_gap} years below the requirement. Highlight projects, internships, or freelance work to compensate.",
                'impact': 'May affect initial screening'
            })
        
        # Keyword suggestions
        keyword_score = match_data.get('keyword_match', 0)
        if keyword_score < 70:
            keyword_analysis = match_data.get('keyword_analysis', {})
            missing_keywords = keyword_analysis.get('missing_from_resume', [])[:10]
            suggestions.append({
                'category': 'Keyword Optimization',
                'priority': 'medium',
                'suggestion': f"Include more keywords from the job description. Consider adding: {', '.join(missing_keywords[:5])}",
                'impact': '+5-10% ATS score'
            })
        
        # Semantic similarity suggestions
        semantic_score = match_data.get('semantic_similarity', 0)
        if semantic_score < 60:
            suggestions.append({
                'category': 'Content Alignment',
                'priority': 'high',
                'suggestion': "Tailor your resume language and descriptions to match the job posting more closely. Use similar terminology and phrasing.",
                'impact': '+10-20% match score'
            })
        
        # Section-based suggestions
        section_scores = match_data.get('section_scores', {})
        
        if section_scores.get('skills', 0) < 50:
            suggestions.append({
                'category': 'Skills Section',
                'priority': 'high',
                'suggestion': "Expand your skills section to include more relevant technologies mentioned in the job description.",
                'impact': '+5-10% match score'
            })
        
        if section_scores.get('experience', 0) < 50:
            suggestions.append({
                'category': 'Experience Section',
                'priority': 'medium',
                'suggestion': "Rewrite your experience bullet points to highlight achievements relevant to this role.",
                'impact': '+5-10% match score'
            })
        
        if section_scores.get('projects', 0) < 30:
            suggestions.append({
                'category': 'Projects Section',
                'priority': 'low',
                'suggestion': "Add or enhance project descriptions that demonstrate skills required for this position.",
                'impact': '+3-5% match score'
            })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        suggestions.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return suggestions
    
    # ==================== CAREER MATCHING ====================
    
    def rank_resumes(
        self, 
        resumes: List[Dict], 
        jd_text: str
    ) -> List[Dict]:
        """
        Rank multiple resumes against a JD (for HR)
        
        Args:
            resumes: List of resume dictionaries with 'text' and 'id' keys
            jd_text: Job description text
            
        Returns:
            Ranked list of resumes with scores
        """
        ranked = []
        
        for resume in resumes:
            resume_text = resume.get('text', resume.get('raw_text', ''))
            match_result = self.calculate_detailed_match(resume_text, jd_text)
            
            ranked.append({
                'resume_id': resume.get('id'),
                'filename': resume.get('filename', 'Unknown'),
                'match_score': match_result['overall_match'],
                'skill_match': match_result['skill_match'],
                'experience_match': match_result['experience_match'],
                'matched_skills': match_result['skill_analysis']['matched_skills'],
                'missing_skills': match_result['skill_analysis']['unmatched_jd_skills']
            })
        
        # Sort by match score descending
        ranked.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Add rank
        for i, item in enumerate(ranked):
            item['rank'] = i + 1
        
        return ranked
    
    def find_career_matches(
        self, 
        resume_text: str, 
        career_options: List[str],
        top_n: int = 5
    ) -> List[Dict]:
        """
        Find matching careers for a resume
        
        Args:
            resume_text: Full resume text
            career_options: List of career titles/descriptions
            top_n: Number of top matches
            
        Returns:
            List of career matches with scores
        """
        return self.embedding_matcher.find_similar_careers(
            resume_text, 
            career_options,
            top_n
        )
    
    # ==================== UTILITY METHODS ====================
    
    def update_scoring_weights(self, weights: Dict[str, float]) -> None:
        """
        Update scoring weights
        
        Args:
            weights: Dictionary with keys: semantic, skills, experience, keywords
        """
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights should sum to 1.0, got {total}. Normalizing...")
            for key in weights:
                weights[key] = weights[key] / total
        
        self.scoring_weights.update(weights)
        logger.info(f"Updated scoring weights: {self.scoring_weights}")
    
    def add_custom_skills(self, category: str, skills: List[str], weight: float = 1.0) -> None:
        """
        Add custom skills to the database
        
        Args:
            category: Category name
            skills: List of skills
            weight: Importance weight
        """
        if category in self.skills_database:
            self.skills_database[category]['skills'].extend([s.lower() for s in skills])
            self.skills_database[category]['skills'] = list(set(self.skills_database[category]['skills']))
        else:
            self.skills_database[category] = {
                'weight': weight,
                'skills': [s.lower() for s in skills]
            }
        
        logger.info(f"Added {len(skills)} skills to category '{category}'")