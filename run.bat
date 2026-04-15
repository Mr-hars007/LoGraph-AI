@echo off
echo ==========================================
echo Starting LoGraph-AI Microservices Stack
echo ==========================================
echo.
echo Step 1: Creating log directory...
if not exist "logs" mkdir "logs"
echo.
echo Step 2: Building and starting containers (detached)...
docker-compose up --build -d
echo.
echo ==========================================
echo Application is starting up!
echo ==========================================
echo Frontend:      http://localhost:3000
echo API Gateway:   http://localhost:5005
echo Jaeger UI:     http://localhost:16686
echo.
echo Centralized Log File: LoGraph-AI/logs/system_activity.log
echo GNN Data File:        LoGraph-AI/data/otel_logs.jsonl
echo.
echo To view logs in real-time:
echo powershell.exe Get-Content logs/system_activity.log -Wait
echo.
echo To stop, run: docker-compose down
echo ==========================================
pause
