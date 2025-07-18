#!/usr/bin/env python3
"""Test the fast summary generation"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_app import create_manual_summary
import time

def test_fast_summary_generation():
    """Test that summary generation is fast"""
    print("Testing fast summary generation...")
    
    # Mock debate history with more realistic data
    debate_history = [
        {
            'model': 'gpt-4',
            'response': 'I believe artificial intelligence will significantly benefit society by automating routine tasks, improving medical diagnostics, and enhancing educational opportunities. The key is responsible development with proper safeguards.'
        },
        {
            'model': 'claude-3-sonnet',
            'response': 'While AI offers benefits, we must be cautious about potential risks including job displacement, privacy concerns, and the concentration of power in tech companies. Regulation and ethical frameworks are essential.'
        },
        {
            'model': 'gemini-pro',
            'response': 'Both perspectives have merit. AI can indeed revolutionize healthcare and education, but we need proactive measures to address societal challenges. The focus should be on human-AI collaboration rather than replacement.'
        },
        {
            'model': 'gpt-4',
            'response': 'I agree with the collaborative approach. History shows that technological advances create new opportunities even as they disrupt existing jobs. The key is ensuring the benefits are distributed equitably.'
        },
        {
            'model': 'claude-3-sonnet',
            'response': 'True, but the speed of AI advancement is unprecedented. We need robust social safety nets and retraining programs to help workers adapt. The transition period is crucial for societal stability.'
        },
        {
            'model': 'gemini-pro',
            'response': 'Agreed. We should also consider AI governance frameworks that ensure transparency and accountability. International cooperation will be essential to address global challenges posed by AI development.'
        }
    ]
    
    selected_models = ['gpt-4', 'claude-3-sonnet', 'gemini-pro']
    topic = "The Impact of AI on Society: Benefits vs. Risks"
    
    try:
        # Time the manual summary generation
        start_time = time.time()
        summary_response = create_manual_summary(topic, debate_history, selected_models)
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        print(f"✅ Summary generated in {generation_time:.3f} seconds")
        print(f"Success: {summary_response.is_successful()}")
        
        if generation_time < 1.0:
            print("✅ Fast generation - under 1 second!")
        else:
            print("⚠️ Generation took longer than expected")
        
        print("\nSummary preview:")
        print("-" * 50)
        summary_content = summary_response.get_response()
        print(summary_content[:300] + "..." if len(summary_content) > 300 else summary_content)
        print("-" * 50)
        
        return generation_time < 2.0  # Should be under 2 seconds
        
    except Exception as e:
        print(f"❌ Error in fast summary generation: {e}")
        return False

if __name__ == "__main__":
    success = test_fast_summary_generation()
    if success:
        print("\n✅ Fast summary generation test passed!")
    else:
        print("\n❌ Fast summary generation test failed!")
        sys.exit(1)
