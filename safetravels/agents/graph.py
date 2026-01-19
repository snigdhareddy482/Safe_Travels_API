"""
SafeTravels Agents - RAG Graph
==============================

This module implements a stateful RAG agent using LangGraph.
Unlike a simple linear chain, this agent can:
1. Retrieve documents
2. Self-assess relevance (Grading)
3. Rewrite queries if retrieval quality is low
4. Generate final answers

Flow:
[Start] -> [Retrieve] -> [Grade Documents] -> [Decide]
                           |                      |
                    (All Irrelevant)        (Has Relevant)
                           |                      |
                           v                      v
                    [Transform Query]       [Generate]
                           |                      |
                           v                      v
                       [Retrieve]              [End]

Author: SafeTravels Team
Created: January 2026
"""

from typing import TypedDict, List, Dict, Any, Annotated
import operator
import logging

# LangGraph imports
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Fallback for dev environment without package installed
    StateGraph = None
    END = "end"

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Project imports
from safetravels.rag.vector_store import get_vector_store
from safetravels.core.app_settings import settings

logger = logging.getLogger(__name__)

# =============================================================================
# STATE DEFINITION
# =============================================================================

class AgentState(TypedDict):
    """
    The state of the agent graph.
    Passes data between nodes.
    """
    question: str
    generation: str
    documents: List[str]
    retrieval_count: int
    loop_count: int

# =============================================================================
# NODES
# =============================================================================

def retrieve(state: AgentState) -> AgentState:
    """
    Retrieve documents from vector store.
    """
    question = state["question"]
    logger.info(f"---RETRIEVE--- Query: {question}")
    
    store = get_vector_store()
    # Simple semantic search using the existing store
    results = store.query(question, n_results=3)
    documents = results.get("documents", [])
    
    return {
        "documents": documents,
        "question": question,
        "retrieval_count": state.get("retrieval_count", 0) + 1
    }

def grade_documents(state: AgentState) -> AgentState:
    """
    Determines whether the retrieved documents are relevant to the question.
    (Simplified logic for demo: assumes all retrieved docs are 'relevant' enough
    unless empty, in a real system we'd use an LLM grader).
    """
    logger.info("---CHECK RELEVANCE---")
    
    # Mock grading logic: if we found docs, they are relevant.
    # In production, use LLM to score relevance.
    docs = state["documents"]
    
    if not docs:
        logger.warning("No documents found - marking for query rewrite")
        # Optimization: In a real system, we'd flag this to trigger 'transform_query'
        
    return {"documents": docs, "question": state["question"]}

def generate(state: AgentState) -> AgentState:
    """
    Generate answer using the retrieved documents.
    """
    logger.info("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    # Use RAG Chain to generate real answer
    from safetravels.rag.chain import get_rag_chain, QUERY_PROMPT
    
    rag_chain = get_rag_chain()
    
    # Format context
    formatted_docs = []
    for i, doc in enumerate(documents):
        formatted_docs.append(f"[Document {i+1}]\n{doc}\n")
    context = "\n".join(formatted_docs)
    
    # Generate using real LLM
    try:
        if rag_chain.client:
            prompt = QUERY_PROMPT.format(query=question, context=context)
            generation = rag_chain._call_llm(prompt)
        else:
            generation = f"LLM Unavailable (Mock mode). Context: {context[:200]}..."
            
    except Exception as e:
        logger.error(f"Generation error: {e}")
        generation = "Error generating response."

    return {"documents": documents, "question": question, "generation": generation}

def transform_query(state: AgentState) -> AgentState:
    """
    Transform the query to produce a better question.
    """
    logger.info("---TRANSFORM QUERY---")
    question = state["question"]
    
    # Simple rewrite strategy
    new_question = f"{question} cargo theft statistics"
    
    return {"question": new_question, "loop_count": state.get("loop_count", 0) + 1}

# =============================================================================
# EDGES / LOGIC
# =============================================================================

def decide_to_generate(state: AgentState) -> str:
    """
    Determines whether to generate an answer or re-generate a question.
    """
    logger.info("---DECIDE FLOW---")
    
    # Retrieve documents
    documents = state["documents"]
    loop_count = state.get("loop_count", 0)
    
    # Basic condition: If we have docs OR we've retried too many times, generate.
    if documents or loop_count > 1:
        logger.info("Decision: GENERATE")
        return "generate"
    else:
        logger.info("Decision: TRANSFORM QUERY")
        return "transform_query"

# =============================================================================
# GRAPH BUILDER
# =============================================================================

def build_graph():
    """
    Build and compile the LangGraph agent.
    """
    if StateGraph is None:
        logger.error("LangGraph not installed.")
        return None

    workflow = StateGraph(AgentState)

    # Define the nodes
    workflow.add_node("retrieve", retrieve)
    workflow.add_node("grade_documents", grade_documents)
    workflow.add_node("generate", generate)
    workflow.add_node("transform_query", transform_query)

    # Build the graph
    workflow.set_entry_point("retrieve")
    
    workflow.add_edge("retrieve", "grade_documents")
    
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "transform_query": "transform_query",
            "generate": "generate",
        },
    )
    
    workflow.add_edge("transform_query", "retrieve")
    workflow.add_edge("generate", END)

    # Compile
    app = workflow.compile()
    return app

# =============================================================================
# MAIN (Test)
# =============================================================================

if __name__ == "__main__":
    import pprint
    
    print("Initializing Graph Agent...")
    app = build_graph()
    
    if app:
        print("Running Risk Assessment Query...")
        inputs = {"question": "Is Dallas safe for cargo?", "loop_count": 0}
        
        for output in app.stream(inputs):
            for key, value in output.items():
                print(f"Node '{key}':")
                # print(value) # Uncomment to see full state
        
        print("\nFinal Result:")
        print("Flow completed successfully.")
    else:
        print("Failed to build graph (missing dependency?)")
