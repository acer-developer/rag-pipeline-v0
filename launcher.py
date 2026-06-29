from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


PROJECT = Path(__file__).parent
VENV_PY = PROJECT / ".venv" / "Scripts" / "python.exe"
STREAMLIT_PORT = 8501
NGROK_API = "http://localhost:4040/api/tunnels"


def find_ngrok() -> Path | None:
    on_path = shutil.which("ngrok")
    if on_path:
        return Path(on_path)
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs",
        Path(os.environ.get("USERPROFILE", "")) / "scoop" / "apps",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")),
        Path("C:/Program Files (x86)"),
    ]
    for root in candidates:
        if not root.exists():
            continue
        try:
            for p in root.rglob("ngrok.exe"):
                return p
        except Exception:
            continue
    return None


def find_ollama() -> Path | None:
    on_path = shutil.which("ollama")
    if on_path:
        return Path(on_path)
    p = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
    return p if p.exists() else None


def kill_existing() -> None:
    print("Cleaning up previous instances...")
    subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], capture_output=True)
    ps_cmd = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" "
        "| Where-Object { $_.CommandLine -like '*streamlit*' } "
        "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
    time.sleep(2)


def wait_until_up(url: str, timeout: int = 90) -> bool:
    print(f"Waiting for {url} ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def get_ngrok_url() -> str | None:
    for _ in range(20):
        try:
            with urllib.request.urlopen(NGROK_API, timeout=2) as r:
                data = json.loads(r.read())
            tunnels = data.get("tunnels") or []
            for t in tunnels:
                if t.get("public_url", "").startswith("https://"):
                    return t["public_url"]
        except Exception:
            pass
        time.sleep(1)
    return None


def main() -> int:
    if not VENV_PY.exists():
        print(f"[ERROR] venv not found at {VENV_PY}")
        print("Run setup.bat first to create it.")
        input("Press Enter to exit...")
        return 1

    ollama = find_ollama()
    if not ollama:
        print("[WARN] Ollama not found. Install from https://ollama.com/download and pull a model:")
        print("  ollama pull llama3.1:8b")
        print("Continuing anyway - generation will fail without a running Ollama.")
        print()

    kill_existing()

    ngrok = find_ngrok()
    ngrok_proc = None
    if ngrok:
        print(f"Starting ngrok tunnel: {ngrok}")
        ngrok_proc = subprocess.Popen(
            [str(ngrok), "http", str(STREAMLIT_PORT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
    else:
        print("[WARN] ngrok not found in PATH or common locations.")
        print("       Install from https://ngrok.com/download then run:")
        print("       ngrok config add-authtoken <your-token>")

    print("Starting Streamlit...")
    streamlit_proc = subprocess.Popen(
        [str(VENV_PY), "-m", "streamlit", "run", "app.py",
         "--server.port", str(STREAMLIT_PORT), "--server.headless", "true"],
        cwd=str(PROJECT),
    )

    local_url = f"http://localhost:{STREAMLIT_PORT}"
    if wait_until_up(local_url, timeout=90):
        print(f"\nStreamlit is up at {local_url}")
        public_url = get_ngrok_url() if ngrok_proc else None
        if public_url:
            print(f"Public URL:  {public_url}")
        webbrowser.open(local_url)
    else:
        print("[ERROR] Streamlit did not start in 90 seconds.")

    print()
    print("Press Ctrl+C in this window to stop everything.")

    try:
        streamlit_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        try:
            streamlit_proc.terminate()
        except Exception:
            pass
        if ngrok_proc:
            try:
                ngrok_proc.terminate()
            except Exception:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
