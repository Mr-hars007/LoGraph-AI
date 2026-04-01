from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from .cli import run_once
from .config import load_config, write_default_config


def launch_gui(config_path: Path, model_path: Path) -> None:
    write_default_config(config_path)
    cfg = load_config(config_path)

    root = tk.Tk()
    root.title("LoGraph Tool - Automation Console")
    root.geometry("900x620")

    frame = ttk.Frame(root, padding=14)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(5, weight=1)

    endpoint_var = tk.StringVar(value=str(cfg.telemetry.get("endpoint", "http://127.0.0.1:4318/v1/logs")))
    jsonl_var = tk.StringVar(value=str(cfg.telemetry.get("jsonl_path", "data/otel_logs.jsonl")))
    mode_var = tk.StringVar(value=str(cfg.telemetry.get("mode", "jsonl")))
    threshold_var = tk.StringVar(value=str(cfg.training.get("anomaly_threshold", 0.25)))
    cmd_var = tk.StringVar(value="python")
    args_var = tk.StringVar(value="scripts/handle_incident.py {source} {target} {probability}")

    ttk.Label(frame, text="Telemetry mode").grid(row=0, column=0, sticky="w")
    mode_box = ttk.Combobox(frame, textvariable=mode_var, values=["jsonl", "http"], state="readonly")
    mode_box.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    ttk.Label(frame, text="OTel endpoint").grid(row=1, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=endpoint_var).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    ttk.Label(frame, text="JSONL path").grid(row=2, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=jsonl_var).grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    ttk.Label(frame, text="Trigger threshold").grid(row=3, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=threshold_var).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    ttk.Label(frame, text="Action command").grid(row=4, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=cmd_var).grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    ttk.Label(frame, text="Action args").grid(row=5, column=0, sticky="nw", pady=(8, 0))
    ttk.Entry(frame, textvariable=args_var).grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    output = tk.Text(frame, height=14)
    output.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=(12, 0))

    def save_config() -> None:
        args = [part for part in args_var.get().split(" ") if part]
        payload = {
            "telemetry": {
                "mode": mode_var.get().strip(),
                "endpoint": endpoint_var.get().strip(),
                "jsonl_path": jsonl_var.get().strip(),
                "poll_seconds": 30,
                "lookback_seconds": 600,
            },
            "training": {
                "negative_ratio": 1,
                "epochs": 500,
                "learning_rate": 0.05,
                "message_passing_steps": 2,
                "embedding_size": 4,
                "anomaly_threshold": float(threshold_var.get().strip()),
            },
            "actions": [
                {
                    "name": "gui-action",
                    "when": {"type": "low_link_probability", "threshold": float(threshold_var.get().strip())},
                    "exec": {"command": cmd_var.get().strip(), "args": args, "timeout_seconds": 20},
                }
            ],
        }
        config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def run_now() -> None:
        try:
            save_config()
            run_once(config_path, model_path)
            output.insert(tk.END, "Run completed. Check terminal for detailed stats.\n")
            output.see(tk.END)
        except Exception as exc:
            messagebox.showerror("Run error", str(exc))

    actions = ttk.Frame(frame)
    actions.grid(row=7, column=0, columnspan=2, sticky="e", pady=(10, 0))
    ttk.Button(actions, text="Save Config", command=save_config).pack(side="left")
    ttk.Button(actions, text="Run Once", command=run_now).pack(side="left", padx=(8, 0))

    root.mainloop()


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    launch_gui(root / "lograph-tool.json", root / "models" / "lograph_tool_model.json")
