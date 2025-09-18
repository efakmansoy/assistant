#!/usr/bin/env python3
"""
Admin API test
"""
import requests
import json

# Test data
competition_data = {
    "name": "Test Yarışması",
    "description": "Test açıklaması",
    "registration_deadline": "2025-12-31",
    "submission_deadline": "2025-12-31",
    "is_active": True
}

# First login
login_data = {
    "username": "admin",
    "password": "admin123"
}

session = requests.Session()

# Login
print("Logging in...")
login_response = session.post('http://localhost:5000/auth/login', data=login_data)
print(f"Login status: {login_response.status_code}")

# Add competition
print("Adding competition...")
response = session.post(
    'http://localhost:5000/admin/competitions',
    headers={'Content-Type': 'application/json'},
    data=json.dumps(competition_data)
)

print(f"Response status: {response.status_code}")
print(f"Response content: {response.text}")