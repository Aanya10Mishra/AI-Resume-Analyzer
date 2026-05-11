# HOW TO EXTRACT REAL DATA FOR EXPERIMENTS

## STEP 1: Connect to Your Database

```python
# In your terminal, make sure Flask app is NOT running
# Then run this script from project root

import sys
sys.path.insert(0, '/c/Users/Manvi/Documents/AI Resume Analyzer')

from backend.app import create_app
from backend.models.database import db, Resume, JobDescription, User

# Create app context
app = create_app('development')
with app.app_context():
    # Now you can query database
    
    # COUNT available data
    resume_count = Resume.query.count()
    jd_count = JobDescription.query.count()
    
    print(f"Total Resumes: {resume_count}")
    print(f"Total Job Descriptions: {jd_count}")
```

## STEP 2: Extract Resumes as Text

```python
# Script to extract resumes (save as: extract_data.py)

from backend.app import create_app
from backend.models.database import db, Resume

app = create_app('development')

def extract_resumes_as_text(limit=50):
    """Extract resume text for experiments"""
    
    with app.app_context():
        resumes = Resume.query.limit(limit).all()
        
        resume_texts = []
        resume_ids = []
        
        for resume in resumes:
            try:
                # Get parsed data
                parsed_data = resume.get_parsed_data()
                
                # Combine all text fields
                resume_text = ""
                
                # Add skills
                skills = parsed_data.get('skills', [])
                if skills:
                    resume_text += " ".join(skills) + " "
                
                # Add experience descriptions
                experience = parsed_data.get('experience', [])
                for exp in experience:
                    resume_text += exp.get('description', '') + " "
                
                # Add education
                education = parsed_data.get('education', [])
                for edu in education:
                    resume_text += f"{edu.get('degree')} {edu.get('field')} " 
                
                # Add summary if exists
                if parsed_data.get('summary'):
                    resume_text += parsed_data['summary']
                
                # Clean and add
                if resume_text.strip():
                    resume_texts.append(resume_text)
                    resume_ids.append(resume.id)
                    
            except Exception as e:
                print(f"Error processing resume {resume.id}: {e}")
                continue
        
        return resume_texts, resume_ids

# RUN
resume_texts, resume_ids = extract_resumes_as_text(limit=50)
print(f"Extracted: {len(resume_texts)} resumes")

# Save to file for backup
import json
with open('resume_data.json', 'w') as f:
    json.dump({
        'resumes': resume_texts,
        'ids': resume_ids,
        'count': len(resume_texts)
    }, f)

print("✅ Saved to resume_data.json")
```

## STEP 3: Extract Job Descriptions

```python
from backend.app import create_app
from backend.models.database import db, JobDescription

app = create_app('development')

def extract_jds_as_text(limit=50):
    """Extract JD text for experiments"""
    
    with app.app_context():
        jds = JobDescription.query.limit(limit).all()
        
        jd_texts = []
        jd_ids = []
        
        for jd in jds:
            try:
                # Combine relevant fields
                jd_text = f"{jd.title} {jd.description} {jd.requirements} "
                
                if jd_text.strip():
                    jd_texts.append(jd_text)
                    jd_ids.append(jd.id)
                    
            except Exception as e:
                print(f"Error processing JD {jd.id}: {e}")
                continue
        
        return jd_texts, jd_ids

# RUN
jd_texts, jd_ids = extract_jds_as_text(limit=50)
print(f"Extracted: {len(jd_texts)} job descriptions")
```

## STEP 4: Quick Data Validation

```python
# Make sure data looks good

# Check lengths
print(f"Resume texts: {len(resume_texts)}")
print(f"JD texts: {len(jd_texts)}")

# Sample output
if resume_texts:
    print(f"\n📄 Sample Resume (first 200 chars):")
    print(resume_texts[0][:200])

if jd_texts:
    print(f"\n📋 Sample JD (first 200 chars):")
    print(jd_texts[0][:200])

# Check if data is valid (not empty)
valid_resumes = [r for r in resume_texts if len(r) > 50]
valid_jds = [j for j in jd_texts if len(j) > 50]

print(f"\n✅ Valid rows - Resumes: {len(valid_resumes)}/{len(resume_texts)}")
print(f"✅ Valid rows - JDs: {len(valid_jds)}/{len(jd_texts)}")
```

## STEP 5: Run Experiments with Real Data

```python
# In experiment_runner.py, use this instead of sample data:

# Modify the main section:
if __name__ == "__main__":
    runner = ExperimentRunner()
    
    # Load REAL data
    resumes, jds = runner.load_real_resumes_from_db(limit=50)
    
    print(f"🔬 Running experiment with {len(resumes)} real resumes, {len(jds)} real JDs")
    
    # Run experiment
    results = runner.run_comparative_test(resumes, jds)
    
    # Save and display
    runner.save_results(results, filename='real_data_results.json')
    runner.print_summary(results)
```

## TROUBLESHOOTING

**Error: "No module named 'backend'"**
```bash
cd /c/Users/Manvi/Documents/AI\ Resume\ Analyzer
python -c "from backend.app import create_app; print('OK')"
```

**Error: "Database is locked"**
- Make sure Flask app is NOT running
- Another Python process might have DB lock
- Restart terminal

**Error: "Resume has no data"**
```python
# Check if parsed_data exists
for resume in resumes[:5]:
    data = resume.get_parsed_data()
    print(f"Resume {resume.id}: {len(data)} fields")
```

**Getting few results?**
- Try higher limit: `limit=100` instead of 50
- Check if DB actually has that many: `Resume.query.count()`
- Filter by date: `Resume.query.filter(Resume.created_at > datetime(2024, 1, 1))`

---

## FILE CREATED OUTPUT

After running extraction, you'll have:
- `resume_data.json` - All resume texts
- `experiment_results.json` - Comparative results
- Plus console logs with metrics
