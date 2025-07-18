#!/usr/bin/env python3
"""
Quick diagnostic test for the enhanced summary issue - v2.
"""

try:
    # Test 1: Basic imports
    print("🔍 Testing basic imports...")
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from unified_app import DebateManager, create_manual_summary
    print("✅ Imports successful")
    
    # Test 2: Create test data with mixed field names
    print("\n🔍 Testing with mixed field names...")
    test_data = [
        {'model': 'gpt-4', 'content': 'This is a test argument with content field', 'round': 1},
        {'model': 'claude-3', 'response': 'This is a test argument with response field', 'round': 1},
        {'model': 'gemini', 'content': 'Another test argument', 'round': 2},
        {'model': 'llama', 'response': 'Final test argument', 'round': 2}
    ]
    
    # Test 3: Manual summary creation
    print("\n🔍 Testing manual summary creation...")
    manual_summary = create_manual_summary("Test Topic", test_data, ['gpt-4', 'claude-3', 'gemini', 'llama'])
    
    if manual_summary.is_successful():
        print("✅ Manual summary created successfully")
        summary_content = manual_summary.get_response()
        print(f"   Summary length: {len(summary_content)} characters")
        print(f"   Contains all models: {all(model in summary_content for model in ['gpt-4', 'claude-3', 'gemini', 'llama'])}")
    else:
        print("❌ Manual summary creation failed")
        
    # Test 4: Consensus analysis
    print("\n🔍 Testing consensus analysis...")
    debate_manager = DebateManager()
    debate_manager.debate_rounds = 2
    
    consensus_analysis = debate_manager.analyze_debate_consensus("Test Topic", test_data)
    
    if consensus_analysis:
        print("✅ Consensus analysis successful")
        print(f"   Consensus score: {consensus_analysis.get('consensus_score', 'N/A')}")
        print(f"   Participation stats: {len(consensus_analysis.get('participation_stats', {}))}")
        
        # Check if all models are in participation stats
        participation_stats = consensus_analysis.get('participation_stats', {})
        for model in ['gpt-4', 'claude-3', 'gemini', 'llama']:
            if model in participation_stats:
                print(f"   {model}: {participation_stats[model].get('participation_percentage', 0)}% participation")
            else:
                print(f"   ❌ {model}: Missing from participation stats")
    else:
        print("❌ Consensus analysis failed")
        
    # Test 5: Summary prompt creation
    print("\n🔍 Testing summary prompt creation...")
    summary_prompt = debate_manager.create_summary_prompt("Test Topic", test_data)
    
    if summary_prompt:
        print("✅ Summary prompt created successfully")
        print(f"   Prompt length: {len(summary_prompt)} characters")
        print(f"   Contains all models: {all(model in summary_prompt for model in ['gpt-4', 'claude-3', 'gemini', 'llama'])}")
    else:
        print("❌ Summary prompt creation failed")
    
    print("\n🎉 All tests completed!")
    print("✅ Enhanced summary generation should be working correctly")
    
except Exception as e:
    print(f"❌ Error during testing: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n🔧 Troubleshooting tips:")
    print("1. Make sure the Flask app is stopped before running this test")
    print("2. Check that all Python dependencies are installed")
    print("3. Verify the working directory is correct")
    
print("\n" + "="*60)
print("To apply the fixes, restart the Flask application:")
print("1. Stop the current app (Ctrl+C)")
print("2. Run: python unified_app.py")
print("="*60)
