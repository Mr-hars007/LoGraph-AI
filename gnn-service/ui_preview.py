"""Tkinter preview UI for graph preparation and local training actions."""

from __future__ import annotations

import math
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

from main import prepare_graph_data
from model_trainer import train_with_rpc_files


def run_pipeline(project_root: Path, rpc_file: str, metrics_dir: str):
    rpc_path = project_root / "data" / rpc_file
    metrics_path = project_root / metrics_dir
    return prepare_graph_data(rpc_path, metrics_path)


def launch_ui() -> None:
    project_root = Path(__file__).resolve().parent.parent
    state = {
        "prepared": None,
        "node_positions": {},
        "node_items": {},
        "selected_node": None,
    }

    root = tk.Tk()
    root.title("LoGraph-AI Detailed Graph Explorer")
    root.geometry("1220x760")
    root.configure(bg="#edf3fb")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Card.TFrame", background="#ffffff")
    style.configure("Header.TLabel", background="#ffffff", font=("Segoe UI", 12, "bold"))
    style.configure("Text.TLabel", background="#ffffff", font=("Segoe UI", 10))

    frame = ttk.Frame(root, padding=14)
    frame.pack(fill="both", expand=True)

    frame.columnconfigure(0, weight=3)
    frame.columnconfigure(1, weight=2)
    frame.rowconfigure(2, weight=1)

    controls = ttk.Frame(frame, style="Card.TFrame", padding=12)
    controls.grid(row=0, column=0, columnspan=2, sticky="ew")
    controls.columnconfigure(1, weight=1)
    controls.columnconfigure(3, weight=1)

    ttk.Label(controls, text="RPC map file(s):", style="Text.TLabel").grid(row=0, column=0, sticky="w")
    rpc_var = tk.StringVar(value="compose_ms_rpc_map.csv")
    ttk.Entry(controls, textvariable=rpc_var, width=40).grid(row=0, column=1, sticky="ew", padx=(8, 14))

    ttk.Label(controls, text="Metrics directory:", style="Text.TLabel").grid(row=0, column=2, sticky="w")
    metrics_var = tk.StringVar(value="data")
    ttk.Entry(controls, textvariable=metrics_var, width=28).grid(row=0, column=3, sticky="ew", padx=(8, 14))

    ttk.Label(controls, text="Model file:", style="Text.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
    model_var = tk.StringVar(value="models/link_predictor_baseline.json")
    ttk.Entry(controls, textvariable=model_var, width=40).grid(row=1, column=1, sticky="ew", padx=(8, 14), pady=(8, 0))

    status_var = tk.StringVar(value="Ready")
    ttk.Label(controls, textvariable=status_var, style="Text.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))

    actions = ttk.Frame(controls, style="Card.TFrame")
    actions.grid(row=2, column=3, sticky="e", pady=(10, 0))
    ttk.Button(actions, text="Run Pipeline", command=lambda: on_run()).pack(side="left")
    ttk.Button(actions, text="Train Model", command=lambda: on_train()).pack(side="left", padx=(8, 0))

    summary = ttk.Frame(frame, style="Card.TFrame", padding=10)
    summary.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 10))
    summary.columnconfigure(0, weight=1)
    summary.columnconfigure(1, weight=1)
    summary.columnconfigure(2, weight=1)
    summary.columnconfigure(3, weight=1)
    summary.columnconfigure(4, weight=1)

    metric_vars = {
        "Nodes": tk.StringVar(value="0"),
        "Edges": tk.StringVar(value="0"),
        "Weighted Calls": tk.StringVar(value="0"),
        "Nodes With CPU": tk.StringVar(value="0"),
        "Feature Dim": tk.StringVar(value="0"),
    }

    for i, (label, var) in enumerate(metric_vars.items()):
        card = ttk.Frame(summary, style="Card.TFrame", padding=8)
        card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0))
        ttk.Label(card, text=label, style="Text.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=var, style="Header.TLabel").pack(anchor="w")

    graph_card = ttk.Frame(frame, style="Card.TFrame", padding=10)
    graph_card.grid(row=2, column=0, sticky="nsew", padx=(0, 8))
    graph_card.columnconfigure(0, weight=1)
    graph_card.rowconfigure(1, weight=1)
    ttk.Label(graph_card, text="Graph View", style="Header.TLabel").grid(row=0, column=0, sticky="w")

    canvas = tk.Canvas(graph_card, bg="#f7fbff", highlightthickness=1, highlightbackground="#d7e3ef")
    canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

    right_panel = ttk.Frame(frame, style="Card.TFrame", padding=10)
    right_panel.grid(row=2, column=1, sticky="nsew")
    right_panel.columnconfigure(0, weight=1)
    right_panel.rowconfigure(1, weight=1)
    right_panel.rowconfigure(3, weight=1)
    right_panel.rowconfigure(5, weight=1)

    ttk.Label(right_panel, text="Node Inspector", style="Header.TLabel").grid(row=0, column=0, sticky="w")
    node_info = tk.Text(right_panel, height=10, wrap="word", bg="#fbfdff", relief="solid", borderwidth=1)
    node_info.grid(row=1, column=0, sticky="nsew", pady=(6, 10))

    ttk.Label(right_panel, text="Edge Details (Top by weight)", style="Header.TLabel").grid(row=2, column=0, sticky="w")
    columns = ("source", "target", "weight")
    edge_table = ttk.Treeview(right_panel, columns=columns, show="headings", height=12)
    edge_table.heading("source", text="Source")
    edge_table.heading("target", text="Target")
    edge_table.heading("weight", text="Call Count")
    edge_table.column("source", width=140, anchor="w")
    edge_table.column("target", width=140, anchor="w")
    edge_table.column("weight", width=90, anchor="center")
    edge_table.grid(row=3, column=0, sticky="nsew", pady=(6, 0))

    edge_scroll = ttk.Scrollbar(right_panel, orient="vertical", command=edge_table.yview)
    edge_table.configure(yscroll=edge_scroll.set)
    edge_scroll.place(relx=1.0, rely=0.64, relheight=0.34, anchor="ne")

    ttk.Label(right_panel, text="Training Output", style="Header.TLabel").grid(row=4, column=0, sticky="w", pady=(10, 0))
    train_info = tk.Text(right_panel, height=7, wrap="word", bg="#fbfdff", relief="solid", borderwidth=1)
    train_info.grid(row=5, column=0, sticky="nsew", pady=(6, 0))
    train_info.insert("1.0", "Click Train Model to train and save the baseline artifact.")
    train_info.configure(state="disabled")

    def update_node_info(node_name: str | None) -> None:
        node_info.configure(state="normal")
        node_info.delete("1.0", tk.END)
        prepared = state["prepared"]
        if not node_name or prepared is None:
            node_info.insert(tk.END, "Click a node to inspect detailed features and connectivity.")
            node_info.configure(state="disabled")
            return

        detail = next((d for d in prepared.node_details if d["name"] == node_name), None)
        if detail is None:
            node_info.insert(tk.END, "Node details unavailable.")
            node_info.configure(state="disabled")
            return

        lines = [
            f"Name: {detail['name']}",
            f"Index: {detail['index']}",
            "",
            f"In-degree: {detail['in_degree']}",
            f"Out-degree: {detail['out_degree']}",
            f"In-weight: {detail['in_weight']}",
            f"Out-weight: {detail['out_weight']}",
            "",
            f"CPU Last: {detail['cpu_last']:.6f}",
            f"CPU Mean: {detail['cpu_mean']:.6f}",
            f"CPU Rate: {detail['cpu_rate']:.9f}",
        ]
        node_info.insert(tk.END, "\n".join(lines))
        node_info.configure(state="disabled")

    def draw_graph() -> None:
        canvas.delete("all")
        state["node_positions"].clear()
        state["node_items"].clear()

        prepared = state["prepared"]
        if prepared is None:
            return

        width = max(canvas.winfo_width(), 700)
        height = max(canvas.winfo_height(), 480)
        nodes = prepared.node_names
        if not nodes:
            return

        cx = width / 2
        cy = height / 2
        radius = min(width, height) * 0.37
        n = len(nodes)

        for idx, node in enumerate(nodes):
            angle = (2 * math.pi * idx / max(n, 1)) - (math.pi / 2)
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            state["node_positions"][node] = (x, y)

        for edge in prepared.edge_details:
            x1, y1 = state["node_positions"][edge["source"]]
            x2, y2 = state["node_positions"][edge["target"]]
            weight = edge["call_count"]
            line_w = 1 + min(5, weight)

            canvas.create_line(
                x1,
                y1,
                x2,
                y2,
                fill="#7b8fa4",
                width=line_w,
                arrow=tk.LAST,
                arrowshape=(10, 12, 4),
            )

            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2
            canvas.create_text(mx, my, text=str(weight), fill="#3f5870", font=("Segoe UI", 8, "bold"))

        for detail in prepared.node_details:
            node = detail["name"]
            x, y = state["node_positions"][node]
            size = 10 + min(14, detail["in_degree"] + detail["out_degree"])
            cpu = detail["cpu_last"]
            fill = "#f7b267" if cpu > 0 else "#8cc8ff"
            outline = "#2a5674" if state["selected_node"] == node else "#3d6f91"
            width_px = 3 if state["selected_node"] == node else 1

            oval = canvas.create_oval(
                x - size,
                y - size,
                x + size,
                y + size,
                fill=fill,
                outline=outline,
                width=width_px,
            )
            label = canvas.create_text(x, y + size + 12, text=node, fill="#1f3342", font=("Segoe UI", 8))
            state["node_items"][oval] = node
            state["node_items"][label] = node

    def on_canvas_click(event: tk.Event) -> None:
        item = canvas.find_closest(event.x, event.y)
        if not item:
            return
        node = state["node_items"].get(item[0])
        if node is None:
            return
        state["selected_node"] = node
        draw_graph()
        update_node_info(node)

    canvas.bind("<Button-1>", on_canvas_click)

    def populate_edges() -> None:
        for item in edge_table.get_children():
            edge_table.delete(item)
        prepared = state["prepared"]
        if prepared is None:
            return

        sorted_edges = sorted(prepared.edge_details, key=lambda e: e["call_count"], reverse=True)
        for edge in sorted_edges[:150]:
            edge_table.insert("", tk.END, values=(edge["source"], edge["target"], edge["call_count"]))

    def on_run() -> None:
        try:
            prepared = run_pipeline(project_root, rpc_var.get().strip(), metrics_var.get().strip())
            state["prepared"] = prepared
            state["selected_node"] = None

            stats = prepared.stats
            metric_vars["Nodes"].set(str(int(stats.get("nodes", 0))))
            metric_vars["Edges"].set(str(int(stats.get("edges", 0))))
            metric_vars["Weighted Calls"].set(str(int(stats.get("weighted_edges", 0))))
            metric_vars["Nodes With CPU"].set(str(int(stats.get("nodes_with_cpu", 0))))
            metric_vars["Feature Dim"].set(str(len(prepared.node_features[0]) if prepared.node_features else 0))

            status_var.set(
                f"Loaded {rpc_var.get().strip()} with {int(stats.get('nodes', 0))} nodes and {int(stats.get('edges', 0))} edges"
            )

            draw_graph()
            update_node_info(None)
            populate_edges()
        except Exception as exc:
            messagebox.showerror("Pipeline Error", str(exc))
            status_var.set("Failed to run pipeline")

    def set_train_info(text: str) -> None:
        train_info.configure(state="normal")
        train_info.delete("1.0", tk.END)
        train_info.insert(tk.END, text)
        train_info.configure(state="disabled")

    def on_train() -> None:
        try:
            raw_rpc = rpc_var.get().strip()
            rpc_candidates = [part.strip() for part in raw_rpc.split(",") if part.strip()]
            if not rpc_candidates:
                rpc_candidates = ["compose_ms_rpc_map.csv"]

            rpc_paths = [project_root / "data" / part for part in rpc_candidates]
            metrics_path = project_root / metrics_var.get().strip()
            model_path = project_root / model_var.get().strip()

            summary = train_with_rpc_files(rpc_paths, metrics_path, model_path)
            status_var.set(f"Model training completed and saved to {model_path}")

            set_train_info(
                "\n".join(
                    [
                        f"Model path: {model_path}",
                        f"Samples: {int(summary.get('samples', 0))}",
                        f"Train samples: {int(summary.get('train_samples', 0))}",
                        f"Test samples: {int(summary.get('test_samples', 0))}",
                        f"Train accuracy: {summary.get('train_accuracy', 0.0):.4f}",
                        f"Test accuracy: {summary.get('test_accuracy', 0.0):.4f}",
                        f"Test F1: {summary.get('test_f1', 0.0):.4f}",
                    ]
                )
            )
        except Exception as exc:
            messagebox.showerror("Training Error", str(exc))
            status_var.set("Model training failed")

    def on_resize(_: tk.Event) -> None:
        if state["prepared"] is not None:
            draw_graph()

    canvas.bind("<Configure>", on_resize)

    on_run()
    root.mainloop()


if __name__ == "__main__":
    launch_ui()
