from fastapi import FastAPI, UploadFile, File
import pandas as pd
import networkx as nx

app = FastAPI()

@app.post("/upload-data")
async def upload_data(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)

    # Create graph
    G = nx.from_pandas_edgelist(df, source="source", target="target")

    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges()
    }