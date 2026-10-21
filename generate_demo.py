import json
from pathlib import Path

from main import build_pdf


BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "examples" / "demo-input.json"
OUTPUT_PATH = BASE_DIR / "output" / "demo-report.pdf"


def main():
    with INPUT_PATH.open(encoding="utf-8") as input_file:
        payload = json.load(input_file)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(build_pdf(payload))
    print(f"Created {OUTPUT_PATH}")


if __name__ == "__main__":
    main()