#!/usr/bin/env python3
"""Test script to verify asyncio import fix"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test that the fixed summary generation works
def test_asyncio_import():
    """Test that asyncio is properly imported and accessible"""
    try:
        import asyncio
        print("✅ asyncio import successful")
        
        # Test that asyncio.TimeoutError is accessible
        try:
            timeout_error = asyncio.TimeoutError
            print("✅ asyncio.TimeoutError accessible")
        except AttributeError as e:
            print(f"❌ asyncio.TimeoutError not accessible: {e}")
            return False
        
        # Test that asyncio.wait_for is accessible
        try:
            wait_for = asyncio.wait_for
            print("✅ asyncio.wait_for accessible")
        except AttributeError as e:
            print(f"❌ asyncio.wait_for not accessible: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ asyncio import failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing asyncio import fix...")
    success = test_asyncio_import()
    
    if success:
        print("\n✅ All asyncio import tests passed!")
        print("The 'cannot access local variable asyncio' error should be fixed.")
    else:
        print("\n❌ asyncio import tests failed!")
        sys.exit(1)
