#!/usr/bin/env python3
"""Unified launcher for Turbo ElSayed.

Usage:
    python start_app.py                 # start Streamlit Web UI
    python start_app.py --mode api     # start FastAPI/Uvicorn
    python start_app.py --mode webui   # explicitly start Streamlit

The optional streamlit_tour package is not imported here or by the Web UI.
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
WEBUI_FILE = ROOT_DIR / "webui" / "Main.py"
ASGI_MODULE = "app.asgi:app"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start Turbo ElSayed")
    parser.add_argument(
        "--mode",
        choices=("webui", "api"),
        default=os.getenv("TURBO_MODE", "webui").lower(),
        help="webui starts Streamlit; api starts FastAPI/Uvicorn",
    )
    parser.add_argument("--host", default=None, help="Override the listening host")
    parser.add_argument("--port", type=int, default=None, help="Override the listening port")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser for Web UI")
    parser.add_argument("--reload", action="store_true", help="Enable Uvicorn reload in API mode")
    return parser


def _read_config() -> tuple[str, int, bool]:
    """Read config lazily so the launcher can show a useful dependency error."""
    try:
        from app.config import config

        return config.listen_host, int(config.listen_port), bool(config.reload_debug)
    except Exception as exc:
        print(f"[Turbo ElSayed] Could not load config.toml: {exc}", file=sys.stderr)
        return "0.0.0.0", 8501, False


def _available_port(host: str, preferred: int, attempts: int = 100) -> int:
    for port in range(preferred, preferred + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No available port found from {preferred} to {preferred + attempts - 1}")


def _python_command(module: str) -> list[str]:
    return [sys.executable, "-m", module]


def _run_webui(host: str, port: int, no_browser: bool) -> int:
    if not WEBUI_FILE.exists():
        raise FileNotFoundError(f"Web UI file not found: {WEBUI_FILE}")
    if shutil.which("streamlit") is None:
        print(
            "Streamlit is not installed. Run: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 2

    selected_port = _available_port(host, port)
    if selected_port != port:
        print(f"[Turbo ElSayed] Port {port} is busy; using {selected_port} instead.")

    command = _python_command("streamlit") + [
        "run",
        str(WEBUI_FILE),
        f"--server.address={host}",
        f"--server.port={selected_port}",
        f"--browser.gatherUsageStats=False",
        "--client.toolbarMode=minimal",
        "--logger.hideWelcomeMessage=True",
    ]
    if no_browser:
        command.append("--server.headless=true")

    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    print(f"[Turbo ElSayed] Web UI: http://{display_host}:{selected_port}")
    return subprocess.call(command, cwd=ROOT_DIR, env={**os.environ, "PYTHONPATH": str(ROOT_DIR)})


def _run_api(host: str, port: int, reload_enabled: bool) -> int:
    try:
        import uvicorn  # noqa: F401
    except ImportError:
        print(
            "Uvicorn is not installed. Run: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 2

    print(f"[Turbo ElSayed] API: http://{host}:{port}/docs")
    import uvicorn

    uvicorn.run(
        ASGI_MODULE,
        host=host,
        port=port,
        reload=reload_enabled,
        app_dir=str(ROOT_DIR),
        log_level="info",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    configured_host, configured_port, configured_reload = _read_config()
    host = (
        args.host
        or os.getenv("TURBO_HOST")
        or os.getenv("MPT_WEBUI_HOST")
        or configured_host
    )
    port = args.port or int(
        os.getenv("TURBO_PORT")
        or os.getenv("MPT_WEBUI_PORT")
        or configured_port
    )

    if not 1 <= port <= 65535:
        print(f"Invalid port: {port}", file=sys.stderr)
        return 2

    os.chdir(ROOT_DIR)
    if args.mode == "api":
        return _run_api(host, port, args.reload or configured_reload)
    return _run_webui(host, port, args.no_browser)


if __name__ == "__main__":
    raise SystemExit(main())
