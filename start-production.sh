#!/bin/bash

echo "🚀 Starting ProEx Platform - Production Mode"
echo "=============================================="

# Start backend API on port 8000 (main service)
echo "Starting Backend API on port 8000..."
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start email service on port 3001
echo "Starting Email Service on port 3001..."
cd backend && npm start &
EMAIL_PID=$!

echo ""
echo "✅ All services started!"
echo "   - Backend API + Frontend: http://0.0.0.0:8000"
echo "   - Email Service: http://0.0.0.0:3001"
echo ""
echo "Waiting for services..."

# Wait for all background processes
wait $BACKEND_PID $EMAIL_PID
