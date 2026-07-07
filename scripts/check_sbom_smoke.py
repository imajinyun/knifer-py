from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOCAL_CYCLONEDX = PROJECT_ROOT / ".venv" / "bin" / "cyclonedx-py"
CYCLONEDX = str(LOCAL_CYCLONEDX) if LOCAL_CYCLONEDX.exists() else "cyclonedx-py"
LOCAL_VENV = PROJECT_ROOT / ".venv"
DEFAULT_OUTPUT = PROJECT_ROOT / "sbom.cdx.json"


def _run(command: list[str]) -> None:
    print(f"==> {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def generate_sbom(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            CYCLONEDX,
            "environment",
            str(LOCAL_VENV) if LOCAL_VENV.exists() else sys.executable,
            "--mc-type",
            "library",
            "--of",
            "JSON",
            "--output-file",
            str(output.relative_to(PROJECT_ROOT)),
        ]
    )


def _json_obj(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"SBOM {field} must be a JSON object")
    return value


def validate_sbom(path: Path) -> None:
    data = _json_obj(json.loads(path.read_text(encoding="utf-8")), "root")
    if data.get("bomFormat") != "CycloneDX":
        raise ValueError("SBOM bomFormat must be CycloneDX")
    if not isinstance(data.get("specVersion"), str) or not data["specVersion"]:
        raise ValueError("SBOM specVersion must be present")

    metadata = _json_obj(data.get("metadata", {}), "metadata")
    metadata_component = metadata.get("component", {})
    if metadata_component:
        _json_obj(metadata_component, "metadata.component")

    components = data.get("components")
    if not isinstance(components, list):
        raise ValueError("SBOM components must be a list")
    if not components:
        raise ValueError("SBOM components must not be empty")

    names = {
        component.get("name")
        for component in components
        if isinstance(component, dict) and isinstance(component.get("name"), str)
    }
    metadata_name = (
        metadata_component.get("name") if isinstance(metadata_component, dict) else None
    )
    if metadata_name != "kniferpy" and "kniferpy" not in names:
        raise ValueError("SBOM must identify the kniferpy package")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and validate a CycloneDX SBOM.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    try:
        generate_sbom(args.output)
        validate_sbom(args.output)
    except (OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as exc:
        print(f"SBOM smoke check failed: {exc}", file=sys.stderr)
        return 1

    print(f"SBOM smoke check passed: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
