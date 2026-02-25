import os
import sys
import tempfile
import subprocess
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Script Sandbox Executor")

class ExecuteRequest(BaseModel):
    script_content: str
    target_backend_url: str
    timeout: int = 5

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/execute")
def execute_script(req: ExecuteRequest):
    # Enforce a maximum timeout of 10s
    timeout = min(req.timeout, 10)
    
    # Write script content to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tf:
        tf.write(req.script_content.encode('utf-8'))
        temp_file_path = tf.name

    try:
        # Prepare environment variables
        env = os.environ.copy()
        env["MOCK_BACKEND_URL"] = req.target_backend_url
        # Disable writing bytecode inside sandbox
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        # Execute in a subprocess
        # In a real Docker container, this runs as the non-root user defined in the Dockerfile.
        # We cap stdout/stderr reading to 50KB to limit output size.
        process = subprocess.Popen(
            [sys.executable, temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return {
                "status": "TIMEOUT",
                "exit_code": -1,
                "stdout": stdout[:50000],
                "stderr": stderr[:50000] + "\n[Execution timed out after {} seconds]".format(timeout)
            }

        # Format outcome
        status = "SUCCESS" if exit_code == 0 else "FAILED"
        return {
            "status": status,
            "exit_code": exit_code,
            "stdout": stdout[:50000],
            "stderr": stderr[:50000]
        }

    except Exception as e:
        return {
            "status": "FAILED",
            "exit_code": -2,
            "stdout": "",
            "stderr": f"Sandbox error: {str(e)}"
        }
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005)
