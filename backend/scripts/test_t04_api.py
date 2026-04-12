#!/usr/bin/env python3
"""
test_t04_api.py — Verify T04 HS Search service directly (no HTTP server needed).

Tests search_hs_codes() RPC and get_by_code() via Supabase client.
Usage:
    cd backend && python3 scripts/test_t04_api.py
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from app.services.hs_search import search, get_by_code

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


async def main():
    print("XNK Webapp — T04 HS Search Service Test")
    print("=" * 50)

    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    all_ok = True

    # Test cases: (query, expected_code_prefix, description)
    test_cases = [
        ("điện thoại",    "8517",     "Phone search (Vietnamese)"),
        ("máy tính",      "8471",     "Computer search (Vietnamese)"),
        ("thép",          "7210",     "Steel search (Vietnamese)"),
        ("nhựa",          "3923",     "Plastic search (Vietnamese)"),
        ("8517",          "8517",     "Code prefix search"),
        ("laptop",        "8471",     "English keyword search"),
        ("smartphone",    "8517",     "English keyword (phone)"),
    ]

    print("\n--- search() via RPC ---")
    for query, expected_prefix, desc in test_cases:
        results = await search(db, query, limit=5)
        if results:
            top = results[0]
            score = f"{top.similarity_score:.3f}" if top.similarity_score is not None else "N/A"
            match = "✓" if top.code.startswith(expected_prefix) else "⚠"
            print(f"  {match} '{query}': {top.code} ({score}) — {desc}")
            if top.code.startswith(expected_prefix) is False:
                print(f"      Expected prefix {expected_prefix}, got {top.code}")
        else:
            print(f"  ✗ '{query}': NO RESULTS — {desc}")
            all_ok = False

    print("\n--- get_by_code() exact match ---")
    exact_tests = [
        ("8517.12.00", True,  "Điện thoại thông minh"),
        ("8471.30.00", True,  "Laptop"),
        ("9999.99.99", False, "Non-existent code"),
    ]
    for code, should_exist, label in exact_tests:
        result = await get_by_code(db, code)
        if should_exist:
            if result:
                print(f"  ✓ {code}: {result.description_vi[:40]}")
            else:
                print(f"  ✗ {code}: NOT FOUND (expected to exist)")
                all_ok = False
        else:
            if result is None:
                print(f"  ✓ {code}: correctly returns None")
            else:
                print(f"  ✗ {code}: should not exist but got result")
                all_ok = False

    print(f"\n{'='*50}")
    if all_ok:
        print("✓ T04 PASSED — HS Search service working")
        sys.exit(0)
    else:
        print("✗ T04 PARTIAL — some tests failed (check above)")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
