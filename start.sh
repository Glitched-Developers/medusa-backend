#!/bin/bash
set -e

echo "Starting Medusa Backend + Dashboard..."

# Start backend in background
echo "Starting FastAPI backend on port ${BACKEND_PORT:-8080}..."
python /app/main.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start dashboard
echo "Starting Next.js dashboard on port ${DASHBOARD_PORT:-3000}..."
cd /app/dashboard
HOSTNAME=0.0.0.0 PORT=${DASHBOARD_PORT:-3000} node server.js &
DASHBOARD_PID=$!

# Function to handle shutdown
cleanup() {
    echo "Shutting down services..."
    kill $BACKEND_PID $DASHBOARD_PID 2>/dev/null || true
    wait $BACKEND_PID $DASHBOARD_PID 2>/dev/null || true
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for processes
wait $BACKEND_PID $DASHBOARD_PID