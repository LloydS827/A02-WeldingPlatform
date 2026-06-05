#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTDIR="${1:-$ROOT_DIR/artifacts/simulation/maniskill-sapien}"

cd "$ROOT_DIR/weld-experience-engine"
python -m weldcore.simulation_bakeoff.maniskill_pipeline --outdir "$OUTDIR"
python - <<'PY' "$OUTDIR"
import json
import sys
from pathlib import Path

summary = json.loads((Path(sys.argv[1]) / "run_summary.json").read_text(encoding="utf-8"))
print("=== ManiSkill/SAPIEN spike summary ===")
print(f"task_count: {summary['task_count']}")
print(f"completed: {summary['completed']}")
print(f"failed: {summary['failed']}")
print(f"failure_boundaries: {summary['failure_boundaries']}")
PY
