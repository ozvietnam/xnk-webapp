import sys
import os

# Vercel runs this file from /var/task/backend/api/
# We need /var/task/backend/ on the path so `app` package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
