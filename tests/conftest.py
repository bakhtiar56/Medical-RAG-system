"""Test configuration and fixtures."""
import sys
from pathlib import Path

# Add project root to sys.path so tests can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))
