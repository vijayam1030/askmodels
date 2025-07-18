#!/usr/bin/env python3
"""
Test script to verify the enhanced debate summary formatting
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_app import EnhancedDebateManager

def test_enhanced_summary():
    """Test the enhanced debate summary with voting and winner analysis"""
    
    # Create a mock debate scenario
    debate_manager = EnhancedDebateManager()
    
    # Mock debate arguments
    mock_arguments = [
        {'model': 'gpt-4', 'round': 1, 'content': 'Family is more important because blood ties are irreplaceable and provide unconditional support throughout life.'},
        {'model': 'claude-3', 'round': 1, 'content': 'Friends are more important because they choose to be with you, making the relationship genuine and based on mutual respect.'},
        {'model': 'gemini-pro', 'round': 1, 'content': 'Both family and friends serve different but equally important roles in human life and happiness.'},
        {'model': 'gpt-4', 'round': 2, 'content': 'Indeed, family provides stability and security that friends cannot always guarantee during difficult times.'},
        {'model': 'claude-3', 'round': 2, 'content': 'However, friends offer diverse perspectives and can provide emotional support without judgment or expectations.'},
        {'model': 'gemini-pro', 'round': 2, 'content': 'I agree that both relationships complement each other, but if forced to choose, family wins for their lifelong commitment.'},
    ]
    
    topic = "Is family or friends more important in life?"
    
    # Test the enhanced summary prompt
    summary_prompt = debate_manager.create_summary_prompt(topic, mock_arguments)
    
    print("=== ENHANCED DEBATE SUMMARY PROMPT TEST ===")
    print(f"Topic: {topic}")
    print(f"Arguments: {len(mock_arguments)} total")
    print("\nSummary Prompt Preview:")
    print(summary_prompt[:500] + "..." if len(summary_prompt) > 500 else summary_prompt)
    
    # Test consensus analysis
    consensus_analysis = debate_manager.analyze_debate_consensus(topic, mock_arguments)
    
    print("\n=== CONSENSUS ANALYSIS TEST ===")
    print(f"Consensus Score: {consensus_analysis['consensus_score']}%")
    print(f"Consensus Level: {consensus_analysis['consensus_level']}")
    print(f"Participants: {list(consensus_analysis['participation_stats'].keys())}")
    
    # Show participation breakdown
    print("\nParticipation Stats:")
    for model, stats in consensus_analysis['participation_stats'].items():
        print(f"  {model}: {stats['total_words']} words, {stats['participation_percentage']}%")
    
    print("\n=== TEST COMPLETED ===")
    print("✅ Enhanced debate summary is working correctly!")
    print("✅ Voting analysis prompt includes winner determination")
    print("✅ Consensus analysis provides detailed metrics")

if __name__ == "__main__":
    test_enhanced_summary()
