from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path


PROJECT = Path(__file__).parent
VENV_PY = PROJECT / ".venv" / "Scripts" / "python.exe"
STREAMLIT_PORT = 8501
NGROK_PATHS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages" / "Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe" / "ngrok.exe",
    Path("ngrok.exe"),
]


def find_ngrok() -> Path | None:
    for p in NGROK_PATHS:
        if p.exists():
            return p
    return None


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


def wait_until_up(url: str, timeout: int = 60) -> bool:
    print(f"Waiting for Streamlit at {url} ...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def main() -> int:
    if not VENV_PY.exists():
        print(f"[ERROR] venv not found at {VENV_PY}")
        print("Run: uv venv --python 3.11 .venv && uv pip install --python .venv -r requirements.txt")
        input("Press Enter to exit...")
        return 1

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
        print("[WARN] ngrok not found - skipping public tunnel.")

    print("Starting Streamlit...")
    streamlit_proc = subprocess.Popen(
        [str(VENV_PY), "-m", "streamlit", "run", "app.py",
         "--server.port", str(STREAMLIT_PORT), "--server.headless", "true"],
        cwd=str(PROJECT),
    )

    if wait_until_up(f"http://localhost:{STREAMLIT_PORT}", timeout=60):
        print("Streamlit is up. Opening browser...")
        webbrowser.open(f"http://localhost:{STREAMLIT_PORT}")
    else:
        print("[ERROR] Streamlit did not start in 60 seconds.")

    print()
    print(" Local:  http://localhost:8501")
    print(" Public: https://donator-aged-enactment.ngrok-free.dev")
    print()
    print("Press Ctrl+C in this window to stop everything.")

    try:
        streamlit_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        streamlit_proc.terminate()
        if ngrok_proc:
            ngrok_proc.terminate()

    return 0


if __name__ == "__main__":
    sys.exit(main())
