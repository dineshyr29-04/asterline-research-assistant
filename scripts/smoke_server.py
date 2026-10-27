"""Check a running local Streamlit server without opening a browser."""
import argparse
import urllib.request


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    with urllib.request.urlopen(base + "/_stcore/health", timeout=10) as response:
        assert response.status == 200 and response.read().decode() == "ok"
    with urllib.request.urlopen(base, timeout=10) as response:
        assert response.status == 200 and b"streamlit" in response.read().lower()
    print(f"PASS: health and HTML endpoints at {base}")


if __name__ == "__main__":
    main()
