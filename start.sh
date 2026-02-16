#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    # Kill all child processes of this script
    pkill -P $$
    exit 0
}

# Trap SIGINT (Ctrl+C) and call cleanup
trap cleanup SIGINT EXIT

echo "🚀 Starting Bookmark RAG Tool..."

# Start Backend in the background
echo "👉 Starting Backend (port 8000)..."
source venv/bin/activate
python run.py &

# Wait a moment for backend to initialize
sleep 2

# Start Frontend in the foreground
echo "👉 Starting Frontend (port 5173)..."
cd frontend
npm run dev
