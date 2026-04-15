"""Desktop GUI for configuring and running LoGraph with CLI-equivalent controls.

Supports config initialization/loading/saving, one-shot runs, and continuous
monitoring with start/stop controls.
"""

from __future__ import annotations

import json
from pathlib import Path
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk

from .cli import run_once
from .config import create_setup_payload, is_setup_completed, load_config, save_config_payload, write_default_config
from .reset import reset_generated_data


def launch_gui(config_path: Path, model_path: Path) -> None:
    write_default_config(config_path)
    cfg = load_config(config_path)

    root = tk.Tk()
    root.title("LoGraph Tool - CLI Parity Console")
    root.geometry("980x760")

    frame = ttk.Frame(root, padding=14)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)
    frame.rowconfigure(14, weight=1)

    state = {
        "monitor_thread": None,
        "monitor_stop": threading.Event(),
        "is_monitoring": False,
    }

    config_path_var = tk.StringVar(value=str(config_path))
    model_path_var = tk.StringVar(value=str(model_path))

    endpoint_var = tk.StringVar(value=str(cfg.telemetry.get("endpoint", "")))
    jsonl_var = tk.StringVar(value=str(cfg.telemetry.get("jsonl_path", "")))
    mode_var = tk.StringVar(value=str(cfg.telemetry.get("mode", "jsonl")))
    poll_var = tk.StringVar(value=str(cfg.telemetry.get("poll_seconds", "30")))
    lookback_var = tk.StringVar(value=str(cfg.telemetry.get("lookback_seconds", "600")))

    neg_ratio_var = tk.StringVar(value=str(cfg.training.get("negative_ratio", "1")))
    epochs_var = tk.StringVar(value=str(cfg.training.get("epochs", "500")))
    lr_var = tk.StringVar(value=str(cfg.training.get("learning_rate", "0.05")))
    steps_var = tk.StringVar(value=str(cfg.training.get("message_passing_steps", "2")))
    emb_var = tk.StringVar(value=str(cfg.training.get("embedding_size", "4")))
    threshold_var = tk.StringVar(value=str(cfg.training.get("anomaly_threshold", "0.25")))
    failure_threshold_var = tk.StringVar(value=str(cfg.training.get("failure_threshold", "0.75")))

    # Incident action fields
    incident_script_default = ""
    failure_script_default = ""

    incident_action = next((a for a in cfg.actions if str(a.get("name", "")) == "gui-action"), {})
    incident_exec = incident_action.get("exec", {})
    incident_script = str(incident_exec.get("python_script", "")).strip()
    if not incident_script:
        incident_args = list(incident_exec.get("args", []))
        if incident_exec.get("command") == "python" and incident_args:
            incident_script = incident_args[0]
            incident_args = incident_args[1:]
        else:
            incident_args = incident_args
    else:
        incident_args = list(incident_exec.get("args", []))

    incident_script_var = tk.StringVar(value=incident_script or incident_script_default)
    incident_args_var = tk.StringVar(value=" ".join(incident_args))

    # Failure action fields
    failure_action = next((a for a in cfg.actions if str(a.get("name", "")) == "python-failure-handler"), {})
    failure_exec = failure_action.get("exec", {})
    failure_script_var = tk.StringVar(value=str(failure_exec.get("python_script", failure_script_default)))
    failure_args_var = tk.StringVar(value=" ".join(list(failure_exec.get("args", []))))

    def log(message: str) -> None:
        ts = time.strftime("%H:%M:%S")
        output.insert(tk.END, f"[{ts}] {message}\n")
        output.see(tk.END)

    def current_config_path() -> Path:
        return Path(config_path_var.get().strip()).resolve()

    def current_model_path() -> Path:
        return Path(model_path_var.get().strip()).resolve()

    def parse_args(text: str) -> list[str]:
        return [part for part in text.split(" ") if part]

    def build_payload() -> dict:
        incident_args = parse_args(incident_args_var.get())
        failure_args = parse_args(failure_args_var.get())

        return {
            "telemetry": {
                "mode": mode_var.get().strip(),
                "endpoint": endpoint_var.get().strip(),
                "jsonl_path": jsonl_var.get().strip(),
                "poll_seconds": int(poll_var.get().strip()),
                "lookback_seconds": int(lookback_var.get().strip()),
            },
            "training": {
                "negative_ratio": int(neg_ratio_var.get().strip()),
                "epochs": int(epochs_var.get().strip()),
                "learning_rate": float(lr_var.get().strip()),
                "message_passing_steps": int(steps_var.get().strip()),
                "embedding_size": int(emb_var.get().strip()),
                "anomaly_threshold": float(threshold_var.get().strip()),
                "failure_threshold": float(failure_threshold_var.get().strip()),
            },
            "actions": [
                {
                    "name": "gui-action",
                    "when": {"type": "low_link_probability", "threshold": float(threshold_var.get().strip())},
                    "exec": {
                        "python_script": incident_script_var.get().strip(),
                        "args": incident_args,
                        "timeout_seconds": 20,
                    },
                },
                {
                    "name": "python-failure-handler",
                    "when": {"type": "high_failure_probability", "threshold": float(failure_threshold_var.get().strip())},
                    "exec": {
                        "python_script": failure_script_var.get().strip(),
                        "args": failure_args,
                        "timeout_seconds": 20,
                    },
                },
            ],
        }

    def fill_form_from_cfg() -> None:
        loaded = load_config(current_config_path())

        mode_var.set(str(loaded.telemetry.get("mode", "jsonl")))
        endpoint_var.set(str(loaded.telemetry.get("endpoint", "")))
        jsonl_var.set(str(loaded.telemetry.get("jsonl_path", "")))
        poll_var.set(str(loaded.telemetry.get("poll_seconds", "30")))
        lookback_var.set(str(loaded.telemetry.get("lookback_seconds", "600")))

        threshold_var.set(str(loaded.training.get("anomaly_threshold", "0.25")))
        failure_threshold_var.set(str(loaded.training.get("failure_threshold", "0.75")))
        neg_ratio_var.set(str(loaded.training.get("negative_ratio", "1")))
        epochs_var.set(str(loaded.training.get("epochs", "500")))
        lr_var.set(str(loaded.training.get("learning_rate", "0.05")))
        steps_var.set(str(loaded.training.get("message_passing_steps", "2")))
        emb_var.set(str(loaded.training.get("embedding_size", "4")))

        loaded_actions = loaded.actions
        loaded_incident = next((a for a in loaded_actions if str(a.get("name", "")) == "gui-action"), {})
        loaded_incident_exec = loaded_incident.get("exec", {})
        incident_script = str(loaded_incident_exec.get("python_script", "")).strip()
        incident_args = list(loaded_incident_exec.get("args", []))
        if not incident_script:
            raw_incident_args = list(loaded_incident_exec.get("args", []))
            if loaded_incident_exec.get("command") == "python" and raw_incident_args:
                incident_script = raw_incident_args[0]
                incident_args = raw_incident_args[1:]

        incident_script_var.set(incident_script or incident_script_default)
        incident_args_var.set(" ".join(incident_args))

        loaded_failure = next((a for a in loaded_actions if str(a.get("name", "")) == "python-failure-handler"), {})
        loaded_failure_exec = loaded_failure.get("exec", {})
        failure_script_var.set(str(loaded_failure_exec.get("python_script", failure_script_default)))
        failure_args_var.set(" ".join(list(loaded_failure_exec.get("args", []))))

    def reset_data() -> None:
        if not messagebox.askyesno("Confirm reset", "Delete generated models and runtime event files?"):
            return
        summary = reset_generated_data(current_config_path().parent, current_model_path())
        log(f"Reset deleted files: {summary['deleted_count']}")
        if summary["errors"]:
            for item in summary["errors"]:
                log(f"Reset error: {item}")

    def save_config() -> None:
        payload = build_payload()
        cp = current_config_path()
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log(f"Saved config to {cp}")

    def quick_setup_and_start() -> None:
        choice = messagebox.askyesnocancel(
            "Setup Mode",
            "Telemetry source?\nYes = Local JSONL\nNo = Remote HTTP\nCancel = abort",
        )
        if choice is None:
            return

        if choice:
            mode = "jsonl"
            jsonl_path = simpledialog.askstring("Local JSONL", "JSONL file path:", initialvalue=jsonl_var.get().strip())
            if not jsonl_path:
                return
            endpoint = ""
        else:
            mode = "http"
            endpoint = simpledialog.askstring(
                "Remote HTTP",
                "OTLP HTTP endpoint:",
                initialvalue=endpoint_var.get().strip(),
            )
            if not endpoint:
                return
            jsonl_path = ""

        incident_script = simpledialog.askstring(
            "Incident Script",
            "Incident handler script path (optional):",
            initialvalue=incident_script_var.get().strip(),
        )
        if incident_script is None:
            return

        failure_script = simpledialog.askstring(
            "Failure Script",
            "Failure handler script path (optional):",
            initialvalue=failure_script_var.get().strip(),
        )
        if failure_script is None:
            return

        start_monitor_now = messagebox.askyesno("Start Mode", "Start continuous monitoring now?\n(No = run once)")

        payload = create_setup_payload(
            mode=mode,
            jsonl_path=jsonl_path,
            endpoint=endpoint,
            incident_script=incident_script,
            failure_script=failure_script,
            poll_seconds=int(poll_var.get().strip() or "30"),
            lookback_seconds=int(lookback_var.get().strip() or "600"),
        )
        save_config_payload(current_config_path(), payload)
        fill_form_from_cfg()
        log(f"Quick setup saved to {current_config_path()}")

        if start_monitor_now:
            start_monitor()
        else:
            run_now()

    def init_config() -> None:
        cp = current_config_path()
        write_default_config(cp)
        fill_form_from_cfg()
        log(f"Initialized default config at {cp}")

    def load_config_into_form() -> None:
        fill_form_from_cfg()
        log(f"Loaded config from {current_config_path()}")

    def run_now() -> None:
        try:
            save_config()
            run_once(current_config_path(), current_model_path())
            log("Run Once completed")
        except Exception as exc:
            messagebox.showerror("Run error", str(exc))

    def monitor_loop() -> None:
        while not state["monitor_stop"].is_set():
            try:
                run_once(current_config_path(), current_model_path())
                root.after(0, lambda: log("Monitor cycle completed"))
            except Exception as exc:
                root.after(0, lambda err=str(exc): log(f"Monitor error: {err}"))

            try:
                poll_seconds = max(1, int(poll_var.get().strip()))
            except ValueError:
                poll_seconds = 30
            state["monitor_stop"].wait(timeout=poll_seconds)

        root.after(0, lambda: log("Monitor stopped"))
        state["is_monitoring"] = False

    def start_monitor() -> None:
        if state["is_monitoring"]:
            return
        try:
            save_config()
            state["monitor_stop"].clear()
            t = threading.Thread(target=monitor_loop, daemon=True)
            state["monitor_thread"] = t
            state["is_monitoring"] = True
            t.start()
            log("Monitor started")
        except Exception as exc:
            messagebox.showerror("Monitor error", str(exc))

    def stop_monitor() -> None:
        state["monitor_stop"].set()

    def on_close() -> None:
        stop_monitor()
        root.destroy()

    row = 0
    ttk.Label(frame, text="Config path").grid(row=row, column=0, sticky="w")
    ttk.Entry(frame, textvariable=config_path_var).grid(row=row, column=1, sticky="ew", padx=(8, 0))

    row += 1
    ttk.Label(frame, text="Model path").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=model_path_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Telemetry mode").grid(row=row, column=0, sticky="w", pady=(8, 0))
    mode_box = ttk.Combobox(frame, textvariable=mode_var, values=["jsonl", "http"], state="readonly")
    mode_box.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="OTel endpoint").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=endpoint_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="JSONL path").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=jsonl_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Poll seconds").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=poll_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Lookback seconds").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=lookback_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Anomaly threshold").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=threshold_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Failure threshold").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=failure_threshold_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Negative ratio").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=neg_ratio_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Epochs").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=epochs_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Learning rate").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=lr_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Message passing steps").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=steps_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Embedding size").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=emb_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Incident script").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=incident_script_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Incident args").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=incident_args_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Failure script").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=failure_script_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    row += 1
    ttk.Label(frame, text="Failure args").grid(row=row, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(frame, textvariable=failure_args_var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

    output = tk.Text(frame, height=14)
    output.grid(row=row + 1, column=0, columnspan=2, sticky="nsew", pady=(12, 0))

    actions = ttk.Frame(frame)
    actions.grid(row=row + 2, column=0, columnspan=2, sticky="e", pady=(10, 0))
    ttk.Button(actions, text="Quick Setup + Start", command=quick_setup_and_start).pack(side="left")
    ttk.Button(actions, text="Init Default", command=init_config).pack(side="left")
    ttk.Button(actions, text="Load Config", command=load_config_into_form).pack(side="left", padx=(8, 0))
    ttk.Button(actions, text="Save Config", command=save_config).pack(side="left", padx=(8, 0))
    ttk.Button(actions, text="Run Once", command=run_now).pack(side="left", padx=(8, 0))
    ttk.Button(actions, text="Start Monitor", command=start_monitor).pack(side="left", padx=(8, 0))
    ttk.Button(actions, text="Stop Monitor", command=stop_monitor).pack(side="left", padx=(8, 0))
    ttk.Button(actions, text="Reset Generated Data", command=reset_data).pack(side="left", padx=(8, 0))

    root.protocol("WM_DELETE_WINDOW", on_close)
    log("GUI ready. Use Quick Setup + Start for first-time minimal setup.")
    if not is_setup_completed(current_config_path()):
        root.after(250, quick_setup_and_start)
    root.mainloop()


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    launch_gui(root / "lograph-tool.json", root / "models" / "lograph_tool_model.json")
