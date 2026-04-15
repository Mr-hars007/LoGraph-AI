# GEMINI.md

## Project Overview
**LoGraph-AI** is a microservices-based e-commerce prototype that showcases centralized logging, distributed tracing (OpenTelemetry), and Graph Neural Network (GNN) capabilities. It comprises a React/Vite frontend and a Python-based backend that consolidates User, Order, Payment, and API Gateway services.

The system uses OpenTelemetry to collect distributed traces, which are then used by the `gnn-service` pipeline to build a directed interaction graph. These traces are saved in `data/otel_logs.jsonl` matching a specific GNN sample data structure. 

## Technologies Used
- **Frontend**: React, Vite
- **Backend**: Python, Flask, FastAPI, Uvicorn
- **Database**: MongoDB
- **Tracing**: OpenTelemetry, Jaeger
- **Data/Graph Processing**: Pandas, NetworkX

## Building and Running

### Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB running locally on port `27017`

### 1. Start the Unified Backend
This starts the consolidated microservices architecture and OpenTelemetry instrumentation:
```powershell
cd LoGraph-AI
pip install -r requirements.txt
python unified_app.py
```
*The backend runs on http://localhost:5005.*

### 2. Start the Frontend
```powershell
cd LoGraph-AI/frontend
npm install
npm run dev -- --port 3000
```
*The frontend runs on http://localhost:3000.*

### 3. GNN Service Pipeline (Optional)
```powershell
cd LoGraph-AI
python gnn-service/main.py
```

## Development Conventions
- **Observability-First**: The system logs every internal service-to-service interaction.
- **Data Formats**: OTel logs are exported in a JSONL format containing Unix timestamps, source, and target keys to be consumed by the GNN model.
- **Absolute Imports**: Absolute imports relative to the `LoGraph-AI` root are preferred for backend Python modules.
- **RESTful APIs**: The backend exposes clearly defined REST endpoints for user authentication, order processing, and payment status checks.