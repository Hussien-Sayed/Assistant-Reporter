#!/usr/bin/env python3
"""Script to list all available Groq models."""

import os
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root))

from dotenv import load_dotenv
from groq import Groq

# Load .env file
load_dotenv(repo_root / ".env")

def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY not found in environment variables")
        sys.exit(1)

    client = Groq(api_key=api_key)
    
    print("Fetching available Groq models...")
    models = client.models.list()
    
    print(f"\nFound {len(models.data)} models:\n")
    
    for model in models.data:
        print(f"ID: {model.id}")
        print(f"  Object: {model.object}")
        print(f"  Owned by: {model.owned_by}")
        print(f"  Active: {model.active}")
        if hasattr(model, 'context_window'):
            print(f"  Context window: {model.context_window}")
        print()

if __name__ == "__main__":
    main()
