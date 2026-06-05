#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTDIR="${1:-$ROOT_DIR/artifacts/simulation/maniskill-sapien}"

cd "$ROOT_DIR/weld-experience-engine"
python - <<'PY' "$OUTDIR"
import sys
from pathlib import Path
from weldcore.simulation_bakeoff import run_maniskill_spike_pipeline

summary = run_maniskill_spike_pipeline(Path(sys.argv[1]))
print("=== ManiSkill/SAPIEN spike summary ===")
print(f"task_count: {summary['task_count']}")
print(f"completed: {summary['completed']}")
print(f"failed: {summary['failed']}")
print(f"failure_boundaries: {summary['failure_boundaries']}")
PY
