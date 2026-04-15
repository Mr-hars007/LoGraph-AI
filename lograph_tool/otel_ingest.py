from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class EdgeEvent:
    timestamp: float
    source: str
    target: str


def _attr_lookup(attributes: Iterable[Dict[str, Any]], key: str) -> Optional[str]:
    for item in attributes:
        if item.get("key") != key:
            continue
        val = item.get("value", {})
        for k in ["stringValue", "intValue", "doubleValue", "boolValue"]:
            if k in val:
                return str(val[k])
    return None


def _extract_target(attributes: Iterable[Dict[str, Any]], body_text: str) -> Optional[str]:
    candidate_keys = [
        "peer.service",
        "server.address",
        "net.peer.name",
        "http.host",
        "db.system",
        "messaging.destination.name",
    ]
    for key in candidate_keys:
        value = _attr_lookup(attributes, key)
        if value:
            return value.strip()

    if "->" in body_text:
        left, right = body_text.split("->", 1)
        if right.strip():
            return right.strip().split()[0]
    return None


def parse_otlp_json(payload: Dict[str, Any]) -> List[EdgeEvent]:
    events: List[EdgeEvent] = []
    for resource_log in payload.get("resourceLogs", []):
        resource_attrs = resource_log.get("resource", {}).get("attributes", [])
        service_name = _attr_lookup(resource_attrs, "service.name")
        if not service_name:
            service_name = "unknown-service"

        for scope_log in resource_log.get("scopeLogs", []):
            for record in scope_log.get("logRecords", []):
                attrs = record.get("attributes", [])
                body = record.get("body", {})
                body_text = str(body.get("stringValue", ""))
                target = _extract_target(attrs, body_text)
                if not target:
                    continue

                ts_unix_nano = record.get("timeUnixNano")
                if ts_unix_nano is None:
                    timestamp = time.time()
                else:
                    timestamp = float(ts_unix_nano) / 1_000_000_000.0

                events.append(EdgeEvent(timestamp=timestamp, source=service_name.strip(), target=target.strip()))
    return events


def fetch_from_otel_http(endpoint: str) -> List[EdgeEvent]:
    req = urllib.request.Request(endpoint, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return parse_otlp_json(data)


def fetch_from_jsonl(jsonl_path: Path) -> List[EdgeEvent]:
    if not jsonl_path.exists():
        return []

    events: List[EdgeEvent] = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Accept either raw event lines or full OTLP documents.
        if "resourceLogs" in payload:
            events.extend(parse_otlp_json(payload))
            continue

        source = str(payload.get("source", "")).strip()
        target = str(payload.get("target", "")).strip()
        if not source or not target:
            continue

        timestamp = float(payload.get("timestamp", time.time()))
        events.append(EdgeEvent(timestamp=timestamp, source=source, target=target))

    return events


def filter_by_lookback(events: List[EdgeEvent], lookback_seconds: int) -> List[EdgeEvent]:
    if lookback_seconds <= 0:
        return events
    cutoff = time.time() - lookback_seconds
    return [e for e in events if e.timestamp >= cutoff]
