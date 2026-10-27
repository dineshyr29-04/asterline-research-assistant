"""One-time developer utility; pypdf is needed only for this script."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SHA256 = "f63fc05cf43204485c98bd8fb6d89860a32c16a7e906bc90975e7c3954fe9fb1"


def main():
    from pypdf import PdfReader

    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/corpus.jsonl"))
    args = parser.parse_args()
    data = PdfReader(args.pdf).attachments["corpus.jsonl"][0]
    if hashlib.sha256(data).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Embedded corpus does not match the supplied candidate package")
    records = [json.loads(line) for line in data.splitlines() if line.strip()]
    assert len(records) == 75 and len({r["doc_id"] for r in records}) == 25
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(data)
    print(f"Extracted unchanged corpus: {len(records)} chunks; SHA256 {EXPECTED_SHA256}")


if __name__ == "__main__":
    main()
