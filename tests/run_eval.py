"""Familiar evaluation entry point; delegates to the single evaluator implementation."""
from pathlib import Path
import sys

# A direct script starts with tests/ on sys.path; make the repository package importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate import main

if __name__ == "__main__":
    main()
