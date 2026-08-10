"""Generate the reviewed OpenAPI artifact deterministically (JSON is valid YAML)."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

OUTPUT = Path(__file__).resolve().parents[1] / "openapi.yaml"


def rendered() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> None:
    OUTPUT.write_text(rendered(), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
