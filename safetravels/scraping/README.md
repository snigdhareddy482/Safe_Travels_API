# Scraping & Data Ingestion

This directory handles data acquisition and loading into the system.

## Purpose
- To scrape, fetch, and load data from various sources (FBI, DOT, etc.).
- To ingest data into the ChromaDB vector store.

## Key Files
- `load_data.py`: Main script to load FBI and truck stop data into vector storage.

## Usage
```bash
python -m safetravels.scraping.load_data
```
