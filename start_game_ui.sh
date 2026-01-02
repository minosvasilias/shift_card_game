#!/bin/bash

# Shift Card Game - Start Frontend and Backend
# This script starts both the FastAPI backend and React frontend

echo "🎮 Starting Shift Card Game..."
echo ""

# Check if Python dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Backend dependencies not found. Installing..."
    pip install -r requirements.txt
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Frontend dependencies not found. Installing..."
    cd frontend && npm install && cd ..
fi

echo "🔧 Starting backend server on http://localhost:8000..."
python3 -m uvicorn api.server:app --reload --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

echo "🎨 Starting frontend server on http://localhost:3000..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Game is starting!"
echo ""
echo "📝 Backend API: http://localhost:8000"
echo "📝 API Docs: http://localhost:8000/docs"
echo "🎮 Game UI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
