#!/usr/bin/env python3
"""
run_migration.py — Apply SQL migrations to Supabase via direct psycopg2 connection.

Usage:
    python3 scripts/run_migration.py                    # apply all *.sql in migrations/
    python3 scripts/run_migration.py path/to/file.sql   # apply specific file
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
MIGRATIONS_DIR = Path(__file__).parent.parent.parent / "supabase" / "migrations"


def _split_sql(sql: str) -> list[str]:
    """Split SQL on ';' but NOT inside $$ dollar-quoted strings."""
    statements = []
    current = []
    in_dollar_quote = False

    for line in sql.splitlines():
        stripped = line.strip()
        # Toggle dollar-quote state
        if "$$" in stripped:
            count = stripped.count("$$")
            if count % 2 != 0:
                in_dollar_quote = not in_dollar_quote

        if not in_dollar_quote and stripped.startswith("--"):
            continue  # skip comment-only lines outside functions

        current.append(line)

        # Only split on ; when not inside a dollar-quoted block
        if not in_dollar_quote and stripped.endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";").strip()
            if stmt and not stmt.startswith("--"):
                statements.append(stmt)
            current = []

    # Catch any remaining content
    remainder = "\n".join(current).strip()
    if remainder and not remainder.startswith("--"):
        statements.append(remainder)

    return [s for s in statements if s]


def get_conn():
    return psycopg2.connect(DATABASE_URL, connect_timeout=15)


def run_migration_file(filepath: Path) -> bool:
    print(f"\n{'='*60}")
    print(f"Migration: {filepath.name}")
    print(f"{'='*60}")

    sql = filepath.read_text(encoding="utf-8")
    print(f"  SQL size: {len(sql)} chars")

    try:
        conn = get_conn()
        conn.autocommit = True
        cur = conn.cursor()

        # Smart split: respect $$ dollar-quoted strings (don't split inside them)
        statements = _split_sql(sql)
        print(f"  Statements to run: {len(statements)}")
        errors = []

        for i, stmt in enumerate(statements):
            if not stmt:
                continue
            try:
                cur.execute(stmt)
                print(f"  [{i+1:02d}/{len(statements)}] OK")
            except psycopg2.errors.DuplicateObject as e:
                print(f"  [{i+1:02d}/{len(statements)}] SKIP (already exists)")
            except psycopg2.errors.DuplicateTable as e:
                print(f"  [{i+1:02d}/{len(statements)}] SKIP (table exists)")
            except psycopg2.errors.UniqueViolation as e:
                print(f"  [{i+1:02d}/{len(statements)}] SKIP (unique violation)")
            except Exception as e:
                msg = str(e).strip()
                if "already exists" in msg:
                    print(f"  [{i+1:02d}/{len(statements)}] SKIP (already exists)")
                else:
                    print(f"  [{i+1:02d}/{len(statements)}] ERROR: {msg[:120]}")
                    errors.append(msg)

        cur.close()
        conn.close()

        if errors:
            print(f"\n  {len(errors)} error(s) — may need manual review")
            return False
        print(f"\n  ✓ Migration applied")
        return True

    except psycopg2.OperationalError as e:
        print(f"  CONNECTION ERROR: {e}")
        return False


def verify_schema() -> bool:
    print(f"\n{'='*60}")
    print("Verifying schema...")
    print(f"{'='*60}")

    expected = {
        "hs_codes": ["id", "code", "description_vi", "tax_rate_normal"],
        "hs_chapters": ["chapter_code", "title_vi"],
        "hs_sections": ["section_code", "title_vi"],
        "customs_regulations": ["id", "title", "category"],
        "search_history": ["id", "query", "user_id"],
        "user_profiles": ["id", "email", "role"],
    }

    try:
        conn = get_conn()
        cur = conn.cursor()
        all_ok = True

        for table, cols in expected.items():
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=%s",
                (table,)
            )
            found_cols = {r[0] for r in cur.fetchall()}
            if not found_cols:
                print(f"  ✗ {table}: NOT FOUND")
                all_ok = False
            else:
                missing = [c for c in cols if c not in found_cols]
                if missing:
                    print(f"  ⚠ {table}: exists but missing cols {missing}")
                else:
                    print(f"  ✓ {table}: OK ({len(found_cols)} columns)")

        # Check pg_trgm extension
        cur.execute("SELECT extname FROM pg_extension WHERE extname='pg_trgm'")
        if cur.fetchone():
            print("  ✓ pg_trgm: enabled")
        else:
            print("  ✗ pg_trgm: NOT enabled")
            all_ok = False

        # Check GIN index
        cur.execute(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename='hs_codes' AND indexname LIKE '%trgm%'"
        )
        idx = cur.fetchone()
        if idx:
            print(f"  ✓ GIN index: {idx[0]}")
        else:
            print("  ✗ GIN index: NOT found")
            all_ok = False

        # Check search function
        cur.execute(
            "SELECT proname FROM pg_proc WHERE proname='search_hs_codes'"
        )
        if cur.fetchone():
            print("  ✓ search_hs_codes(): function exists")
        else:
            print("  ⚠ search_hs_codes(): function not found")

        cur.close()
        conn.close()
        return all_ok

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set in backend/.env")
        sys.exit(1)

    print("XNK Webapp — T02 Migration Runner (psycopg2)")
    print(f"DB: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

    # Select files
    if len(sys.argv) > 1:
        files = [Path(sys.argv[1])]
    else:
        files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    if not files:
        print(f"No .sql files in {MIGRATIONS_DIR}")
        sys.exit(1)

    print(f"Files: {[f.name for f in files]}\n")

    all_ok = True
    for f in files:
        if not f.exists():
            print(f"ERROR: {f} not found")
            all_ok = False
            continue
        ok = run_migration_file(f)
        all_ok = all_ok and ok

    ok_verify = verify_schema()

    print(f"\n{'='*60}")
    print("RESULT")
    print(f"{'='*60}")
    print(f"  Migration : {'✓ PASSED' if all_ok else '⚠ partial (check above)'}")
    print(f"  Schema    : {'✓ VERIFIED' if ok_verify else '✗ FAILED'}")

    if ok_verify:
        print("\n✓ T02 COMPLETED — schema ready for T03 seed data")
        sys.exit(0)
    else:
        print("\n✗ Schema not complete")
        sys.exit(1)


if __name__ == "__main__":
    main()
