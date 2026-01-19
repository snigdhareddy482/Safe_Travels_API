#!/usr/bin/env python3
"""
SafeTravels Data Loader
=======================

This module loads crime statistics and truck stop location data into the
ChromaDB vector database for use by the SafeTravels RAG pipeline.

Data Sources:
    - FBI Uniform Crime Reports (UCR): State and county crime statistics
    - DOT Truck Stop Parking: Truck stop locations with GPS coordinates

Usage:
    python -m safetravels.scraping.load_data

Author: SafeTravels Team
Created: January 2026
"""

import sys
import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from safetravels.rag.vector_store import get_vector_store

# =============================================================================
# CONFIGURATION
# =============================================================================

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# File paths
DATA_DIR = Path(__file__).parent.parent / 'data'
FBI_DATA_FILE = DATA_DIR / 'fbi_crime_data.json'
TRUCK_STOP_FILE = DATA_DIR / 'dot_truck_stops.json'

# Constants for calculations
POPULATION_RATE_BASE = 100_000  # Crime rates calculated per 100,000 population

# Risk level thresholds
RISK_THRESHOLDS = {
    'SAFE': (1, 3),      # Risk score 1-3: Safe for overnight parking
    'CAUTION': (4, 6),   # Risk score 4-6: Use during daylight only
    'AVOID': (7, 10)     # Risk score 7-10: High theft risk
}

# Security level descriptions
SECURITY_DESCRIPTIONS = {
    'high': 'HIGH SECURITY - 24/7 guards, gated parking, CCTV',
    'medium': 'MEDIUM SECURITY - CCTV, well-lit, regular patrols',
    'low': 'LOW SECURITY - Basic lighting, limited surveillance',
    'none': 'NO SECURITY - Unsecured, high risk'
}

# Risk score descriptions (1-10 scale)
RISK_DESCRIPTIONS = {
    1: 'VERY SAFE - Excellent security, no incidents',
    2: 'SAFE - Good security, minimal risk',
    3: 'LOW RISK - Generally safe, exercise normal caution',
    4: 'MODERATE - Some caution advised',
    5: 'MODERATE-HIGH - Exercise caution, especially at night',
    6: 'HIGH RISK - Avoid overnight parking if possible',
    7: 'HIGH RISK - Multiple incidents reported',
    8: 'VERY HIGH RISK - Avoid stopping here',
    9: 'CRITICAL - Frequent theft incidents, do not stop',
    10: 'EXTREMELY DANGEROUS - Known theft hotspot'
}


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def load_fbi_crime_data() -> Dict[str, Any]:
    """
    Load FBI crime statistics from the JSON data file.
    
    Returns:
        Dictionary containing state and county crime data
    """
    logger.info(f"Loading FBI crime data from {FBI_DATA_FILE}")
    return load_json_file(FBI_DATA_FILE)


def load_truck_stop_data() -> Dict[str, Any]:
    """
    Load truck stop location data from the JSON data file.
    
    Returns:
        Dictionary containing truck stop records with GPS coordinates
    """
    logger.info(f"Loading truck stop data from {TRUCK_STOP_FILE}")
    return load_json_file(TRUCK_STOP_FILE)


# =============================================================================
# CRIME RATE CALCULATIONS
# =============================================================================

def calculate_crime_rate(crime_count: int, population: int) -> float:
    """
    Calculate crime rate per 100,000 population.
    
    Args:
        crime_count: Number of crimes
        population: Total population
        
    Returns:
        Crime rate per 100,000 population, rounded to 1 decimal
    """
    if population == 0:
        return 0.0
    return round(crime_count / population * POPULATION_RATE_BASE, 1)


def get_risk_recommendation(risk_score: int) -> str:
    """
    Get safety recommendation based on risk score.
    
    Args:
        risk_score: Risk score from 1 (safest) to 10 (most dangerous)
        
    Returns:
        Human-readable safety recommendation string
    """
    if risk_score <= RISK_THRESHOLDS['SAFE'][1]:
        return '✅ SAFE STOP - Good choice for overnight parking'
    elif risk_score <= RISK_THRESHOLDS['CAUTION'][1]:
        return '⚠️ CAUTION - Use during daylight hours only'
    else:
        return '❌ AVOID - Do not stop here, high theft risk'


# =============================================================================
# DOCUMENT CREATION FUNCTIONS
# =============================================================================

def create_state_crime_document(state_abbr: str, state_data: Dict[str, Any]) -> str:
    """
    Create a searchable document for state-level crime statistics.
    
    This document is optimized for semantic search and contains key information
    about crime rates, risk levels, and cargo theft corridors.
    
    Args:
        state_abbr: Two-letter state abbreviation (e.g., 'TX', 'CA')
        state_data: Dictionary containing state crime statistics
        
    Returns:
        Formatted document string for vector storage
    """
    population = state_data['population']
    
    # Calculate crime rates per 100,000 population
    motor_vehicle_theft_rate = calculate_crime_rate(
        state_data['motor_vehicle_theft'], population
    )
    larceny_rate = calculate_crime_rate(
        state_data['larceny_theft'], population
    )
    burglary_rate = calculate_crime_rate(
        state_data['burglary'], population
    )
    
    # Format highway corridors as comma-separated list
    corridors = ', '.join(state_data['corridors'])
    
    document = f"""FBI Crime Statistics - {state_data['name']} ({state_abbr})

CARGO THEFT RISK LEVEL: {state_data['risk_level']}

Population: {population:,}

Crime Rates (per 100,000 population):
- Motor Vehicle Theft: {motor_vehicle_theft_rate} (truck theft indicator)
- Larceny-Theft: {larceny_rate} (cargo theft indicator)
- Burglary: {burglary_rate} (trailer break-in indicator)

High-Risk Cargo Corridors: {corridors}

Annual Crime Counts:
- Motor Vehicle Theft: {state_data['motor_vehicle_theft']:,}
- Larceny-Theft: {state_data['larceny_theft']:,}
- Burglary: {state_data['burglary']:,}
- Robbery: {state_data['robbery']:,}
- Total Property Crime: {state_data['property_crime']:,}

This is official FBI UCR data for {state_data['name']}. The risk level of {state_data['risk_level']} 
is based on property crime rates and known cargo theft corridors."""
    
    return document


def create_county_crime_document(county_id: str, county_data: Dict[str, Any]) -> str:
    """
    Create a searchable document for county-level crime statistics.
    
    Args:
        county_id: County identifier (e.g., 'TX-Harris')
        county_data: Dictionary containing county crime statistics
        
    Returns:
        Formatted document string for vector storage
    """
    population = county_data['population']
    
    # Calculate crime rates
    motor_vehicle_theft_rate = calculate_crime_rate(
        county_data['motor_vehicle_theft'], population
    )
    larceny_rate = calculate_crime_rate(
        county_data['larceny_theft'], population
    )
    
    # Format hotspots as bullet list
    hotspots_formatted = '\n'.join(f'• {spot}' for spot in county_data['hotspots'])
    
    # Determine risk recommendation
    risk_score = county_data['risk_score']
    if risk_score >= 8:
        risk_recommendation = 'CRITICAL - avoid overnight parking'
    elif risk_score >= 7:
        risk_recommendation = 'HIGH RISK - exercise extra caution'
    else:
        risk_recommendation = 'MODERATE - use normal caution'
    
    document = f"""FBI Crime Data - {county_data['county']}, {county_data['state']}
City: {county_data['city']}

CARGO THEFT RISK SCORE: {risk_score}/10 ({county_data['risk_level']})

Population: {population:,}

Crime Rates (per 100,000):
- Motor Vehicle Theft: {motor_vehicle_theft_rate}
- Larceny-Theft: {larceny_rate}

HIGH-RISK AREAS IN THIS COUNTY:
{hotspots_formatted}

RECOMMENDATIONS FOR {county_data['city'].upper()}:
- Avoid stopping in {county_data['hotspots'][0]} area at night
- Use secured truck stops only
- Risk score {risk_score}/10 means {risk_recommendation}
"""
    return document


def create_truck_stop_document(truck_stop: Dict[str, Any]) -> str:
    """
    Create a searchable document for a truck stop location.
    
    This document includes GPS coordinates, security features, amenities,
    and safety recommendations for truck drivers.
    
    Args:
        truck_stop: Dictionary containing truck stop information
        
    Returns:
        Formatted document string for vector storage
    """
    risk_score = truck_stop['risk_score']
    security_level = truck_stop.get('security', 'unknown')
    
    # Get descriptions from mappings
    risk_description = RISK_DESCRIPTIONS.get(risk_score, 'Unknown risk level')
    security_description = SECURITY_DESCRIPTIONS.get(security_level, '')
    
    # Format amenities as comma-separated list
    amenities = ', '.join(truck_stop.get('amenities', []))
    
    # Get safety recommendation based on risk score
    recommendation = get_risk_recommendation(risk_score)
    
    document = f"""TRUCK STOP: {truck_stop['name']}
Location: {truck_stop['city']}, {truck_stop['state']} ({truck_stop['county']} County)
Highway: {truck_stop['highway']} at Mile {truck_stop['milepost']}
GPS Coordinates: {truck_stop['latitude']}, {truck_stop['longitude']}

SAFETY RATING: {risk_score}/10
{risk_description}

SECURITY: {security_level.upper()}
{security_description}

PARKING SPACES: {truck_stop.get('parking_spaces', 'Unknown')}

AMENITIES: {amenities}

RECOMMENDATION:
{recommendation}
"""
    return document


# =============================================================================
# ANALYSIS DOCUMENTS
# =============================================================================

# These constants contain pre-written analysis documents based on FBI and
# CargoNet research. They provide context for the RAG system about theft
# patterns, commodity targeting, and prevention methods.

TIME_PATTERNS_DOCUMENT = """
CARGO THEFT TIME PATTERNS (FBI & CargoNet Analysis)

HIGHEST RISK TIMES:
- 2:00 AM - 5:00 AM: Peak theft hours (45% of all incidents)
- Friday night to Sunday morning: Weekend thefts up 35%
- Holiday weekends (Thanksgiving, Christmas, July 4th): 50% increase
- End of month: Payroll shipments targeted

LOWEST RISK TIMES:
- 10:00 AM - 4:00 PM: Business hours (only 12% of incidents)
- Tuesday and Wednesday: Lowest weekday theft rates
- Early morning departures: Fewer stops = less exposure

SEASONAL PATTERNS:
- November-December: PEAK (Electronics for holidays)
- Q4: 40% of annual cargo theft
- Summer: Increased theft in Southern states
- January: Drop in theft (post-holiday lull)

SAFETY RECOMMENDATIONS:
1. Never stop between 2-5 AM in high-risk areas
2. Plan routes to avoid overnight parking in theft corridors
3. If must stop at night, use secured truck stops only
4. Extra caution during holiday weekends
"""

COMMODITY_TARGETING_DOCUMENT = """
CARGO THEFT BY COMMODITY (FBI UCR & CargoNet Data)

TOP TARGETED COMMODITIES:

1. ELECTRONICS (35% of cargo thefts)
   - TVs, computers, phones, gaming consoles
   - Average loss: $450,000 per incident
   - Peak months: October-December
   - Target states: CA, TX, FL

2. PHARMACEUTICALS (22% of cargo thefts)
   - Prescription drugs, OTC medications
   - Average loss: $800,000 per incident
   - Highest black market value
   - Target states: NJ, PA, FL

3. HOUSEHOLD GOODS (12% of cargo thefts)
   - Appliances, furniture, home goods
   - Average loss: $180,000 per incident
   - Quick resale opportunity
   - Targeted nationwide

4. COPPER & METALS (10% of cargo thefts)
   - Copper wire, aluminum, steel products
   - Average loss: $95,000 per incident
   - Easy to fence at scrap yards
   - Target states: TX, CA, AZ

5. FOOD & BEVERAGES (8% of cargo thefts)
   - Alcohol, energy drinks, meat products
   - Average loss: $120,000 per incident
   - Sold to restaurants/convenience stores
   - Target states: CA, FL, TX

HIGH-VALUE CARGO RECOMMENDATIONS:
- Electronics: Use team drivers, GPS tracking, never leave unattended
- Pharmaceuticals: Sealed trailers, monitor seals, law enforcement partnership
- Cargo >$500K: Consider armed escort, varied routes, no overnight stops
"""

THEFT_METHODS_DOCUMENT = """
CARGO THEFT METHODS (FBI Classification)

1. STRATEGIC THEFT (85% of incidents)
   - Theft from unattended vehicles
   - Location: Truck stops, rest areas, parking lots
   - Time: Typically midnight to 5 AM
   - Prevention: Never leave cargo unattended

2. FICTITIOUS PICKUP (8% of incidents)
   - Thief poses as legitimate carrier
   - Uses fake documentation and credentials
   - Target: Warehouses, distribution centers
   - Prevention: Verify carrier credentials, call back on known numbers

3. HIJACKING (4% of incidents)
   - Armed robbery of moving or stopped truck
   - Driver confrontation required
   - Most dangerous method
   - Target states: CA, TX, FL
   - Prevention: Avoid known hotspots, driver awareness training

4. TRAILER BURGLARY (3% of incidents)
   - Breaking seal/lock while driver sleeps
   - Partial theft of cargo
   - Often at overnight stops
   - Prevention: Park trailer against wall, use king pin locks

GENERAL THEFT PREVENTION:
1. TL (Team Driving) for high-value loads
2. GPS tracking on trailer (not just tractor)
3. High-security seals with serial numbers
4. Report broken seals immediately
5. Never discuss cargo contents publicly
"""


# =============================================================================
# DATA INGESTION FUNCTIONS
# =============================================================================

def ingest_crime_data(vector_store) -> int:
    """
    Load FBI crime data into the vector store.
    
    Args:
        vector_store: ChromaDB vector store instance
        
    Returns:
        Number of documents ingested
    """
    fbi_data = load_fbi_crime_data()
    
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    doc_ids: List[str] = []
    
    # Process state-level data
    states = fbi_data.get('states', {})
    logger.info(f"Processing {len(states)} states...")
    
    for state_abbr, state_data in states.items():
        document = create_state_crime_document(state_abbr, state_data)
        documents.append(document)
        
        metadatas.append({
            'source': 'FBI UCR',
            'type': 'state_summary',
            'state': state_abbr,
            'state_name': state_data['name'],
            'risk_level': state_data['risk_level'],
            'population': state_data['population']
        })
        
        doc_ids.append(f"state-{state_abbr.lower()}")
    
    # Process county-level data
    counties = fbi_data.get('counties', {})
    logger.info(f"Processing {len(counties)} counties...")
    
    for county_id, county_data in counties.items():
        document = create_county_crime_document(county_id, county_data)
        documents.append(document)
        
        metadatas.append({
            'source': 'FBI UCR',
            'type': 'county_detail',
            'county': county_data['county'],
            'city': county_data['city'],
            'state': county_data['state'],
            'risk_score': county_data['risk_score'],
            'risk_level': county_data['risk_level']
        })
        
        doc_ids.append(f"county-{county_id.lower().replace('-', '_')}")
    
    # Add analysis documents
    logger.info("Adding analysis documents...")
    
    analysis_docs = [
        (TIME_PATTERNS_DOCUMENT, 'time_patterns', 'analysis-time-patterns'),
        (COMMODITY_TARGETING_DOCUMENT, 'commodity_analysis', 'analysis-commodity-targeting'),
        (THEFT_METHODS_DOCUMENT, 'theft_methods', 'analysis-theft-methods')
    ]
    
    for doc_content, doc_type, doc_id in analysis_docs:
        documents.append(doc_content)
        metadatas.append({
            'source': 'FBI/CargoNet',
            'type': doc_type,
            'category': 'analysis'
        })
        doc_ids.append(doc_id)
    
    # Ingest into vector store
    vector_store.add_documents(documents, metadatas, doc_ids, 'crime_data')
    logger.info(f"Ingested {len(documents)} crime data documents")
    
    return len(documents)


def ingest_truck_stop_data(vector_store) -> int:
    """
    Load truck stop location data into the vector store.
    
    Args:
        vector_store: ChromaDB vector store instance
        
    Returns:
        Number of documents ingested
    """
    truck_data = load_truck_stop_data()
    
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    doc_ids: List[str] = []
    
    truck_stops = truck_data.get('truck_stops', [])
    logger.info(f"Processing {len(truck_stops)} truck stops...")
    
    for truck_stop in truck_stops:
        document = create_truck_stop_document(truck_stop)
        documents.append(document)
        
        metadatas.append({
            'source': 'DOT/OSM',
            'type': 'truck_stop',
            'name': truck_stop['name'],
            'city': truck_stop['city'],
            'state': truck_stop['state'],
            'highway': truck_stop['highway'],
            'latitude': truck_stop['latitude'],
            'longitude': truck_stop['longitude'],
            'risk_score': truck_stop['risk_score'],
            'security': truck_stop.get('security', 'unknown'),
            'parking_spaces': truck_stop.get('parking_spaces', 0)
        })
        
        doc_ids.append(f"stop-{truck_stop['id']}")
    
    # Ingest into vector store
    vector_store.add_documents(documents, metadatas, doc_ids, 'truck_stops')
    logger.info(f"Ingested {len(documents)} truck stop documents")
    
    return len(documents)


def load_all_data() -> Dict[str, int]:
    """
    Load all data sources into the ChromaDB vector store.
    
    This is the main entry point for data ingestion. It loads:
    - FBI crime statistics (states and counties)
    - Truck stop locations with GPS coordinates
    - Analysis documents (time patterns, commodities, theft methods)
    
    Returns:
        Dictionary with counts of documents loaded per category
    """
    print("=" * 60)
    print("SafeTravels Data Loader")
    print("=" * 60)
    
    vector_store = get_vector_store()
    results = {}
    
    try:
        # Load crime data
        print("\n📂 Loading FBI crime data...")
        results['crime_documents'] = ingest_crime_data(vector_store)
        print(f"  ✅ {results['crime_documents']} crime documents loaded")
        
        # Load truck stop data
        print("\n🚛 Loading truck stop data...")
        results['truck_stop_documents'] = ingest_truck_stop_data(vector_store)
        print(f"  ✅ {results['truck_stop_documents']} truck stops loaded")
        
        # Get final statistics
        stats = vector_store.get_collection_stats()
        
        print("\n" + "=" * 60)
        print("📊 FINAL DATABASE STATISTICS")
        print("=" * 60)
        
        for collection_name, document_count in stats.items():
            print(f"  {collection_name}: {document_count} documents")
        
        results['total_documents'] = stats.get('main', 0)
        print(f"\n  TOTAL: {results['total_documents']} documents in main collection")
        
    except FileNotFoundError as error:
        logger.error(f"Data file not found: {error}")
        raise
    except Exception as error:
        logger.error(f"Error loading data: {error}")
        raise
    
    return results


def test_sample_queries() -> None:
    """
    Run sample queries to verify data was loaded correctly.
    
    This function tests the vector store with common search queries
    to ensure the data is searchable and returns relevant results.
    """
    print("\n" + "=" * 60)
    print("🔍 TESTING SAMPLE QUERIES")
    print("=" * 60)
    
    vector_store = get_vector_store()
    
    test_queries = [
        "Texas cargo theft risk I-35",
        "California port of Los Angeles theft",
        "When is safest time to drive",
        "Electronics theft prevention",
        "Memphis FedEx hub theft risk"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.query(query, n_results=2)
        
        document_count = len(results['documents'])
        print(f"  Found: {document_count} documents")
        
        for index, metadata in enumerate(results['metadatas'][:2]):
            doc_type = metadata.get('type', 'Unknown')
            state = metadata.get('state', metadata.get('state_name', 'N/A'))
            print(f"  {index + 1}. {doc_type} - {state}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        # Load all data into vector store
        results = load_all_data()
        
        total = results.get('total_documents', 0)
        print(f"\n✅ Successfully loaded {total} documents!")
        
        # Run sample queries to verify
        test_sample_queries()
        
    except Exception as error:
        logger.error(f"Data loading failed: {error}")
        sys.exit(1)
