"""Export OpenAPI contract specification to a target JSON file."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure 'src' is discoverable on pythonpath
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from app.main import app

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATH = BASE_DIR.parent / "frontend" / "api-contract.json"


def export_contract(output_path: Path | str = DEFAULT_OUTPUT_PATH) -> Path:
    """Export the OpenAPI schema to a target JSON file.

    Args:
        output_path: Target destination path for the OpenAPI JSON file.

    Returns:
        The resolved Path where the contract was saved.
    """
    resolved_path = Path(output_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    openapi_schema = app.openapi()
    with open(resolved_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)

    logger.info("Successfully exported OpenAPI contract to '%s'", resolved_path)
    return resolved_path


def main() -> None:
    """Parse CLI arguments and trigger contract export."""
    parser = argparse.ArgumentParser(
        description="Export FastAPI OpenAPI contract to a JSON file."
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=None,
        help=f"Target file path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        type=Path,
        dest="flag_output",
        default=None,
        help="Target file path flag override.",
    )
    args = parser.parse_args()
    target_path = args.flag_output or args.output or DEFAULT_OUTPUT_PATH
    export_contract(target_path)


if __name__ == "__main__":
    main()
