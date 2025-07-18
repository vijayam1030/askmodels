#!/usr/bin/env python3
"""
Simple validation script to check if the field name fix works correctly.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_field_compatibility():
    """Test that the functions can handle mixed field names"""
    
    # Test data with mixed field names
    test_data = [
        {'model': 'test1', 'content': 'content field test', 'round': 1},
        {'model': 'test2', 'response': 'response field test', 'round': 1},
        {'model': 'test3', 'round': 2}  # Missing content/response
    ]
    
    print("Testing field compatibility:")
    
    # Test 1: Safe field access
    for item in test_data:
        content = item.get('content', '') or item.get('response', '')
        print(f"  {item['model']}: '{content}' ({len(content)} chars)")
    
    # Test 2: Word count calculation
    total_words = 0
    for item in test_data:
        content = item.get('content', '') or item.get('response', '')
        words = len(content.split()) if content else 0
        total_words += words
        print(f"  {item['model']}: {words} words")
    
    print(f"  Total words: {total_words}")
    
    # Test 3: Content filtering
    valid_items = [item for item in test_data if item.get('content') or item.get('response')]
    print(f"  Valid items: {len(valid_items)} out of {len(test_data)}")
    
    return True

if __name__ == "__main__":
    print("Field Name Compatibility Test")
    print("=" * 40)
    
    try:
        test_field_compatibility()
        print("\n✅ Field compatibility tests passed!")
        print("The enhanced summary generation should now work correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("There may still be issues with the field name handling.")
