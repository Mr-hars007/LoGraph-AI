"""Rule evaluation and action execution for predicted link anomalies.

Supports low-link and high-failure probability triggers with command execution.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, List

from .graph_model import TrainedModel, predict_edge_probability
from .otel_ingest import EdgeEvent


@dataclass(frozen=True)
class TriggeredAction:
    name: str
    rule_type: str
    source: str
    target: str
    probability: float
    failure_probability: float
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
        failure_probability = 1.0 - probability
        context = {
            "source": event.source,
            "target": event.target,
            "probability": f"{probability:.6f}",
            "failure_probability": f"{failure_probability:.6f}",
            "timestamp": f"{event.timestamp:.3f}",
        }

        for action in actions:
            rule = action.get("when", {})
            rule_type = str(rule.get("type", "low_link_probability")).strip().lower()
            threshold = float(rule.get("threshold", model.threshold))

            should_trigger = False
            if rule_type == "low_link_probability":
                should_trigger = probability <= threshold
            elif rule_type in {"high_failure_probability", "failure_probability_above"}:
                should_trigger = failure_probability >= threshold

            if not should_trigger:
                continue

            exec_cfg = action.get("exec", {})
            python_script = str(exec_cfg.get("python_script", "")).strip()
            if python_script:
                command = sys.executable
                raw_args = [python_script] + list(exec_cfg.get("args", []))
            else:
                command = str(exec_cfg.get("command", "")).strip()
                raw_args = list(exec_cfg.get("args", []))
                if not command:
                    continue

            args = _render_args(raw_args, context)
            timeout = int(exec_cfg.get("timeout_seconds", 20))
            result = subprocess.run([command] + args, capture_output=True, text=True, timeout=timeout)
            triggered.append(
                TriggeredAction(
                    name=str(action.get("name", "unnamed-action")),
                    rule_type=rule_type,
                    source=event.source,
                    target=event.target,
                    probability=probability,
                    failure_probability=failure_probability,
                    command=" ".join([command] + args),
                    return_code=int(result.returncode),
                )
            )

    return triggered
