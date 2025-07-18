#!/usr/bin/env python3
"""Test script to verify the debate response error fix"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_app import create_manual_summary

def test_error_handling():
    """Test error handling with problematic debate history"""
    print("Testing error handling for problematic debate history...")
    
    # Test with problematic debate history structures
    test_cases = [
        # Case 1: Missing 'response' key
        [
            {'model': 'gpt-4'},  # No 'response' key
            {'model': 'claude-3-sonnet', 'response': 'This is a valid response'}
        ],
        # Case 2: Missing 'model' key
        [
            {'response': 'Response without model'},  # No 'model' key
            {'model': 'gpt-4', 'response': 'Valid response'}
        ],
        # Case 3: Empty response
        [
            {'model': 'gpt-4', 'response': ''},  # Empty response
            {'model': 'claude-3-sonnet', 'response': 'Valid response'}
        ],
        # Case 4: None values
        [
            {'model': 'gpt-4', 'response': None},  # None response
            {'model': None, 'response': 'Valid response'}  # None model
        ],
        # Case 5: Mixed problematic data
        [
            {'model': 'gpt-4'},  # Missing response
            {'response': 'Missing model'},  # Missing model
            {'model': 'claude-3-sonnet', 'response': ''},  # Empty response
            {'model': 'gemini-pro', 'response': 'This is a valid response with content'}
        ]
    ]
    
    selected_models = ['gpt-4', 'claude-3-sonnet', 'gemini-pro']
    topic = "Test Topic: Error Handling"
    
    all_passed = True
    
    for i, debate_history in enumerate(test_cases, 1):
        try:
            print(f"\nTest Case {i}: {len(debate_history)} interactions")
            
            # Test manual summary creation
            summary_response = create_manual_summary(topic, debate_history, selected_models)
            
            if summary_response.is_successful():
                summary_content = summary_response.get_response()
                print(f"✅ Test Case {i} passed - Summary generated successfully")
                print(f"   Summary length: {len(summary_content)} characters")
            else:
                print(f"❌ Test Case {i} failed - Summary not successful")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Test Case {i} failed with error: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("Testing debate response error fixes...")
    success = test_error_handling()
    
    if success:
        print("\n✅ All error handling tests passed!")
        print("The 'response' key error should be fixed.")
    else:
        print("\n❌ Some error handling tests failed!")
        sys.exit(1)
