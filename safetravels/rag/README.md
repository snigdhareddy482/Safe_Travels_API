# RAG (Retrieval-Augmented Generation) Module

This directory implements the RAG pipeline for intelligent query answering and risk assessment.

## Purpose
- To retrieve relevant context from the vector database.
- To synthesize answers using Large Language Models (LLMs).

## Key Files
- `vector_store.py`: Interface for ChromaDB interactions.
- `chain.py`: Logic for RAG chain (Retrieval + LLM Generation).

## Structure
- Uses `chromadb` for storage.
- Uses OpenAI (or other LLMs) for generation.
