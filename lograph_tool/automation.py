from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List

from .graph_model import TrainedModel, predict_edge_probability
from .otel_ingest import EdgeEvent


@dataclass(frozen=True)
class TriggeredAction:
    name: str
    source: str
    target: str
    probability: float
    command: str
    return_code: int


def _render_args(args: List[str], context: Dict[str, Any]) -> List[str]:
    return [a.format(**context) for a in args]


def evaluate_and_trigger(events: List[EdgeEvent], model: TrainedModel, actions: List[Dict[str, Any]]) -> List[TriggeredAction]:
    triggered: List[TriggeredAction] = []
    if not actions:
        return triggered

    for event in events:
        probability = predict_edge_probability(model, event.source, event.target)
        context = {
            "source": event.source,
            "target": event.target,
            "probability": f"{probability:.6f}",
            "timestamp": f"{event.timestamp:.3f}",
        }

        for action in actions:
            rule = action.get("when", {})
            if rule.get("type") != "low_link_probability":
                continue
            threshold = float(rule.get("threshold", model.threshold))
            if probability > threshold:
                continue

            exec_cfg = action.get("exec", {})
            command = str(exec_cfg.get("command", "")).strip()
            if not command:
                continue

            args = _render_args(exec_cfg.get("args", []), context)
            timeout = int(exec_cfg.get("timeout_seconds", 20))
            result = subprocess.run([command] + args, capture_output=True, text=True, timeout=timeout)
            triggered.append(
                TriggeredAction(
                    name=str(action.get("name", "unnamed-action")),
                    source=event.source,
                    target=event.target,
                    probability=probability,
                    command=" ".join([command] + args),
                    return_code=int(result.returncode),
                )
            )

    return triggered
