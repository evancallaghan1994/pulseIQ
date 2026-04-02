"""
pytest configuration — adds project root to sys.path so all internal imports resolve.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
