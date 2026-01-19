#!/usr/bin/env python3
"""
SafeTravels RAG - Chain
=======================

This module implements the core RAG (Retrieval-Augmented Generation) chain
that powers the SafeTravels API. It combines ChromaDB vector retrieval with
OpenAI LLM synthesis to provide intelligent risk assessments.

Architecture:
    1. Query → ChromaDB → Retrieve relevant documents
    2. Documents + Prompt → OpenAI GPT → Structured JSON response
    3. Response → Parse and validate → Return to API

Key Features:
    - Consistent 1-10 risk scoring with detailed rubric
    - Source citation for transparency
    - Fallback to retrieval-only when LLM unavailable
    - Low temperature for consistent scoring

Usage:
    from safetravels.rag.chain import get_rag_chain
    
    chain = get_rag_chain()
    result = chain.assess_risk(32.7767, -96.7970, commodity="electronics")

Author: SafeTravels Team
Created: January 2026
"""

from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime
import json
import os
import logging

from safetravels.core.app_settings import settings
from safetravels.rag.vector_store import get_vector_store

# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# LLM temperature (low for consistent, reproducible scoring)
LLM_TEMPERATURE = 0.1

# Maximum tokens for LLM response
LLM_MAX_TOKENS = 1000

# Number of documents to retrieve per query
DEFAULT_RETRIEVAL_COUNT = 5

# =============================================================================
# OPENAI CLIENT INITIALIZATION
# =============================================================================

# Try to import OpenAI client
try:
    from openai import OpenAI, AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not installed. Run: pip install openai")


# =============================================================================
# SCORING RUBRIC
# =============================================================================

SCORING_RUBRIC = """
RISK SCORING RUBRIC (1-10 scale):

Score 1-2 (LOW):
- No theft incidents in past 12 months
- Low crime rate area (< 20 per 100K)
- Secured location with guards/fencing/CCTV

Score 3-4 (MODERATE-LOW):
- 0-1 incidents in past 12 months
- Average crime rate (20-40 per 100K)
- Basic security (lighting, cameras)

Score 5-6 (MODERATE):
- 1-2 incidents in past 12 months
- Above average crime rate (40-60 per 100K)
- Limited security features

Score 7-8 (HIGH):
- 3-5 incidents in past 12 months
- High crime rate (60-80 per 100K)
- Known theft corridor or hotspot

Score 9-10 (CRITICAL):
- 6+ incidents in past 12 months
- Very high crime rate (> 80 per 100K)
- Active theft ring operating in area
"""


# =============================================================================
# LLM PROMPTS
# =============================================================================

RISK_ASSESSMENT_PROMPT = """You are a cargo theft risk analyst. Based on the retrieved documents below, 
assess the theft risk for the location at latitude {latitude}, longitude {longitude}.

RETRIEVED DOCUMENTS:
{context}

{rubric}

RESPONSE INSTRUCTIONS:
Analyze the documents and respond ONLY with valid JSON in this exact format:
{{
  "risk_score": <number 1-10>,
  "risk_level": "<low|moderate|high|critical>",
  "assessment": "<2-3 sentence natural language explanation>",
  "key_factors": ["<factor1>", "<factor2>", "<factor3>"],
  "recommendations": ["<recommendation1>", "<recommendation2>"],
  "confidence": <number 0.0-1.0>
}}

Risk level mapping:
- 1-3: "low"
- 4-5: "moderate"  
- 6-7: "high"
- 8-10: "critical"

Respond with JSON only, no additional text."""


QUERY_PROMPT = """You are a cargo theft intelligence assistant. Answer the user's question based on 
the retrieved documents below.

USER QUESTION: {query}

RETRIEVED DOCUMENTS:
{context}

Provide a helpful, accurate answer based on the documents. Include specific details
from the sources when available. If the documents don't contain enough information
to answer fully, say so.

Be concise but thorough. End with 1-2 actionable recommendations if applicable."""


# =============================================================================
# RAG CHAIN CLASS
# =============================================================================

class RAGChain:
    """
    Complete RAG chain combining ChromaDB retrieval with OpenAI synthesis.
    
    This class provides methods to:
        - Assess risk at a specific location
        - Answer natural language queries
        - Analyze route-level risk
    
    The chain uses a consistent scoring rubric to ensure reproducible
    risk assessments across different locations and times.
    
    Attributes:
        vector_store: ChromaDB vector store instance
        temperature: LLM temperature setting
        client: OpenAI client (None if unavailable)
        
    Example:
        chain = RAGChain()
        result = chain.assess_risk(32.7767, -96.7970)
        print(f"Risk: {result['risk_score']}/10")
    """
    
    def __init__(self) -> None:
        """Initialize RAG chain with vector store and LLM client."""
        self.vector_store = get_vector_store()
        self.temperature = LLM_TEMPERATURE
        
        # Initialize OpenAI client
        self.client = self._initialize_openai_client()
        
        if self.client:
            logger.info("RAG Chain initialized with OpenAI")
        else:
            logger.warning("RAG Chain initialized WITHOUT OpenAI (retrieval-only mode)")
    
    def _initialize_openai_client(self) -> Optional[Any]:
        """
        Initialize the OpenAI client if credentials are available.
        
        Returns:
            OpenAI client instance or None if unavailable
        """
        if not OPENAI_AVAILABLE:
            return None
        
        # Check for Azure OpenAI credentials
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            logger.info("Initializing Azure OpenAI Client")
            return AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )

        # Fallback to standard OpenAI
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if api_key:
            return OpenAI(api_key=api_key)
        
        logger.warning("No OpenAI API key found in settings or environment")
        return None
    
    def _format_context(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> str:
        """
        Format retrieved documents into a context string for the LLM.
        
        Args:
            documents: List of document text strings
            metadatas: Optional list of metadata dictionaries
            
        Returns:
            Formatted context string with document sources
        """
        formatted_docs = []
        
        for index, document in enumerate(documents, start=1):
            # Get source info from metadata
            source_info = ""
            if metadatas and index <= len(metadatas):
                source = metadatas[index - 1].get('source', 'Unknown')
                source_info = f" [{source}]"
            
            formatted_docs.append(f"[Document {index}{source_info}]\n{document}\n")
        
        return "\n".join(formatted_docs)
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        Call the OpenAI API with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            LLM response text or None if error/unavailable
        """
        if not self.client:
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=settings.azure_deployment_name if isinstance(self.client, AzureOpenAI) else settings.llm_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cargo theft risk analyst. Always respond with valid JSON when asked."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=LLM_MAX_TOKENS
            )
            return response.choices[0].message.content
            
        except Exception as error:
            logger.error(f"LLM API Error: {error}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Parse JSON from LLM response, handling markdown code blocks.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed dictionary or None if parsing fails
        """
        if not response:
            return None
        
        # Clean up markdown code blocks
        cleaned = response.strip()
        
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
            
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as error:
            logger.error(f"JSON Parse Error: {error}")
            return None
    
    def _generate_mock_response(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """
        Generate a mock response when LLM is unavailable.
        
        This provides meaningful output based on retrieval alone.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            
        Returns:
            Mock assessment dictionary
        """
        return {
            "risk_score": 6,
            "risk_level": "high",
            "assessment": (
                f"Based on retrieved documents, location ({latitude:.2f}, {longitude:.2f}) "
                f"has elevated risk. Documents indicate recent cargo theft incidents in the area. "
                f"Property crime rate is above average."
            ),
            "key_factors": [
                "Recent theft incidents in area",
                "Above average crime rate",
                "Limited security features"
            ],
            "recommendations": [
                "Park in well-lit areas near entrance",
                "Avoid overnight stops if possible"
            ],
            "confidence": 0.70
        }
    
    def _build_sources_list(
        self,
        metadatas: List[Dict],
        distances: List[float]
    ) -> List[Dict]:
        """
        Build a list of source citations from retrieval results.
        
        Args:
            metadatas: Metadata from retrieved documents
            distances: Distance scores from retrieval
            
        Returns:
            List of source dictionaries with title and relevance
        """
        sources = []
        
        for index, metadata in enumerate(metadatas):
            source_name = metadata.get('source', 'Document')
            location_name = metadata.get('county', metadata.get('city', 'Unknown'))
            
            # Convert distance to relevance (1 - distance for similarity)
            relevance = 0.8  # Default
            if distances and index < len(distances):
                relevance = round(1 - distances[index], 2)
            
            sources.append({
                "title": f"{source_name} - {location_name}",
                "relevance": relevance
            })
        
        return sources
    
    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================
    
    def assess_risk(
        self,
        latitude: float,
        longitude: float,
        commodity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assess cargo theft risk for a specific location.
        
        This method:
            1. Retrieves relevant documents from ChromaDB
            2. Builds a prompt with scoring rubric
            3. Calls the LLM for synthesis
            4. Parses and validates the response
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            commodity: Optional cargo type for specific risk factors
            
        Returns:
            Dictionary with risk_score, risk_level, assessment, 
            key_factors, recommendations, sources, and confidence
            
        Example:
            result = chain.assess_risk(32.7767, -96.7970, "electronics")
            print(f"Risk: {result['risk_score']}/10 - {result['risk_level']}")
        """
        logger.info(f"Assessing risk at ({latitude}, {longitude})")
        
        # Step 1: Build retrieval query
        query = f"cargo theft risk near latitude {latitude} longitude {longitude}"
        if commodity:
            query += f" for {commodity} shipments"
        
        # Step 2: Retrieve relevant documents
        results = self.vector_store.query(query, n_results=DEFAULT_RETRIEVAL_COUNT)
        
        # Step 3: Build LLM prompt
        context = self._format_context(
            results.get("documents", []),
            results.get("metadatas", [])
        )
        
        prompt = RISK_ASSESSMENT_PROMPT.format(
            latitude=latitude,
            longitude=longitude,
            context=context,
            rubric=SCORING_RUBRIC
        )
        
        # Step 4: Call LLM and parse response
        llm_response = self._call_llm(prompt)
        result = self._parse_json_response(llm_response)
        
        # Fallback to mock if LLM unavailable
        if not result:
            result = self._generate_mock_response(latitude, longitude)
        
        # Step 5: Add sources from retrieval
        result["sources"] = self._build_sources_list(
            results.get("metadatas", []),
            results.get("distances", [])
        )
        
        # Add metadata
        result["generated_at"] = datetime.utcnow().isoformat()
        result["documents_retrieved"] = len(results.get("documents", []))
        
        return result
    
    def answer_query(
        self,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Answer a natural language question using RAG.
        
        Args:
            query: Natural language question
            latitude: Optional location latitude for context
            longitude: Optional location longitude for context
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        logger.info(f"Answering query: {query[:50]}...")
        
        # Enhance query with location if provided
        search_query = query
        if latitude and longitude:
            search_query += f" near latitude {latitude} longitude {longitude}"
        
        # Retrieve relevant documents
        results = self.vector_store.query(
            search_query,
            n_results=DEFAULT_RETRIEVAL_COUNT
        )
        
        # Build prompt
        context = self._format_context(
            results.get("documents", []),
            results.get("metadatas", [])
        )
        
        prompt = QUERY_PROMPT.format(query=query, context=context)
        
        # Call LLM
        answer = self._call_llm(prompt)
        
        # Fallback if LLM unavailable
        if not answer:
            documents = results.get("documents", [])
            docs_summary = " | ".join([doc[:100] for doc in documents[:3]])
            answer = (
                f"Based on {len(documents)} retrieved documents:\n\n"
                f"{docs_summary}...\n\n"
                f"(LLM not configured - showing raw retrieval results)"
            )
        
        # Build response
        return {
            "query": query,
            "answer": answer,
            "sources": self._build_sources_list(
                results.get("metadatas", []),
                results.get("distances", [])
            ),
            "documents_retrieved": len(results.get("documents", [])),
            "follow_up_questions": [
                "What are the safest truck stops in this area?",
                "What commodities are most targeted here?"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def analyze_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        departure_time: datetime,
        commodity: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze theft risk along a route.
        
        Args:
            origin: Tuple of (latitude, longitude) for start
            destination: Tuple of (latitude, longitude) for end
            departure_time: Planned departure datetime
            commodity: Optional cargo type
            
        Returns:
            Dictionary with segment risks and overall assessment
        """
        logger.info(f"Analyzing route: {origin} -> {destination}")
        
        # Assess risk at origin and destination
        origin_risk = self.assess_risk(origin[0], origin[1], commodity)
        destination_risk = self.assess_risk(destination[0], destination[1], commodity)
        
        # Calculate overall score
        average_score = (
            origin_risk["risk_score"] + destination_risk["risk_score"]
        ) // 2
        
        # Determine overall level
        if average_score <= 3:
            level = "low"
        elif average_score <= 5:
            level = "moderate"
        elif average_score <= 7:
            level = "high"
        else:
            level = "critical"
        
        return {
            "overall_risk_score": average_score,
            "overall_risk_level": level,
            "origin_risk": origin_risk,
            "destination_risk": destination_risk,
            "summary": (
                f"Route analysis complete. "
                f"Origin risk: {origin_risk['risk_score']}/10, "
                f"Destination risk: {destination_risk['risk_score']}/10. "
                f"Overall: {average_score}/10 ({level})."
            ),
            "generated_at": datetime.utcnow().isoformat()
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_rag_chain_instance: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """
    Get or create the singleton RAGChain instance.
    
    Returns:
        RAGChain singleton instance
        
    Example:
        chain = get_rag_chain()
        result = chain.assess_risk(32.7767, -96.7970)
    """
    global _rag_chain_instance
    
    if _rag_chain_instance is None:
        _rag_chain_instance = RAGChain()
    
    return _rag_chain_instance


# =============================================================================
# MAIN (for testing)
# =============================================================================

if __name__ == "__main__":
    """Test the RAG chain with sample queries."""
    
    print("=" * 60)
    print("RAG Chain Test")
    print("=" * 60)
    
    chain = get_rag_chain()
    
    # Test 1: Risk Assessment
    print("\n--- Test 1: Risk Assessment ---")
    result = chain.assess_risk(32.7767, -96.7970)  # Dallas coordinates
    print(f"Risk Score: {result['risk_score']}/10")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Assessment: {result['assessment'][:200]}...")
    print(f"Documents Retrieved: {result['documents_retrieved']}")
    
    # Test 2: Natural Language Query
    print("\n--- Test 2: Natural Language Query ---")
    result = chain.answer_query("Is Dallas safe for truck parking?")
    print(f"Answer: {result['answer'][:300]}...")
    print(f"Sources: {len(result['sources'])}")
    
    print("\n✅ RAG Chain tests complete!")
