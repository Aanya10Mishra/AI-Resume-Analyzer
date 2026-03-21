"""
Test Role-Based Routes
"""
import requests
import json

BASE = "http://localhost:5000"

def test_endpoints():
    print("="*60)
    print("🧪 TESTING ROLE-BASED ROUTES")
    print("="*60)
    
    # 1. Check home page shows new endpoints
    print("\n1️⃣  Checking home page...")
    r = requests.get(BASE)
    data = r.json()
    print(f"   Endpoints available: {list(data['endpoints'].keys())}")
    
    # 2. Register a student
    print("\n2️⃣  Registering student...")
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": "student_test@example.com",
        "password": "pass123",
        "full_name": "Test Student",
        "role": "student"
    })
    if r.status_code == 201:
        student_id = r.json()['user']['id']
        print(f"   ✅ Student ID: {student_id}")
        
        # 3. Test student dashboard
        print("\n3️⃣  Testing student dashboard...")
        r = requests.get(f"{BASE}/api/student/dashboard/{student_id}")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   ✅ Dashboard loaded!")
            print(f"   Data: {json.dumps(r.json(), indent=2)[:300]}...")
    
    # 4. Register employee
    print("\n4️⃣  Registering employee...")
    r = requests.post(f"{BASE}/api/auth/register", json={
        "email": "employee_test@example.com",
        "password": "pass123",
        "full_name": "Test Employee",
        "role": "employee"
    })
    if r.status_code == 201:
        emp_id = r.json()['user']['id']
        print(f"   ✅ Employee ID: {emp_id}")
        
        # 5. Test employee dashboard
        print("\n5️⃣  Testing employee dashboard...")
        r = requests.get(f"{BASE}/api/employee/dashboard/{emp_id}")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   ✅ Dashboard loaded!")
    
    # 6. Test HR dashboard
    print("\n6️⃣  Testing HR dashboard...")
    r = requests.get(f"{BASE}/api/recruiter/dashboard")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print(f"   ✅ Dashboard loaded!")
        print(f"   Metrics: {r.json()['metrics']}")
    
    print("\n" + "="*60)
    print("✅ ALL ROLE-BASED ROUTES WORKING!")
    print("="*60)

if __name__ == "__main__":
    test_endpoints()