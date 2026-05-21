# 🤖 AI Resume Analyzer

Unlock the power of AI for job hunting!  
**AI Resume Analyzer** is an advanced platform that uses cutting-edge AI models to analyze resumes, deliver ATS (Applicant Tracking System) scoring, and generate personalized career content. With five professional AI-driven features, you’ll get actionable improvements for your resume, tailored suggestions, and much more.

---

![Python](https://img.shields.io/badge/Python-55.4%25-blue)
![JavaScript](https://img.shields.io/badge/JavaScript-26.7%25-yellow)
![HTML](https://img.shields.io/badge/HTML-17.9%25-orange)
![Status](https://img.shields.io/badge/AI-Driven-blueviolet)


---

## 🚀 How It Works

1. **Upload Your Resume:** Start by uploading your resume as a user.
2. **Parsing & ATS Scoring:** The backend extracts and analyzes key data using advanced NLP and ML, including skills, experience, and education, then benchmarks you with ATS scoring.
3. **Select a Job (Optional):** Get even deeper insights by comparing your resume to a specific job description.
4. **AI Features:** Access any of the following professional AI features for actionable outcomes.
5. **Instant Results:** The web interface provides scores, improvement suggestions, tailored content, and more—instantly!

---

## 🌟 Core AI Features

### 1. **AI Resume Improvement Suggestions**
- **What it does:**  
  Analyzes your resume using Groq's Llama AI model and provides prioritized recommendations to enhance your content for both human readability and ATS optimization.
- **How:**  
  Calls the backend `/api/ai/improve-resume/<id>` which reviews your parsed data, ATS performance, and returns high/medium-priority actionable tips.  
- **Sample outcomes:** Improve achievements, clarify roles, optimize keywords, highlight leadership.

---

### 2. **Job Match & ATS Score**
- **What it does:**  
  Compares your resume directly to a job description and computes a matching percentage, breaking down relevance across skills, roles, and keywords.
- **How:**  
  The system extracts requirements from the job description, cross-references with your resume, and calculates a score for easy ATS-readiness assessment.
- **Sample outcomes:** See which skills or sections need enhancement to align better with a particular job.

---

### 3. **Career Path Recommendations**
- **What it does:**  
  AI analyzes your background and suggests customized career routes you might consider, based on your existing profile, market trends, and adjacent opportunities.
- **How:**  
  Backend uses your profile and skillset, matches with labor market data, then Groq AI generates concise, realistic next-steps and career advice.
- **Sample outcomes:** Pathways for advancement, lateral moves, in-demand skills for your role, roadmaps for switching sectors.

---

### 4. **Skill Gap Analysis & AI-Powered Learning Recommendations**
- **What it does:**  
  Identifies missing skills for your chosen job targets and recommends precise skills to put you ahead, complete with learning paths if desired.
- **How:**  
  Compares your skillset versus recent job matches, fetches market-demanded skills, and queries AI for a learning plan.
- **Sample outcomes:** List of top 5 skills to learn next, with reasoning and links to resources.

---

### 5. **One-Click Tailored Resume & Cover Letter Generation**
- **What it does:**  
  Instantly rewrites your resume and generates a cover letter adapted to a specific job description—personalized and ATS-friendly.
- **How:**  
  Using the AI backend, it tailors every section for maximum relevance using evidence from your resume and the job ad.
- **Sample outcomes:** Ready-to-use, job-specific resume sections and a personalized cover letter in your preferred tone.

---

## 🧩 Project Structure

- **Python Backend:** Handles resume parsing, AI scoring, and interaction with Groq AI models.
- **Frontend (HTML/JS):** Elegant dashboard for uploading, selecting, and viewing analyses and AI outputs.
- **Endpoints:**  
  - `/api/ai/improve-resume/<resume_id>`
  - `/api/ai/skill-recommendations/<resume_id>`
  - `/api/ai/tailored-resume/<resume_id>`
  - `/api/ai/career-advice/<user_id>`
  - And more, powering each AI feature.

---

## 💡 Example Workflow

1. Upload or select your resume.
2. Click "Get AI Suggestions" to receive actionable improvement tips.
3. Choose a job for ATS score and gap analysis.
4. Open "Career Path" or "Skill Growth" for guidance on next steps.
5. Click "Tailor Resume" for a personalized, role-specific resume rewrite.
6. Get a custom cover letter for your job application—all at lightning speed!

---

## 🛡️ Security & Privacy

- Documents are processed securely and are not retained post-analysis.
- No sharing of your data.

---

## 🤝 Contributing

Pull requests are welcome! For significant changes, please open an issue first to discuss what you’d like to add.

---


> **Built with state-of-the-art NLP and AI. Ready to supercharge your job hunt!**
