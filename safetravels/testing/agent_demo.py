"""
SafeTravels Agent Example
=========================

This script demonstrates how to use the LangGraph-powered intelligent agent.

Usage:
    python -m safetravels.agents.example
"""

import sys
import logging
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

def run_agent_demo():
    print("=" * 60)
    print("SafeTravels Intelligent Agent Demo")
    print("=" * 60)
    
    try:
        from safetravels.agents.graph import build_graph
    except ImportError as e:
        print(f"\n❌ Error: Could not import graph agent. ({e})")
        print("Please ensure you have installed the dependencies:")
        print("pip install langgraph langchain-openai chromadb")
        return

    # Build the agent
    print("\n1. Building Agent Graph...")
    agent = build_graph()
    
    if not agent:
        print("❌ Failed to build agent. Check dependencies.")
        return
        
    # Run a query
    query = "Is Dallas a high risk area for electronics?"
    print(f"\n2. Running Query: '{query}'")
    
    inputs = {"question": query, "loop_count": 0}
    
    print("\n--- Agent Execution Trace ---")
    try:
        results = []
        for output in agent.stream(inputs):
            for node_name, state in output.items():
                print(f"  ➜ Node Completed: {node_name}")
                results.append((node_name, state))
                
        print("\n3. Execution Complete")
        
        # Get final state
        final_state = results[-1][1] if results else {}
        answer = final_state.get('generation', 'No answer generated.')
        
        print("\n" + "=" * 60)
        print("FINAL ANSWER")
        print("=" * 60)
        print(answer)
        
    except Exception as e:
        print(f"\n❌ Execution Error: {e}")

if __name__ == "__main__":
    run_agent_demo()
