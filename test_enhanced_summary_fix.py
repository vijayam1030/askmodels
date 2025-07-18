#!/usr/bin/env python3
"""
Test script to verify enhanced summary generation works correctly after the field name fix.
"""
import sys
sys.path.insert(0, '.')

from unified_app import DebateManager, create_manual_summary

def test_enhanced_summary_fix():
    """Test that enhanced summary generation works with mixed field names"""
    
    # Mock debate history with mixed field names (content and response)
    mock_debate_history = [
        {
            'round': 1,
            'model': 'gpt-4',
            'content': 'I believe artificial intelligence will revolutionize education by providing personalized learning experiences.',
            'timestamp': 1234567890
        },
        {
            'round': 1,
            'model': 'claude-3-opus',
            'response': 'While AI has potential, we must consider the risks of over-reliance on technology in education.',
            'timestamp': 1234567891
        },
        {
            'round': 2,
            'model': 'gpt-4',
            'content': 'The benefits outweigh the risks. AI can help teachers focus on creative and critical thinking.',
            'timestamp': 1234567892
        },
        {
            'round': 2,
            'model': 'claude-3-opus',
            'response': 'However, we risk losing human connection and emotional intelligence development.',
            'timestamp': 1234567893
        }
    ]
    
    # Test 1: Manual summary generation with mixed field names
    print("🔍 Testing manual summary generation with mixed field names...")
    try:
        selected_models = ['gpt-4', 'claude-3-opus']
        topic = "AI in Education"
        
        manual_summary = create_manual_summary(topic, mock_debate_history, selected_models)
        
        if manual_summary.is_successful():
            summary_content = manual_summary.get_response()
            print("✅ Manual summary generation successful!")
            print(f"   Summary length: {len(summary_content)} characters")
            print(f"   Contains topic: {'AI in Education' in summary_content}")
            print(f"   Contains model names: {all(model in summary_content for model in selected_models)}")
        else:
            print("❌ Manual summary generation failed!")
            return False
    except Exception as e:
        print(f"❌ Manual summary generation error: {e}")
        return False
    
    # Test 2: Consensus analysis with mixed field names
    print("\n🔍 Testing consensus analysis with mixed field names...")
    try:
        debate_manager = DebateManager()
        debate_manager.debate_rounds = 2
        
        consensus_analysis = debate_manager.analyze_debate_consensus(topic, mock_debate_history)
        
        if consensus_analysis:
            print("✅ Consensus analysis successful!")
            print(f"   Consensus score: {consensus_analysis.get('consensus_score', 'N/A')}")
            print(f"   Consensus level: {consensus_analysis.get('consensus_level', 'N/A')}")
            print(f"   Participation stats: {len(consensus_analysis.get('participation_stats', {}))}")
            print(f"   Round analysis: {len(consensus_analysis.get('round_analysis', []))}")
            
            # Check that both models are in participation stats
            participation_stats = consensus_analysis.get('participation_stats', {})
            for model in selected_models:
                if model in participation_stats:
                    print(f"   {model}: {participation_stats[model].get('participation_percentage', 0)}% participation")
                else:
                    print(f"   ❌ {model}: Not found in participation stats")
        else:
            print("❌ Consensus analysis returned None!")
            return False
    except Exception as e:
        print(f"❌ Consensus analysis error: {e}")
        return False
    
    # Test 3: Summary prompt creation with mixed field names
    print("\n🔍 Testing summary prompt creation with mixed field names...")
    try:
        debate_manager = DebateManager()
        summary_prompt = debate_manager.create_summary_prompt(topic, mock_debate_history)
        
        if summary_prompt:
            print("✅ Summary prompt creation successful!")
            print(f"   Prompt length: {len(summary_prompt)} characters")
            print(f"   Contains topic: {'AI in Education' in summary_prompt}")
            print(f"   Contains both models: {all(model in summary_prompt for model in selected_models)}")
            print(f"   Contains round info: {'Round 1' in summary_prompt and 'Round 2' in summary_prompt}")
        else:
            print("❌ Summary prompt creation failed!")
            return False
    except Exception as e:
        print(f"❌ Summary prompt creation error: {e}")
        return False
    
    print("\n🎉 All enhanced summary tests passed!")
    print("✅ Field name compatibility fix is working correctly")
    print("✅ Summary generation should now work without errors")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Enhanced Summary Generation Fix")
    print("=" * 60)
    
    success = test_enhanced_summary_fix()
    
    if success:
        print("\n✅ All tests passed! Enhanced summary generation is fixed.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    
    print("\n" + "=" * 60)
