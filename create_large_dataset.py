"""
Generate LARGE realistic dataset with 50+ resumes and JDs
This will show REAL differences in paper results
"""

import json
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base templates for diverse roles
RESUME_TEMPLATES = {
    'Backend': [
        "Senior Backend Engineer with 6 years Python, Django, FastAPI experience. Expert in PostgreSQL, Redis, MongoDB. AWS certified architect. Microservices, CI/CD, Docker, Kubernetes. Led team of 8. Strong OOP, design patterns. API design, database optimization.",
        "Backend Developer 5 years Java Spring Boot. Experienced with SQL, NoSQL databases. Kafka, RabbitMQ messaging. Microservices architecture. Docker containerization. AWS EC2, S3. REST APIs, GraphQL.",
        "Python Backend Specialist. 4 years Flask, Django, FastAPI. PostgreSQL, MySQL expertise. Redis caching. Docker deployment. Linux server management. API development.",
        "Senior Java Developer. 7 years Spring, Spring Boot. Enterprise applications. SQL Server, Oracle databases. Multithreading, concurrency. Performance optimization.",
        "Backend Engineer with C# .NET Core. 5 years development. SQL Server databases. Azure cloud platform. RESTful APIs. Entity Framework ORM.",
    ],
    'Frontend': [
        "React Frontend Developer 5 years React.js, Redux. Building responsive UIs with Tailwind CSS, Material-UI. Jest, Cypress testing. Web performance optimization. Accessibility standards. TypeScript, ES6+.",
        "Full Stack JavaScript Engineer 6 years. React frontend expertise. Node.js, Express backend. MongoDB databases. GraphQL API design. Docker deployment.",
        "Vue.js Specialist 4 years. Single page applications. Vuex state management. Component development. REST API integration. CSS, SASS, Bootstrap.",
        "Angular Developer 5 years Angular framework. TypeScript expert. RxJS reactive programming. Material Design. State management with NgRx.",
        "Frontend Engineer with React, Next.js expertise. 4 years building scalable applications. Server-side rendering. Performance optimization. SEO implementation.",
    ],
    'ML/AI': [
        "Machine Learning Engineer 5 years. TensorFlow, PyTorch expertise. Deep learning, NLP. Computer vision projects. Python, scikit-learn. Data preprocessing, feature engineering. Published ML research.",
        "Data Scientist 6 years. Python, R programming. Statistical analysis, machine learning. Pandas, NumPy, scikit-learn. SQL for data querying. Data visualization with Matplotlib, Seaborn.",
        "AI/ML Specialist 4 years. Neural networks, transformers. BERT, GPT models. NLP applications. Python TensorFlow. Published papers on deep learning.",
        "Data Science Engineer with MLOps focus. 5 years. TensorFlow, PyTorch. Model deployment, monitoring. Docker, Kubernetes. MLflow tracking.",
        "Research Scientist in AI. 6 years deep learning. Computer vision, NLP. Novel architectures. Published at top conferences.",
    ],
    'DevOps': [
        "DevOps Engineer 6 years. Kubernetes, Docker expertise. Infrastructure as code with Terraform. AWS, Azure clouds. CI/CD pipelines Jenkins, GitLab. Prometheus, Grafana monitoring.",
        "Cloud Architect 7 years AWS. EC2, S3, RDS, Lambda. Cost optimization. Security best practices. Terraform, CloudFormation. High availability design.",
        "Site Reliability Engineer 5 years. System administration Linux. Kubernetes orchestration. Monitoring, alerting systems. Disaster recovery planning. On-call management.",
        "Infrastructure Engineer with Kubernetes expertise. 6 years. Container orchestration, Helm. CI/CD automation. Prometheus monitoring. GitOps methodology.",
        "Cloud Infrastructure Specialist 4 years GCP. Compute, storage, networking. Terraform Infrastructure-as-code. Cloud security.",
    ],
    'Mobile': [
        "React Native Developer 4 years. Cross-platform mobile apps. iOS, Android deployment. Push notifications, offline sync. JavaScript, TypeScript.",
        "Flutter Developer 3 years. Mobile app development. Dart programming. App store deployment iOS/Android. Firebase integration.",
        "iOS Developer 5 years Swift. Native iOS development. UIKit, SwiftUI. App store guidelines. In-app purchases, analytics.",
        "Mobile Engineer with React Native, Flutter. 5 years shipping apps. Performance optimization. Mobile testing. App monetization.",
        "Android Developer 6 years Kotlin, Java. Material Design. Play Store deployment. Firebase integration.",
    ],
    'QA/Testing': [
        "QA Engineer 5 years. Selenium automation, Cypress, Jest testing. API testing with Postman. CI/CD pipeline integration. Test case design.",
        "Test Automation Engineer 6 years. Selenium WebDriver expertise. Python, JavaScript test scripts. BDD with Cucumber. Jenkins automation.",
        "Quality Assurance Specialist 4 years. Manual testing, automation. Test plan creation. Regression testing. Bug reporting, tracking.",
        "SW Testing Engineer with automation focus. 5 years Selenium, Appium. Test framework design. Load testing tools. JMeter expertise.",
        "QA Lead 7 years. Test automation architecture. Team management. Testing strategy. Process improvement.",
    ],
}

JD_TEMPLATES = {
    'Backend': [
        "Senior Backend Engineer needed - 5+ years Python/Django/FastAPI required. Build scalable APIs using PostgreSQL, Redis. Microservices architecture, Kubernetes, Docker. AWS experience essential. Strong system design skills needed.",
        "Backend Developer wanted - 4+ years Java Spring Boot. SQL/NoSQL databases required. Kafka messaging experience. REST API design. Docker containerization knowledge.",
        "Python Backend Role - 4+ years Flask/Django experience required. PostgreSQL expertise. Redis caching. API development. Performance optimization critical.",
        "Senior Java Architect - 6+ years Spring Boot, enterprise Java. SQL Server / Oracle databases. System design, scalability. Microservices architecture.",
        ".NET Backend Engineer - 5+ years C# .NET Core. SQL Server databases. Azure cloud experience. REST APIs essential.",
    ],
    'Frontend': [
        "React Frontend Developer - 4+ years React.js, Redux required. Build beautiful UIs with Material-UI, Tailwind. Jest/Cypress testing mandatory. Performance optimization skills needed.",
        "Full Stack JavaScript - 5+ years React frontend expertise. Node.js, Express backend required. MongoDB databases. GraphQL API design experience.",
        "Vue.js Developer wanted - 3+ years Vue.js framework. Component-based development. State management Vuex. CSS, responsive design skills.",
        "Angular Developer - 4+ years Angular framework expertise. TypeScript required. RxJS reactive programming. Material Design implementation.",
        "Frontend Lead - 5+ years React, Next.js expertise. Server-side rendering knowledge. Performance optimization. SEO implementation skills.",
    ],
    'ML/AI': [
        "Machine Learning Engineer - 4+ years TensorFlow/PyTorch required. Deep learning expertise. NLP or Computer Vision experience. Python programming essential.",
        "Data Scientist - 5+ years statistical analysis, ML. Python, R programming required. SQL for data querying. Data visualization skills (Tableau/Power BI).",
        "AI Research Engineer - 4+ years deep learning. Novel model architectures. Published research experience. Python TensorFlow/PyTorch expertise.",
        "MLOps Engineer - 5+ years ML model deployment. Docker, Kubernetes required. MLflow, experiment tracking. Model monitoring systems.",
        "AI/ML Specialist - 6+ years machine learning projects. Statistical modeling. Feature engineering expertise. Python scikit-learn.",
    ],
    'DevOps': [
        "DevOps Engineer - Kubernetes, Docker essential. 5+ years infrastructure experience. Terraform infrastructure-as-code required. AWS or Azure cloud platform.",
        "Cloud Architect wanted - 6+ years AWS architectural design. EC2, RDS, Lambda expertise. CloudFormation or Terraform. High availability systems.",
        "SRE - 5+ years Linux system administration. Kubernetes orchestration required. Monitoring systems Prometheus/Grafana. On-call experience essential.",
        "Infrastructure Engineer - 5+ years Kubernetes deployment. CI/CD pipeline design. Jenkins or GitLab CI experience. Helm charts knowledge.",
        "Cloud Infrastructure Lead - 6+ years GCP/AWS/Azure. Terraform infrastructure-as-code. Security best practices. Cost optimization experience.",
    ],
    'Mobile': [
        "React Native Developer wanted - 3+ years React Native experience required. iOS and Android deployment. Push notifications, offline sync needed.",
        "Flutter Developer - 3+ years Flutter framework expertise. Dart programming required. iOS/Android app store deployment experience.",
        "iOS Developer - 4+ years Swift programming required. Native iOS development with UIKit/SwiftUI. App store deployment knowledge.",
        "Mobile Engineer - 4+ years React Native or Flutter. Cross-platform development expertise. Performance optimization critical.",
        "Android Developer - 5+ years Kotlin/Java Android development. Material Design implementation. Play Store deployment experience.",
    ],
    'QA/Testing': [
        "QA Automation Engineer - 4+ years Selenium expertise required. Test automation frameworks. CI/CD pipeline integration essential. API testing knowledge.",
        "Test Automation Lead - 5+ years test automation architecture. Selenium WebDriver, framework design. Team leadership experience.",
        "QA Engineer - 4+ years QA experience, automation preferred. Jest, Cypress, Selenium skills. Regression testing expertise.",
        "Software Testing Engineer - 5+ years test automation. Appium for mobile testing. Load testing tools JMeter experience.",
        "Quality Assurance Specialist - 4+ years QA best practices. Test case design, automation. Bug tracking systems. Process improvement.",
    ],
}

def generate_large_dataset(resumes_count=50, jds_count=50):
    """Generate large realistic dataset"""
    
    logger.info(f"📊 Generating {resumes_count} resumes and {jds_count} JDs...")
    
    roles = list(RESUME_TEMPLATES.keys())
    resumes = []
    jds = []
    
    # Generate resumes
    for i in range(resumes_count):
        role = roles[i % len(roles)]
        resume = random.choice(RESUME_TEMPLATES[role])
        # Add some variation
        resume += f" Project experience: {5 + i % 10}+ years. Key achievements: Led {i % 5 + 2} projects. Strong communication skills."
        resumes.append(resume)
    
    # Generate JDs
    for i in range(jds_count):
        role = roles[i % len(roles)]
        jd = random.choice(JD_TEMPLATES[role])
        # Add variation
        jd += f" Salary: ${80 + i % 50}K. Location: Remote/On-site hybrid. Benefits: Health insurance, 401k, PTO."
        jds.append(jd)
    
    logger.info(f"✅ Generated {len(resumes)} resumes")
    logger.info(f"✅ Generated {len(jds)} JDs")
    
    # Save dataset
    dataset = {
        'resumes': resumes,
        'jds': jds,
        'count': {
            'resumes': len(resumes),
            'jds': len(jds)
        }
    }
    
    with open('large_realistic_data.json', 'w') as f:
        json.dump(dataset, f, indent=2)
    
    logger.info(f"✅ Saved to large_realistic_data.json")
    
    # Show samples
    logger.info(f"\n📝 Sample Resume:")
    logger.info(f"   {resumes[0][:150]}...")
    
    logger.info(f"\n📋 Sample JD:")
    logger.info(f"   {jds[0][:150]}...")

if __name__ == "__main__":
    generate_large_dataset(resumes_count=50, jds_count=50)
