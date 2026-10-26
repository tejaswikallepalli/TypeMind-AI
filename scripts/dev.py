#!/usr/bin/env python3
"""Unified Development Launcher for TypeMind AI (Backend & Frontend)."""

import os
import sys
import subprocess
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"


def run_backend(host: str = "127.0.0.1", port: int = 8000, reload: bool = True):
    """Launch the FastAPI backend server using uvicorn."""
    print(f"[TypeMind AI] Starting FastAPI backend on http://{host}:{port} ...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, cwd=str(BACKEND_DIR), env=env, check=True)
    except KeyboardInterrupt:
        print("\n[TypeMind AI] Backend shutdown gracefully.")


def run_frontend(host: str = "127.0.0.1", port: int = 5173):
    """Launch the React + TypeScript frontend using Vite."""
    print(f"[TypeMind AI] Starting React frontend on http://{host}:{port} ...")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    cmd = [npm_cmd, "run", "dev", "--", "--host", host, "--port", str(port)]
    try:
        subprocess.run(cmd, cwd=str(FRONTEND_DIR), check=True)
    except KeyboardInterrupt:
        print("\n[TypeMind AI] Frontend shutdown gracefully.")


def run_full_stack():
    """Launch both backend and frontend simultaneously."""
    print("=" * 60)
    print(" TypeMind AI — Starting Full-Stack Development Workspace")
    print("   Backend:  http://127.0.0.1:8000 (OpenAPI: /docs)")
    print("   Frontend: http://127.0.0.1:5173")
    print("=" * 60)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)

    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=str(BACKEND_DIR),
        env=env,
    )

    time.sleep(1.5)

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        cwd=str(FRONTEND_DIR),
    )

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\n[TypeMind AI] Terminating all development services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=2)
            frontend_proc.wait(timeout=2)
        except Exception:
            backend_proc.kill()
            frontend_proc.kill()
        print("[TypeMind AI] All services stopped.")


def run_all_tests():
    """Run all backend and frontend tests."""
    print("\n--- [1/2] Running Backend Tests (pytest) ---")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    py_res = subprocess.run([sys.executable, "-m", "pytest", "backend/tests", "-v"], cwd=str(ROOT_DIR), env=env)

    print("\n--- [2/2] Running Frontend Tests (vitest) ---")
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    fe_res = subprocess.run([npm_cmd, "test"], cwd=str(FRONTEND_DIR))

    if py_res.returncode == 0 and fe_res.returncode == 0:
        print("\nSUCCESS: All backend and frontend tests passed cleanly!")
    else:
        print("\nFAILURE: Some tests did not pass.")
        sys.exit(1)


if __name__ == "__main__":
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "full"
    if arg == "backend":
        run_backend()
    elif arg == "frontend":
        run_frontend()
    elif arg == "test":
        run_all_tests()
    elif arg in ("full", "all", "start"):
        run_full_stack()
    else:
        print("Usage: python scripts/dev.py [full | backend | frontend | test]")
