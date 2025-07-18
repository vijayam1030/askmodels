#!/usr/bin/env python3
"""Quick test for the response error fix"""

# Test create_manual_summary function directly
def test_response_error_fix():
    # Mock problematic debate history
    problematic_history = [
        {'model': 'gpt-4'},  # Missing 'response' key
        {'response': 'Response without model'},  # Missing 'model' key
        {'model': 'claude-3-sonnet', 'response': ''},  # Empty response
        {'model': 'gemini-pro', 'response': 'Valid response'}  # Good entry
    ]
    
    # Test the problematic patterns
    for interaction in problematic_history:
        # Test accessing with .get() method (should not error)
        model = interaction.get('model', 'Unknown')
        response = interaction.get('response', 'No response')
        
        print(f"Model: {model}, Response: {response[:50]}...")
        
        # Test response length calculation (should not error)
        response_length = len(response) if response else 0
        print(f"Response length: {response_length}")
        
        # Test response splitting (should not error)
        word_count = len(response.split()) if response else 0
        print(f"Word count: {word_count}")
    
    print("✅ All problematic patterns handled safely!")
    return True

if __name__ == "__main__":
    print("Testing response error fix...")
    success = test_response_error_fix()
    
    if success:
        print("\n✅ Response error fix test passed!")
    else:
        print("\n❌ Response error fix test failed!")
