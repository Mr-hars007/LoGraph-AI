"""FastAPI backend for graph preview, upload, and pipeline integration.

Provides endpoints used by the web UI and local testing workflows.
"""

from pathlib import Path
import sys

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import networkx as nx

app = FastAPI()

# Allow importing modules from gnn-service folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GNN_SERVICE_DIR = PROJECT_ROOT / "gnn-service"
if str(GNN_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(GNN_SERVICE_DIR))

try:
    from main import prepare_graph_data  # type: ignore
except Exception:
    prepare_graph_data = None


@app.get("/preview", response_class=HTMLResponse)
def preview_page() -> str:
        return """
<!doctype html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>LoGraph-AI Preview</title>
    <style>
        :root {
            --bg: #f3f6f9;
            --card: #ffffff;
            --text: #172026;
            --muted: #5b6b77;
            --accent: #0a84ff;
            --line: #d9e2ea;
        }
        body {
            margin: 0;
            font-family: Segoe UI, Tahoma, sans-serif;
            background: radial-gradient(circle at 0% 0%, #dfefff 0, var(--bg) 45%);
            color: var(--text);
        }
        .wrap {
            max-width: 920px;
            margin: 40px auto;
            padding: 0 16px;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(10, 132, 255, 0.08);
            padding: 20px;
            margin-bottom: 16px;
        }
        h1 { margin: 0 0 6px; font-size: 1.4rem; }
        p { margin: 0 0 14px; color: var(--muted); }
        .row { display: flex; gap: 12px; flex-wrap: wrap; }
        input, button {
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid var(--line);
            font-size: 14px;
        }
        input { min-width: 240px; }
        button {
            background: var(--accent);
            color: #fff;
            border-color: var(--accent);
            cursor: pointer;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 14px;
        }
        .metric {
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 10px;
        }
        .k { color: var(--muted); font-size: 12px; }
        .v { font-weight: 700; font-size: 1.1rem; }
        ul { margin: 10px 0 0 18px; }
        #err { color: #b42318; margin-top: 8px; }
    </style>
</head>
<body>
    <div class=\"wrap\">
        <div class=\"card\">
            <h1>LoGraph-AI Working Preview</h1>
            <p>This page calls <code>/prepare-graph</code> and shows live pipeline output.</p>
            <div class=\"row\">
                <input id=\"rpc\" value=\"compose_ms_rpc_map.csv\" />
                <input id=\"metrics\" value=\"data\" />
                <button id=\"run\">Run Pipeline</button>
            </div>
            <div id=\"err\"></div>
            <div class=\"grid\" id=\"metricsGrid\"></div>
            <div class=\"card\" style=\"margin-top:12px;\">
                <div class=\"k\">Sample Nodes</div>
                <ul id=\"nodes\"></ul>
            </div>
        </div>
    </div>

    <script>
        const grid = document.getElementById('metricsGrid');
        const nodes = document.getElementById('nodes');
        const err = document.getElementById('err');

        function addMetric(name, value) {
            const box = document.createElement('div');
            box.className = 'metric';
            box.innerHTML = `<div class=\"k\">${name}</div><div class=\"v\">${value}</div>`;
            grid.appendChild(box);
        }

        async function runPipeline() {
            err.textContent = '';
            grid.innerHTML = '';
            nodes.innerHTML = '';

            const rpc = document.getElementById('rpc').value.trim();
            const metricsDir = document.getElementById('metrics').value.trim();

            try {
                const url = `/prepare-graph?rpc_map_file=${encodeURIComponent(rpc)}&metrics_dir=${encodeURIComponent(metricsDir)}`;
                const res = await fetch(url);
                const data = await res.json();

                if (!res.ok) {
                    throw new Error(data.detail || 'Pipeline failed');
                }

                addMetric('Nodes', Number(data.stats.nodes || 0));
                addMetric('Edges', Number(data.stats.edges || 0));
                addMetric('Weighted Calls', Number(data.stats.weighted_edges || 0));
                addMetric('Nodes With CPU', Number(data.stats.nodes_with_cpu || 0));
                addMetric('Feature Dim', Number(data.feature_dim || 0));

                (data.sample_nodes || []).forEach((n) => {
                    const li = document.createElement('li');
                    li.textContent = n;
                    nodes.appendChild(li);
                });
            } catch (e) {
                err.textContent = e.message;
            }
        }

        document.getElementById('run').addEventListener('click', runPipeline);
        runPipeline();
    </script>
</body>
</html>
"""

@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)

    # Create graph
    G = nx.from_pandas_edgelist(df, source="source", target="target")

    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges()
    }


@app.get("/prepare-graph")
async def prepare_graph(
    rpc_map_file: str = "compose_ms_rpc_map.csv",
    metrics_dir: str = "data",
):
    """Prepare graph and node features from project datasets for GNN training."""
    if prepare_graph_data is None:
        raise HTTPException(
            status_code=500,
            detail="GNN pipeline import failed. Ensure gnn-service dependencies are installed.",
        )

    rpc_map_path = PROJECT_ROOT / "data" / rpc_map_file
    metrics_path = PROJECT_ROOT / metrics_dir

    if not rpc_map_path.exists():
        raise HTTPException(status_code=404, detail=f"RPC map not found: {rpc_map_path.name}")
    if not metrics_path.exists():
        raise HTTPException(status_code=404, detail=f"Metrics directory not found: {metrics_path}")

    try:
        prepared = prepare_graph_data(rpc_map_path, metrics_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc

    return {
        "stats": prepared.stats,
        "node_count": len(prepared.node_to_index),
        "edge_count": len(prepared.edge_index[0]) if prepared.edge_index else 0,
        "feature_dim": len(prepared.node_features[0]) if prepared.node_features else 0,
        "sample_nodes": list(prepared.node_to_index.keys())[:5],
    }