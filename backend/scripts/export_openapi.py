"""Export FastAPI OpenAPI schema to JSON. Usage: python scripts/export_openapi.py > docs/openapi.json"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app

print(json.dumps(app.openapi(), indent=2, ensure_ascii=False))
