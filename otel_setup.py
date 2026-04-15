import os
import json
import logging
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor

class JsonFileSpanExporter(SpanExporter):
    """Custom Exporter to save OTel spans as JSON lines in the data folder."""
    def __init__(self, file_path):
        self.file_path = file_path
        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        except:
            pass

    def export(self, spans):
        for span in spans:
            # Prepare a simplified span record for JSON storage
            span_record = {
                "timestamp": span.start_time // 10**9, # Unix timestamp in seconds
                "trace_id": format(span.get_span_context().trace_id, "032x"),
                "span_id": format(span.get_span_context().span_id, "16x"),
                "parent_id": format(span.parent.span_id, "16x") if span.parent else None,
                "name": span.name,
                "service": span.resource.attributes.get("service.name", "unknown"),
                "duration_ms": (span.end_time - span.start_time) / 10**6,
                "attributes": dict(span.attributes),
                "status": span.status.status_code.name,
                "start_time_iso": datetime.fromtimestamp(span.start_time / 10**9).isoformat()
            }
            
            # Write to the JSONL file in the data folder
            try:
                with open(self.file_path, "a") as f:
                    f.write(json.dumps(span_record) + "\n")
            except Exception as e:
                print(f"Error writing OTel span to file: {e}")
                
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass

def setup_otel(service_name):
    """Initializes OpenTelemetry with both Jaeger and File exporters."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    
    # 1. File Exporter (for centralized data folder persistence)
    # Use /app/data/system_logs for Docker, but fallback to local path
    if os.path.exists("/app/data"):
        data_dir = "/app/data/system_logs"
    else:
        # Local relative path
        data_dir = os.path.join(os.path.dirname(__file__), "data", "system_logs")
    
    os.makedirs(data_dir, exist_ok=True)
    trace_file = os.path.join(data_dir, "otel_traces.json")
    
    file_exporter = JsonFileSpanExporter(trace_file)
    provider.add_span_processor(BatchSpanProcessor(file_exporter))
    
    # 2. OTLP Exporter (Jaeger)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "jaeger:4317")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            # Handle cases where endpoint might be localhost for local dev
            if "jaeger" not in otlp_endpoint and "localhost" not in otlp_endpoint:
                # Default to jaeger if not specified and in docker
                if os.path.exists("/.dockerenv"):
                    otlp_endpoint = "jaeger:4317"
            
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        except Exception as e:
            print(f"Failed to setup OTLP Exporter: {e}")

    trace.set_tracer_provider(provider)
    
    # Global Instrumentation for outgoing requests and database
    RequestsInstrumentor().instrument()
    PymongoInstrumentor().instrument()
    
    return trace.get_tracer(service_name)

def instrument_app(app):
    """Instruments a Flask application."""
    FlaskInstrumentor().instrument_app(app)
