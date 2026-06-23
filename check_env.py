"""
Verify your .env keys are loaded. Prints only the status of each key,
never the secret value itself.

Run:  python check_env.py
"""
import os

import config  # importing this loads the .env file


def status(name: str) -> str:
    val = os.getenv(name, "")
    if not val or val.startswith("paste-"):
        return "NOT SET (still placeholder)"
    return f"set  (len {len(val)}, starts '{val[:5]}...')"


for key in ["CHROMA_API_KEY", "CHROMA_TENANT", "CHROMA_DATABASE", "ANTHROPIC_API_KEY"]:
    print(f"{key:18} : {status(key)}")
