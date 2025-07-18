#!/usr/bin/env python3
"""Test script to verify the summary generation fixes"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_app import create_manual_summary

def test_manual_summary():
    """Test the manual summary generation"""
    print("Testing manual summary generation...")
    
    # Mock debate history
    debate_history = [
        {
            'model': 'gpt-4',
            'response': 'This is a sample response from GPT-4 about the debate topic. It provides detailed analysis and arguments.'
        },
        {
            'model': 'claude-3-sonnet',
            'response': 'Claude responds with a different perspective on the topic, offering counter-arguments and additional insights.'
        },
        {
            'model': 'gpt-4',
            'response': 'GPT-4 provides a follow-up response, building on the previous discussion and addressing Claude\'s points.'
        }
    ]
    
    selected_models = ['gpt-4', 'claude-3-sonnet']
    topic = "Test Topic: AI Impact on Society"
    
    try:
        # Test manual summary creation
        summary_response = create_manual_summary(topic, debate_history, selected_models)
        
        print(f"Summary generation successful: {summary_response.is_successful()}")
        print("\nSummary content:")
        print("-" * 50)
        print(summary_response.get_response())
        print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"Error in manual summary generation: {e}")
        return False

if __name__ == "__main__":
    success = test_manual_summary()
    if success:
        print("\n✅ Manual summary generation test passed!")
    else:
        print("\n❌ Manual summary generation test failed!")
        sys.exit(1)
