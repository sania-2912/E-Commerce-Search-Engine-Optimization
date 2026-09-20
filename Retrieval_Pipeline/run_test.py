"""
CLI Verification for Retrieval Pipeline
Usage: python Retrieval_Pipeline/run_test.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import Retrieval_Pipeline.models.model_loader as ml
from Retrieval_Pipeline.retrieval_pipeline import search

if __name__ == "__main__":
    print("=" * 80)
    print("INITIALIZING RETRIEVAL PIPELINE...")
    print("=" * 80)
    ml.load_all()

    test_queries = ["iPhone 15 Pro", "Samsung Galaxy", "5G mobile phone smartphone"]
    for q in test_queries:
        print(f"\nSearching for: '{q}'")
        res = search(text=q, top_k=5)
        for r in res.get("results", []):
            print(f"  - [{r.get('brand')}] {r.get('product_name')} (Rs. {r.get('discounted_price', 0):,.0f}) | Final Score: {r.get('final_score')}")

    print("\n" + "=" * 80)
    print("RETRIEVAL PIPELINE TEST COMPLETE - SUCCESS!")
    print("=" * 80)
