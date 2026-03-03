"""Configuration module for the Medical RAG system."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge_base"
SAMPLE_REPORTS_DIR = DATA_DIR / "sample_reports"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 10

CONFIDENCE_THRESHOLD = 0.7
MAX_ELIMINATION_ROUNDS = 5
CRITICAL_ALERT_THRESHOLD = 0.9
