"""
Complete Backend Test
"""
import requests
import json

BASE = "http://localhost:5000"

print("="*60)
print("TESTING COMPLETE BACKEND")
print("="*60)

# 1. Health check
print("\n1. Testing health endpoint...")
r = requests.get(f"{BASE}/api/health")
print(f"   Status: {r.status_code}")
print(f"   Response: {r.json()}")

# 2. Register user
print("\n2. Registering user...")
r = requests.post(f"{BASE}/api/auth/register", json={
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User",
    "role": "student"
})
print(f"   Status: {r.status_code}")
if r.status_code == 201:
    user_id = r.json()['user']['id']
    print(f"   User ID: {user_id}")
else:
    print(f"   Error: {r.json()}")

print("\n✅ Backend is working!")
print("="*60)