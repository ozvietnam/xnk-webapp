#!/bin/bash
set -e

echo "=== XNK Webapp Init ==="

# Step 1: Check dependencies
for cmd in python3 node npm; do
  command -v $cmd >/dev/null 2>&1 || { echo "ERROR: $cmd not found"; exit 1; }
done
echo "✓ Dependencies OK"

# Step 2: Check backend env
if [ ! -f backend/.env ]; then
  echo "ERROR: backend/.env not found. Copy backend/.env.example and fill values."
  exit 1
fi
echo "✓ backend/.env found"

# Step 3: Backend
echo "→ Starting backend..."
cd backend
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -r requirements.txt -q
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Step 4: Frontend
echo "→ Starting frontend..."
cd frontend
npm install -q
npm run dev &
FRONTEND_PID=$!
cd ..

# Step 5: Health checks
sleep 5
echo "→ Health checks..."
curl -sf http://localhost:8000/health && echo "✓ Backend OK" || echo "✗ Backend failed"
curl -sf http://localhost:3000 && echo "✓ Frontend OK" || echo "✗ Frontend failed"

echo ""
echo "=== Services running ==="
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "PIDs: backend=$BACKEND_PID frontend=$FRONTEND_PID"
echo "Stop: kill $BACKEND_PID $FRONTEND_PID"
