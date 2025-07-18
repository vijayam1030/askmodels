#!/usr/bin/env python3
"""
Test script to verify the puzzle API is working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_app import app, dashboard_provider

def test_puzzle_api():
    """Test the puzzle API endpoint"""
    print("Testing puzzle API...")
    
    # Test the DashboardProvider directly
    puzzle_data = dashboard_provider.get_puzzle_data()
    print(f"Direct puzzle data: {puzzle_data}")
    
    # Test with Flask app context
    with app.test_client() as client:
        response = client.get('/api/dashboard/puzzle')
        print(f"API response status: {response.status_code}")
        print(f"API response data: {response.get_json()}")
        
        # Test dashboard route
        dashboard_response = client.get('/dashboard')
        print(f"Dashboard route status: {dashboard_response.status_code}")
        print(f"Dashboard route content type: {dashboard_response.content_type}")

if __name__ == "__main__":
    test_puzzle_api()
