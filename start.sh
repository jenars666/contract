#!/bin/bash
set -e

echo "Starting SmartPatch..."

if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Install Python 3.10+"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Node not found. Install Node.js 18+"
    exit 1
fi

cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
pip install solc-select -q
solc-select install 0.8.19
solc-select use 0.8.19

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env — please add your ANTHROPIC_API_KEY"
fi

uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

cd ../frontend
npm install -q
npm run dev &
FRONTEND_PID=$!

echo ""
echo "SmartPatch is running!"
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
