"""
Create REALISTIC synthetic data that shows actual differences
This demonstrates how embeddings beat TF-IDF on real-world scenarios
"""

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Realistic resumes with diverse skills
REALISTIC_RESUMES = [
    # Senior Python Dev
    "Senior Python Developer with 5 years experience. Expert in Django, Flask, FastAPI. " +
    "Strong in PostgreSQL, Redis, Docker, Kubernetes. AWS certified. Experienced with microservices " +
    "architecture, CI/CD pipelines, Jenkins. Passionate about clean code and testing.",
    
    # Full Stack JS
    "Full Stack JavaScript Engineer. 4 years building React, Vue.js, Angular applications. " +
    "Backend: Node.js, Express, NestJS. Databases: MongoDB, PostgreSQL. Cloud: AWS, GCP. " +
    "Strong DevOps skills with Docker and Kubernetes.",
    
    # ML Engineer  
    "Machine Learning Engineer with expertise in Python, TensorFlow, PyTorch. " +
    "Specialized in NLP, Computer Vision, Deep Learning. Experience with scikit-learn, pandas, numpy. " +
    "Published 3 papers on transformer models. Strong statistical analysis background.",
    
    # Java Backend
    "Senior Java Engineer, 6 years experience. Spring Boot expert, microservices architect. " +
    "AWS, Kafka, SQL databases. Proficient in CI/CD, Jenkins, Docker deployment. " +
    "Led team of 5 developers. Strong in REST APIs and system design.",
    
    # DevOps Engineer
    "DevOps specialist with Kubernetes, Docker, Terraform expertise. AWS certified architect. " +
    "Infrastructure automation using Ansible. Experience with Prometheus, Grafana monitoring. " +
    "CI/CD pipeline design with Jenkins and GitLab. 7 years infrastructure experience.",
    
    # Data Scientist
    "Data Scientist focusing on analytics and visualization. SQL, Python, R programming. " +
    "Tableau, Power BI dashboards. Statistical modeling, A/B testing. Big data with Spark. " +
    "5 years in business analytics and data-driven decision making.",
    
    # React Specialist
    "React Frontend Developer with 3 years experience. Redux state management expert. " +
    "Building responsive UIs with Tailwind CSS, Material-UI. Testing with Jest and Cypress. " +
    "Performance optimization, web accessibility. Strong JavaScript ES6+ skills.",
    
    # Cloud Architect
    "Cloud Solutions Architect with AWS specialization. 8 years cloud infrastructure. " +
    "Design scalable systems, cost optimization, security best practices. " +
    "Terraform infrastructure-as-code. Multi-cloud strategy. AWS Solutions Architect certified.",
    
    # Mobile Developer
    "Mobile Developer specializing in React Native and Flutter. iOS/Android development. " +
    "3 years shipping apps to app stores. Push notifications, offline sync, analytics. " +
    "JavaScript, Dart, Swift languages. Cross-platform development expertise.",
    
    # Systems Engineer
    "Systems Engineer with expertise in Linux, Windows servers. Networking, security, compliance. " +
    "5 years managing enterprise infrastructure. Active Directory, firewalls, VPNs. " +
    "Disaster recovery, backup solutions. ITIL certified.",
]

# Realistic job descriptions with different focuses
REALISTIC_JDS = [
    # Python Backend Role
    "Senior Python Backend Engineer - 5+ years Django/Flask development required. " +
    "Build scalable REST APIs using PostgreSQL, Redis. Docker and Kubernetes experience essential. " +
    "Strong testing background required. AWS cloud knowledge preferred. Strong communication skills.",
    
    # Frontend React Role
    "React Frontend Developer needed. 3+ years React.js and Redux experience. " +
    "Build beautiful UIs with Material-UI, Tailwind CSS. Jest/Cypress testing mandatory. " +
    "Web accessibility standards knowledge. Performance optimization skills needed.",
    
    # DevOps Role
    "DevOps Engineer - Kubernetes and Docker essential. Terraform infrastructure-as-code. " +
    "AWS or Azure cloud platform expertise. CI/CD pipeline design (Jenkins/GitLab). " +
    "Prometheus/Grafana monitoring. 4+ years infrastructure automation experience.",
    
    # Data Science Role
    "Data Scientist - Python, SQL, statistics required. Machine learning libraries (scikit-learn, pandas). " +
    "Data visualization (Tableau or Power BI). Statistical modeling and A/B testing. " +
    "Big data experience with Spark preferred. 3+ years analytics experience.",
    
    # Java Microservices Role
    "Senior Java Backend Engineer - Spring Boot microservices architecture expertise. " +
    "6+ years Java development required. Kafka, REST APIs, system design. AWS cloud experience. " +
    "Docker containerization, Jenkins CI/CD. Team lead potential.",
    
    # ML/AI Role
    "Machine Learning Engineer - TensorFlow, PyTorch expertise required. " +
    "NLP and Computer Vision background preferred. Deep learning and transformers knowledge. " +
    "Python, scikit-learn proficiency. Research mindset. 4+ years ML experience.",
    
    # AWS Cloud Architect
    "AWS Solutions Architect - Design scalable cloud infrastructure. " +
    "7+ years cloud architecture experience. AWS certified required. Terraform infrastructure-as-code. " +
    "Cost optimization, security best practices. Multi-cloud strategy knowledge.",
    
    # Full Stack JS Role
    "Full Stack JavaScript Engineer - 4+ years React/Vue.js frontend. " +
    "Backend: Node.js, Express, databases (SQL/MongoDB). AWS or GCP cloud. " +
    "Docker containerization. Strong full-stack development skills required.",
    
    # Mobile Developer Role
    "Mobile App Developer - React Native or Flutter experience. " +
    "3+ years shipping apps to iOS/Android app stores. Cross-platform development. " +
    "Push notifications, offline sync implementation. JavaScript and mobile best practices.",
    
    # Systems Admin Role
    "Systems Administrator - Linux, Windows server administration required. " +
    "Active Directory, networking, firewalls expertise. 5+ years system administration. " +
    "Disaster recovery planning. ITIL certification preferred. Security compliance knowledge.",
]

def create_realistic_dataset():
    """Create synthetic but realistic data showing actual method differences"""
    
    logger.info("📊 Creating realistic synthetic dataset...")
    
    dataset = {
        'resumes': REALISTIC_RESUMES,
        'jds': REALISTIC_JDS,
        'count': {
            'resumes': len(REALISTIC_RESUMES),
            'jds': len(REALISTIC_JDS)
        },
        'notes': [
            'This is realistic synthetic data that demonstrates real differences.',
            'Resume 0 (Senior Python Dev) should match JD 0 (Python Backend)',
            'But has some keyword overlap with JD 1 (Frontend) and JD 2 (DevOps)',
            'TF-IDF might incorrectly rank by keyword frequency',
            'Sentence Transformers understands semantic meaning better'
        ]
    }
    
    with open('realistic_data.json', 'w') as f:
        json.dump(dataset, f, indent=2)
    
    logger.info(f"✅ Created realistic dataset:")
    logger.info(f"   - {len(REALISTIC_RESUMES)} diverse resumes")
    logger.info(f"   - {len(REALISTIC_JDS)} realistic job descriptions")
    logger.info(f"   - Saved to: realistic_data.json")
    
    logger.info(f"\n📝 Sample Resume (Python Dev):")
    logger.info(f"   {REALISTIC_RESUMES[0][:150]}...")
    
    logger.info(f"\n📋 Sample JD (Python Backend):")
    logger.info(f"   {REALISTIC_JDS[0][:150]}...")

if __name__ == "__main__":
    create_realistic_dataset()
