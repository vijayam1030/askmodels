#!/usr/bin/env python3
"""
Test OCR functionality with a simple image
"""

import os
import base64
from PIL import Image, ImageDraw, ImageFont
import pytesseract

def create_test_image():
    """Create a simple test image with text"""
    # Create a white image with black text
    img = Image.new('RGB', (400, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw some test text
    test_text = "Hello World! OCR Test 123"
    draw.text((10, 30), test_text, fill='black')
    
    # Save test image
    test_path = 'uploads/test_image.png'
    os.makedirs('uploads', exist_ok=True)
    img.save(test_path)
    print(f"✅ Created test image: {test_path}")
    
    return test_path

def test_ocr():
    """Test OCR on the created image"""
    try:
        # Create test image
        image_path = create_test_image()
        
        # Test OCR
        print("🔍 Testing Tesseract OCR...")
        with Image.open(image_path) as img:
            extracted_text = pytesseract.image_to_string(img)
            print(f"✅ OCR Result: '{extracted_text.strip()}'")
            
        return True
        
    except Exception as e:
        print(f"❌ OCR Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OCR functionality...")
    success = test_ocr()
    if success:
        print("✅ OCR test passed!")
    else:
        print("❌ OCR test failed!")
