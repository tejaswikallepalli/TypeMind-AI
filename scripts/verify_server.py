"""Verification script that runs live server startup and verifies all Phase 5 API endpoints."""

import os
import sys
import time
import subprocess
import httpx
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"

def verify_live_server():
    print("[1/7] Spawning live Uvicorn backend server on http://127.0.0.1:8000 ...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)

    python_exe = sys.executable
    server_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        url_health = "http://127.0.0.1:8000/health"
        url_root = "http://127.0.0.1:8000/"
        url_info = "http://127.0.0.1:8000/api/v1/info"
        url_categories = "http://127.0.0.1:8000/api/v1/diagnostics/categories"
        url_model_info = "http://127.0.0.1:8000/api/v1/model/info"
        url_analyze = "http://127.0.0.1:8000/api/v1/analyze"

        # Wait up to 10 seconds for server to be responsive
        ready = False
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                r = httpx.get(url_health, timeout=1.0)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.5)

        if not ready:
            print("ERROR: Server failed to start within timeout.")
            stdout, stderr = server_process.communicate(timeout=2)
            print(f"Server STDOUT:\n{stdout}")
            print(f"Server STDERR:\n{stderr}")
            sys.exit(1)

        print("[2/7] GET /health check:")
        r_health = httpx.get(url_health)
        print(f"  Status: {r_health.status_code}")
        print(f"  Body:   {r_health.json()}")
        print(f"  X-Request-ID: {r_health.headers.get('X-Request-ID')}")
        assert r_health.status_code == 200
        assert r_health.json()["status"] == "healthy"
        assert "X-Request-ID" in r_health.headers

        print("[3/7] GET / root check:")
        r_root = httpx.get(url_root)
        print(f"  Status: {r_root.status_code}")
        print(f"  Body:   {r_root.json()}")
        assert r_root.status_code == 200
        assert r_root.json()["name"] == "TypeMind AI"

        print("[4/7] GET /api/v1/info check:")
        r_info = httpx.get(url_info)
        print(f"  Status: {r_info.status_code}")
        print(f"  Body:   {r_info.json()}")
        assert r_info.status_code == 200
        assert r_info.json()["project_name"] == "TypeMind AI"

        print("[5/7] GET /api/v1/diagnostics/categories check:")
        r_cats = httpx.get(url_categories)
        print(f"  Status: {r_cats.status_code}")
        cats_body = r_cats.json()
        print(f"  Total Categories: {cats_body['total_categories']}")
        assert r_cats.status_code == 200
        assert cats_body["total_categories"] >= 7
        codes = [c["code"] for c in cats_body["categories"]]
        assert "type_mismatch" in codes
        assert "syntax_error" in codes

        print("[6/7] GET /api/v1/model/info check:")
        r_model = httpx.get(url_model_info)
        print(f"  Status: {r_model.status_code}")
        model_body = r_model.json()
        print(f"  Model Status: {model_body['status']}")
        print(f"  Architecture: {model_body.get('model_architecture')}")
        print(f"  Classes Count: {len(model_body.get('classes', []))}")
        assert r_model.status_code == 200
        assert model_body["status"] in ("loaded", "unavailable")

        print("[7/7] POST /api/v1/analyze live semantic analysis check:")
        payload = {
            "source_code": "def greet(name: str) -> str:\n    return name + 42\n",
            "file_path": "test_greeting.py",
        }
        r_analyze = httpx.post(url_analyze, json=payload)
        print(f"  Status: {r_analyze.status_code}")
        body = r_analyze.json()
        print(f"  Status Field:   {body['status']}")
        print(f"  Findings Count: {len(body['findings'])}")
        print(f"  Rule ID:        {body['findings'][0]['rule_id']}")
        print(f"  Origin:         {body['findings'][0]['origin']}")
        print(f"  Fixes Count:    {len(body['findings'][0]['suggested_fixes'])}")
        assert r_analyze.status_code == 200
        assert body["status"] == "success"
        assert len(body["findings"]) == 1
        assert body["findings"][0]["rule_id"] == "TM001_STRING_NUMBER_CONCAT"
        assert len(body["findings"][0]["suggested_fixes"]) >= 1

        print("\nSUCCESS: All 5 Phase 5 backend endpoints responded and verified live!")

    finally:
        print("Terminating server process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("Server shutdown completed.")

if __name__ == "__main__":
    verify_live_server()
