#!/usr/bin/env python3
"""
Simple admin endpoint test to debug authentication issue
"""

import requests

def test_admin_auth():
    base_url = "https://cafd1537-671b-41f5-a582-2c457f3b80d3.preview.emergentagent.com"
    
    # Login as admin
    login_response = requests.post(f"{base_url}/api/auth/login", json={
        "email": "admin@casino.com",
        "password": "admin123"
    })
    
    print(f"Login status: {login_response.status_code}")
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get('token')
        role = login_data.get('role')
        print(f"Role: {role}")
        print(f"Token: {token[:50]}...")
        
        # Test admin dashboard
        headers = {'Authorization': f'Bearer {token}'}
        dashboard_response = requests.get(f"{base_url}/api/admin/dashboard", headers=headers)
        print(f"Dashboard status: {dashboard_response.status_code}")
        
        # Test admin sessions
        sessions_response = requests.get(f"{base_url}/api/admin/games/sessions", headers=headers)
        print(f"Sessions status: {sessions_response.status_code}")
        if sessions_response.status_code != 200:
            print(f"Sessions error: {sessions_response.text}")
        else:
            print("Sessions endpoint works!")
            
        # Test admin activity report
        activity_response = requests.get(f"{base_url}/api/admin/reports/activity", headers=headers)
        print(f"Activity status: {activity_response.status_code}")
        if activity_response.status_code != 200:
            print(f"Activity error: {activity_response.text}")
        else:
            print("Activity endpoint works!")

if __name__ == "__main__":
    test_admin_auth()