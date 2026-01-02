#!/bin/bash

# Script to run the interactive Shift card game
# Starts the FastAPI server, runs the client, and cleans up

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🎮 Starting Shift Card Game Interactive Mode${NC}"

# Check if uvicorn is installed
if ! python -c "import uvicorn" 2>/dev/null; then
    echo -e "${RED}❌ uvicorn not found. Installing...${NC}"
    pip install uvicorn fastapi requests pydantic
fi

# Start the FastAPI server in the background
echo -e "${YELLOW}🚀 Starting API server...${NC}"
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 > /tmp/shift_game_server.log 2>&1 &
SERVER_PID=$!

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down server...${NC}"
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Server stopped${NC}"
}

# Register cleanup function to run on exit
trap cleanup EXIT INT TERM

# Wait for server to start
echo -e "${YELLOW}⏳ Waiting for server to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Server failed to start. Check /tmp/shift_game_server.log${NC}"
        exit 1
    fi
    sleep 0.5
done

echo -e "${YELLOW}📝 API docs available at: http://localhost:8000/docs${NC}"
echo ""

# Run the client
python api/client.py

# Cleanup happens automatically via trap
