#!/usr/bin/env python3
"""CLI runner script for TypeMind AI ML Training and Evaluation Pipeline."""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.train import train_and_evaluate

if __name__ == "__main__":
    print("[TypeMind AI] Starting Machine Learning Pipeline Training & Evaluation...")
    metadata = train_and_evaluate()
    print("[TypeMind AI] Finished successfully!")
