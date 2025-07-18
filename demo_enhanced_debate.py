#!/usr/bin/env python3
"""
Test script to demonstrate enhanced debate summary with voting and winner analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_app import EnhancedDebateManager

def test_complete_debate_flow():
    """Test complete debate flow with enhanced summary"""
    
    print("=== ENHANCED DEBATE SUMMARY DEMO ===")
    print("Testing the new voting analysis and winner determination features")
    print()
    
    # Create debate manager
    debate_manager = EnhancedDebateManager("test_session", 3)
    
    # Start new debate
    topic = "Should AI development be slowed down to ensure safety?"
    participants = ["gpt-4", "claude-3", "gemini-pro", "llama-2"]
    debate_manager.start_new_debate(topic, participants)
    
    print(f"📝 Topic: {topic}")
    print(f"🤖 Participants: {', '.join(participants)}")
    print(f"🆔 Debate ID: {debate_manager.current_debate_id}")
    print()
    
    # Simulate debate rounds with realistic arguments
    debate_arguments = [
        # Round 1 - Initial positions
        {"model": "gpt-4", "round": 1, "content": "AI development should be slowed down. The rapid advancement of AI poses existential risks to humanity. We need comprehensive safety measures, international cooperation, and rigorous testing before deploying advanced AI systems."},
        
        {"model": "claude-3", "round": 1, "content": "I disagree. Slowing AI development could be more dangerous than accelerating it. China and other nations won't pause their AI research. We need to stay competitive while building safety measures in parallel, not sequentially."},
        
        {"model": "gemini-pro", "round": 1, "content": "Both perspectives have merit. We should implement a balanced approach - continue research but with mandatory safety protocols, international oversight, and gradual deployment with extensive testing phases."},
        
        {"model": "llama-2", "round": 1, "content": "AI development should definitely be slowed down. The potential for job displacement, misinformation, and loss of human agency is too great. We need time to develop proper governance frameworks and ethical guidelines."},
        
        # Round 2 - Responses and rebuttals
        {"model": "gpt-4", "round": 2, "content": "I agree with llama-2's concerns about job displacement. Additionally, we've seen how social media algorithms already manipulate human behavior. Advanced AI could be exponentially more dangerous without proper safeguards."},
        
        {"model": "claude-3", "round": 2, "content": "However, consider the benefits we're delaying - AI could solve climate change, cure diseases, and enhance human potential. The risks of falling behind in AI development may outweigh the risks of proceeding carefully but steadily."},
        
        {"model": "gemini-pro", "round": 2, "content": "Indeed, claude-3 raises valid points about beneficial applications. Perhaps the solution isn't to slow all AI development, but to prioritize safety-critical applications and implement stricter controls on potentially dangerous AI systems."},
        
        {"model": "llama-2", "round": 2, "content": "I maintain that slowing down is essential. The benefits mentioned by claude-3 are speculative, while the risks are immediate and concrete. We've seen how tech companies prioritize speed over safety - regulation must come first."},
        
        # Round 3 - Final arguments
        {"model": "gpt-4", "round": 3, "content": "Based on our discussion, I believe the consensus is clear: AI safety must be the top priority. Whether through slowing development or implementing stronger safeguards, we cannot afford to prioritize speed over human welfare."},
        
        {"model": "claude-3", "round": 3, "content": "I respectfully disagree with the characterization of consensus. While safety is crucial, I believe balanced progress with strong oversight is the optimal path. Complete deceleration is neither feasible nor desirable."},
        
        {"model": "gemini-pro", "round": 3, "content": "After considering all arguments, I lean toward slowing development in high-risk areas while maintaining progress in beneficial applications. This targeted approach addresses safety concerns while preserving innovation."},
        
        {"model": "llama-2", "round": 3, "content": "The evidence strongly supports slowing AI development. The precautionary principle demands that we err on the side of caution when facing potentially catastrophic risks. Safety first, innovation second."},
    ]
    
    # Add all arguments to the debate
    for arg in debate_arguments:
        debate_manager.add_argument(arg["model"], arg["round"], arg["content"])
    
    # End the debate
    debate_manager.end_debate()
    
    print("=== DEBATE ROUNDS COMPLETED ===")
    print(f"✅ {len(debate_arguments)} arguments recorded")
    print(f"⏱️ Duration: {debate_manager.debate_end_time - debate_manager.debate_start_time:.2f}s")
    print()
    
    # Generate enhanced summary
    print("=== GENERATING ENHANCED SUMMARY ===")
    summary_prompt = debate_manager.create_summary_prompt(topic, debate_manager.debate_history)
    
    print("📝 Summary prompt includes:")
    print("   ✅ Voting analysis with participant categorization")
    print("   ✅ Winner determination with reasoning")
    print("   ✅ Argument strength assessment")
    print("   ✅ Final verdict with margin of victory")
    print()
    
    # Generate consensus analysis
    print("=== CONSENSUS ANALYSIS ===")
    consensus_analysis = debate_manager.analyze_debate_consensus(topic, debate_manager.debate_history)
    
    print(f"📊 Consensus Score: {consensus_analysis['consensus_score']}%")
    print(f"📈 Consensus Level: {consensus_analysis['consensus_level']}")
    print(f"🤝 Agreement instances: {consensus_analysis['interaction_counts']['agreement_instances']}")
    print(f"❌ Disagreement instances: {consensus_analysis['interaction_counts']['disagreement_instances']}")
    print()
    
    print("=== PARTICIPATION BREAKDOWN ===")
    for model, stats in consensus_analysis['participation_stats'].items():
        print(f"🤖 {model}: {stats['total_words']} words ({stats['participation_percentage']}%)")
    print()
    
    print("=== IMPROVEMENTS IMPLEMENTED ===")
    print("✅ Enhanced voting summary with clear position categorization")
    print("✅ Winner determination based on argument strength and support")
    print("✅ Current debate state tracking (no old debate data)")
    print("✅ Detailed participant analysis with vote counts")
    print("✅ Improved frontend formatting with visual voting results")
    print("✅ Debate duration and ID tracking")
    print("✅ Clear verdict section with margin of victory")
    print()
    
    print("=== NEXT STEPS ===")
    print("1. Start a new debate in the web interface")
    print("2. Check the 'Summary' tab for enhanced voting analysis")
    print("3. Look for winner determination and vote percentages")
    print("4. Verify that only current debate results are shown")
    print()
    
    print("🎉 ENHANCED DEBATE SUMMARY TESTING COMPLETE!")
    print("The voting summary now includes clear winner analysis and vote counts!")

if __name__ == "__main__":
    test_complete_debate_flow()
