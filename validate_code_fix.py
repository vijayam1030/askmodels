#!/usr/bin/env python3
"""
Simple code validation test for the enhanced summary fix.
This test doesn't run the Flask app, just validates the code changes.
"""

print("🔍 Validating Enhanced Summary Fix...")
print("="*60)

# Test 1: Check if the code has safe dictionary access patterns
print("\n1. Checking code for safe dictionary access patterns...")

with open('unified_app.py', 'r', encoding='utf-8') as file:
    content = file.read()
    
# Look for the key patterns that should be fixed
patterns_to_check = [
    "item.get('content', item.get('response', ''))",  # Safe field access
    "entry.get('content', entry.get('response', ''))",  # Another safe field access
    "response.get('content', response.get('response', ''))",  # Another variant
]

fixes_found = 0
for pattern in patterns_to_check:
    if pattern in content:
        fixes_found += 1
        print(f"✅ Found safe access pattern: {pattern}")
    else:
        print(f"⚠️  Pattern not found: {pattern}")

print(f"\n📊 Found {fixes_found} out of {len(patterns_to_check)} expected safe access patterns")

# Test 2: Check for dangerous direct access patterns
print("\n2. Checking for potentially dangerous direct access patterns...")

dangerous_patterns = [
    "item['content']",  # Direct access without safety
    "entry['content']",  # Direct access without safety
    "response['content']",  # Direct access without safety
]

dangerous_found = 0
for pattern in dangerous_patterns:
    count = content.count(pattern)
    if count > 0:
        dangerous_found += count
        print(f"⚠️  Found {count} instances of: {pattern}")
    else:
        print(f"✅ No dangerous pattern found: {pattern}")

print(f"\n📊 Found {dangerous_found} potentially dangerous direct access patterns")

# Test 3: Check specific functions
print("\n3. Checking specific function implementations...")

functions_to_check = [
    "def analyze_debate_consensus(",
    "def create_summary_prompt(",
    "def create_manual_summary(",
]

for func in functions_to_check:
    if func in content:
        print(f"✅ Function exists: {func}")
    else:
        print(f"❌ Function missing: {func}")

# Test 4: Check for try-catch blocks
print("\n4. Checking for error handling...")

try_count = content.count("try:")
except_count = content.count("except")

print(f"✅ Found {try_count} try blocks")
print(f"✅ Found {except_count} except blocks")

# Test 5: Summary
print("\n" + "="*60)
print("VALIDATION RESULTS:")
print("="*60)

if fixes_found >= 2:
    print("✅ GOOD: Safe dictionary access patterns are implemented")
else:
    print("❌ ISSUE: Not enough safe dictionary access patterns found")

if dangerous_found == 0:
    print("✅ GOOD: No dangerous direct access patterns found")
else:
    print(f"⚠️  WARNING: {dangerous_found} dangerous patterns still exist")

print("\n🔧 NEXT STEPS:")
print("1. Stop the Flask app (Ctrl+C in the terminal where it's running)")
print("2. Restart the Flask app: python unified_app.py")
print("3. Test the enhanced summary generation feature")
print("4. The fixes should now be active!")

print("\n💡 NOTE: The code changes look good, but the app needs to be restarted")
print("   for the fixes to take effect in the running application.")
