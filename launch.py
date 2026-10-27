"""Cross-platform, one-command launch after installing requirements."""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    raise SystemExit(subprocess.call([
        sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("app.py")),
        "--server.address=127.0.0.1", "--server.headless=true", *sys.argv[1:],
    ]))
