# WeldSkillUnit 仿真最小验证与数字资产沉淀 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable `WeldSkillUnit` simulation bake-off layer that turns simulation attempts into auditable digital assets.

**Architecture:** Add a small `weldcore.simulation_bakeoff` package instead of expanding existing simlite or ingest modules. The new package defines task specs, adapter result boundaries, evidence bundles, route attempts, scorecards, and a report command while reusing existing `SimulationRunRecord`, `SkillDataset`, Rerun optional replay, and simulation evidence conventions.

**Tech Stack:** Python 3.10+, dataclasses, enum, pathlib, json, pytest, existing `weldcore` models, existing optional `rerun-sdk` boundary, Markdown/HTML docs, `uv`.

---

## 0. Scope Boundary

Design spec:

- `docs/superpowers/specs/2026-06-04-WeldSkillUnit仿真最小验证与数字资产沉淀-design.md`

This plan implements the spec goals for the current stage:

- Define `SimulationTaskSpec`, `SimulatorAdapterResult`, and `SimulationEvidenceBundle`.
- Generate two default `SimulationTaskSpec` objects from the two core `WeldSkillUnit` candidates.
- Produce R0/simlite baseline evidence as the stable runnable path.
- Attempt the same two tasks through ManiSkill/SAPIEN and Gazebo/MoveIt adapter spikes.
- If optional simulator dependencies are absent, record standardized failure boundaries instead of failing default tests.
- Aggregate all attempts into scorecards and evidence bundles.
- Keep Rerun optional and use it only as an evidence replay layer.
- Add a report command that writes runtime and docs evidence for the bake-off.

It does not:

- Choose a final simulator.
- Install or require ManiSkill, SAPIEN, Gazebo, MoveIt, Isaac Lab, RoboDK, RobotStudio, or Process Simulate.
- Implement complete external simulator adapters.
- Implement molten-pool, thermal, metallurgical, weld-pool, or real forming simulation.
- Claim real welding quality validation.
- Generate or replace WPS/PQR.
- Connect a real robot, welder, PLC, or field bus.

---

## 1. File Structure

### New Package

- Create: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
  - Public exports for bake-off models, default tasks, adapter attempts, evidence building, and runner.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/model.py`
  - `SimulationPathPoint`, `SimulationTaskSpec`, `SimulatorAdapterResult`, `SimulationEvidenceBundle`, `BakeoffScorecard`.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/task_specs.py`
  - Convert first-batch core `WeldSkillUnit` values into two default `SimulationTaskSpec` objects.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/adapters.py`
  - R0/simlite reference adapter plus ManiSkill/SAPIEN and Gazebo/MoveIt optional dependency spikes.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/evidence.py`
  - Convert adapter results into existing `SimulationRunRecord`, `SkillDataset`, and `SimulationEvidenceBundle`.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/bakeoff.py`
  - Run the full minimal bake-off, build scorecards, and produce serializable summaries.

### New Report

- Create: `weld-experience-engine/weldcore/report/simulation_bakeoff_report.py`
  - CLI and callable report that writes JSON and Markdown evidence.

### Tests

- Create: `weld-experience-engine/tests/test_simulation_bakeoff_models.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_task_specs.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_adapters.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_evidence.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_runner.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_report.py`

### Docs

- Modify: `README.md`
  - Add the new bake-off report command and clarify it is selection evidence, not final simulator selection.
- Modify: `details.md`
  - Update the next-stage ledger so non-technical readers understand the bake-off step.
- Modify: `README.html`
  - Refresh HTML reading copy after README update.
- Modify: `details.html`
  - Refresh HTML reading copy after details update.
- Modify: `docs/simulation/robot-like-simulation-route.md`
  - Add a short note that the first bake-off implementation uses R0 baseline plus R2 route attempts.

---

## Task 0: Baseline Safety Check

**Files:**
- Read only.

- [ ] **Step 1: Confirm branch and working tree**

Run from repo root:

```bash
git status --short --branch
```

Expected:

- Current branch shown.
- Existing untracked `weld-experience-engine/uv.lock` may appear. Do not stage, delete, or modify it unless separately instructed.
- Local `main` may be ahead of `origin/main` by the spec commit.

- [ ] **Step 2: Confirm approved spec exists**

Run:

```bash
test -f docs/superpowers/specs/2026-06-04-WeldSkillUnit仿真最小验证与数字资产沉淀-design.md
```

Expected: exit code 0.

- [ ] **Step 3: Run baseline tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass. Current known baseline: `166 passed`.

- [ ] **Step 4: Commit nothing**

No commit for this task.

---

## Task 1: Add Bake-off Data Models

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/model.py`
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_models.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_simulation_bakeoff_models.py`:

```python
import json

from weldcore.model import SimulationRunRecord, SimulationRunStatus, SimulatorName
from weldcore.simulation_bakeoff import (
    BakeoffScorecard,
    SimulationEvidenceBundle,
    SimulationPathPoint,
    SimulationTaskSpec,
    SimulatorAdapterResult,
)


def test_simulation_task_spec_serializes_minimal_contract():
    spec = SimulationTaskSpec(
        task_id="task-long-straight-horizontal-tracking",
        unit_id="long-straight-horizontal-tracking",
        name="长直横焊沿缝跟踪仿真任务",
        seam_path=(
            SimulationPathPoint(t=0.0, x=0.0, y=0.0, z=0.0, rx=0.0, ry=10.0, rz=0.0),
            SimulationPathPoint(t=1.0, x=100.0, y=0.0, z=0.0, rx=0.0, ry=10.0, rz=0.0),
        ),
        tcp_frame="torch_tcp",
        tool_orientation_constraint=("work_angle_stable", "travel_angle_stable"),
        motion_constraint=("path_continuity", "speed_stability"),
        robot_constraint=("ik_reachability", "collision_check"),
        expected_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
        evaluation_metrics=("path_continuity", "posture_stability", "speed_stability"),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
    )

    data = spec.to_dict()

    assert data["task_id"] == "task-long-straight-horizontal-tracking"
    assert data["unit_id"] == "long-straight-horizontal-tracking"
    assert data["seam_path"][1]["x"] == 100.0
    assert data["tool_orientation_constraint"] == [
        "work_angle_stable",
        "travel_angle_stable",
    ]
    assert data["out_of_scope"] == ["real_welding_quality", "WPS/PQR"]


def test_adapter_result_serializes_success_and_failure_boundary():
    result = SimulatorAdapterResult(
        adapter_name="gazebo_moveit",
        task_id="task-corner-horizontal-transition",
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        planning_result={"attempted": True},
        failure_boundary=("optional_dependency_missing", "no_moveit_runtime"),
        metrics={"path_continuity": 0.0},
        artifacts={"report": "simulation_bakeoff_report_out/report.md"},
        evidence_notes=("same_task_attempted", "not_final_simulator_selection"),
    )

    data = result.to_dict()

    assert data["adapter_name"] == "gazebo_moveit"
    assert data["status"] == "failed"
    assert data["failure_boundary"] == [
        "optional_dependency_missing",
        "no_moveit_runtime",
    ]
    assert data["metrics"]["path_continuity"] == 0.0


def test_evidence_bundle_reuses_existing_run_record_contract():
    task = SimulationTaskSpec(
        task_id="task-long-straight-horizontal-tracking",
        unit_id="long-straight-horizontal-tracking",
        name="长直横焊沿缝跟踪仿真任务",
        seam_path=(SimulationPathPoint(t=0.0, x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0),),
        tcp_frame="torch_tcp",
        tool_orientation_constraint=("stable",),
        motion_constraint=("continuous",),
        robot_constraint=("ik",),
        expected_outputs=("tcp_trajectory",),
        evaluation_metrics=("path_continuity",),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
    )
    result = SimulatorAdapterResult(
        adapter_name="simlite_reference",
        task_id=task.task_id,
        status="completed",
        tcp_trajectory=task.seam_path,
        tool_orientation=task.seam_path,
        planning_result={"attempted": True, "task_status": "completed"},
        failure_boundary=(),
        metrics={"path_continuity": 1.0},
        artifacts={},
        evidence_notes=("r0_baseline",),
    )
    run_record = SimulationRunRecord(
        simulation_run_id="run-simlite-reference-task-long-straight-horizontal-tracking",
        input_id=task.task_id,
        simulator=SimulatorName.SIMLITE,
        simulator_version="0.1",
        adapter_version="bakeoff-v0.1",
        seed=None,
        sample_count=1,
        status=SimulationRunStatus.COMPLETED,
        created_at="2026-06-04T00:00:00Z",
        completed_at="2026-06-04T00:00:00Z",
        output_bundle_uris=[],
        boundary_notes=["not final simulator selection"],
    )
    bundle = SimulationEvidenceBundle(
        bundle_id="evidence-simlite-reference-task-long-straight-horizontal-tracking",
        task_spec=task,
        adapter_result=result,
        run_record=run_record,
        dataset=None,
        rerun_replay_uri=None,
        rerun_replay_status="not_attempted",
        rerun_notes=("rerun_optional_not_attempted_by_evidence_builder",),
        bakeoff_score={"digital_asset_score": 1.0},
    )

    data = bundle.to_dict()

    assert data["run_record"]["simulator"] == "simlite"
    assert data["adapter_result"]["status"] == "completed"
    assert data["dataset"] is None
    assert data["rerun_replay_status"] == "not_attempted"
    assert data["rerun_notes"] == ["rerun_optional_not_attempted_by_evidence_builder"]
    assert "SimulationOutputBundle" not in json.dumps(data)


def test_scorecard_declares_no_final_selection():
    scorecard = BakeoffScorecard(
        dimension_weights={
            "digital_asset_writeback": 0.35,
            "robot_executability": 0.30,
            "skill_unit_expression": 0.20,
            "engineering_access_cost": 0.15,
        },
        route_dimension_scores={
            "simlite_reference": {
                "digital_asset_writeback": 1.0,
                "robot_executability": 0.4,
                "skill_unit_expression": 1.0,
                "engineering_access_cost": 1.0,
            },
            "maniskill_sapien": {
                "digital_asset_writeback": 0.0,
                "robot_executability": 0.25,
                "skill_unit_expression": 1.0,
                "engineering_access_cost": 0.25,
            },
        },
        route_scores={"simlite_reference": 0.82, "maniskill_sapien": 0.3125},
        attempted_task_ids=("task-a", "task-b"),
        recommendation="continue_with_r0_baseline_and_external_spikes",
        final_simulator_selected=False,
        evidence_notes=("not_final_simulator_selection",),
    )

    data = scorecard.to_dict()

    assert data["final_simulator_selected"] is False
    assert data["attempted_task_ids"] == ["task-a", "task-b"]
    assert data["dimension_weights"] == {
        "digital_asset_writeback": 0.35,
        "robot_executability": 0.30,
        "skill_unit_expression": 0.20,
        "engineering_access_cost": 0.15,
    }
    assert data["route_dimension_scores"]["simlite_reference"]["digital_asset_writeback"] == 1.0
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_models.py
```

Expected: FAIL because `weldcore.simulation_bakeoff` does not exist.

- [ ] **Step 3: Create minimal model implementation**

Create `weld-experience-engine/weldcore/simulation_bakeoff/model.py` with frozen dataclasses:

- `SimulationPathPoint`
- `SimulationTaskSpec`
- `SimulatorAdapterResult`
- `SimulationEvidenceBundle`
- `BakeoffScorecard`

Implementation requirements:

- Use `dataclasses.asdict`.
- Use a private `_jsonable(value)` helper.
- Convert tuples to lists in `to_dict()`.
- Convert enum values via `.value`.
- If a field has a `to_dict()` method, use it.
- `SimulationEvidenceBundle.dataset` is `SkillDataset | None`.
- `SimulationEvidenceBundle.rerun_replay_uri` is `str | None`.
- `SimulationEvidenceBundle.rerun_replay_status` is one of `"not_attempted"`, `"logged"`, or `"skipped"`.
- `SimulationEvidenceBundle.rerun_notes` records the replay entrance or skip reason so evidence remains auditable without `rerun-sdk`.
- `BakeoffScorecard` must include:
  - `dimension_weights`
  - `route_dimension_scores`
  - `route_scores`
  - `attempted_task_ids`
  - `recommendation`
  - `final_simulator_selected`
  - `evidence_notes`
- `dimension_weights` must preserve the spec weights:
  - `digital_asset_writeback`: 0.35
  - `robot_executability`: 0.30
  - `skill_unit_expression`: 0.20
  - `engineering_access_cost`: 0.15
- Do not add molten-pool, thermal, metallurgy, quality validation, or WPS/PQR fields.

Use this public API shape:

```python
@dataclass(frozen=True)
class SimulationPathPoint:
    t: float
    x: float
    y: float
    z: float
    rx: float
    ry: float
    rz: float


@dataclass(frozen=True)
class SimulationTaskSpec:
    task_id: str
    unit_id: str
    name: str
    seam_path: tuple[SimulationPathPoint, ...]
    tcp_frame: str
    tool_orientation_constraint: tuple[str, ...]
    motion_constraint: tuple[str, ...]
    robot_constraint: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    evaluation_metrics: tuple[str, ...]
    out_of_scope: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]: ...
```

Use analogous `to_dict()` methods for the other dataclasses.

- [ ] **Step 4: Create package exports**

Create `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py` exporting:

- `BakeoffScorecard`
- `SimulationEvidenceBundle`
- `SimulationPathPoint`
- `SimulationTaskSpec`
- `SimulatorAdapterResult`

- [ ] **Step 5: Run GREEN tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_models.py tests/test_simulation_io_models.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff weld-experience-engine/tests/test_simulation_bakeoff_models.py
git commit -m "feat: add simulation bakeoff models"
```

---

## Task 2: Generate SimulationTaskSpec From Core WeldSkillUnits

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/task_specs.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_task_specs.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_simulation_bakeoff_task_specs.py`:

```python
import json

from weldcore.simulation_bakeoff import default_simulation_task_specs


def test_default_simulation_task_specs_cover_same_two_core_units():
    specs = default_simulation_task_specs()
    task_ids = {spec.task_id for spec in specs}
    unit_ids = {spec.unit_id for spec in specs}

    assert task_ids == {
        "task-long-straight-horizontal-tracking",
        "task-corner-horizontal-transition",
    }
    assert unit_ids == {
        "long-straight-horizontal-tracking",
        "corner-horizontal-transition",
    }
    assert "u-seam-vertical-extension" not in unit_ids


def test_task_specs_have_paths_constraints_outputs_and_metrics():
    specs = default_simulation_task_specs()

    for spec in specs:
        data = spec.to_dict()
        assert data["tcp_frame"] == "torch_tcp"
        assert len(data["seam_path"]) >= 3
        assert "tcp_trajectory" in data["expected_outputs"]
        assert "tool_orientation" in data["expected_outputs"]
        assert "task_status" in data["expected_outputs"]
        assert "path_continuity" in data["evaluation_metrics"]
        assert "ik_reachability" in data["robot_constraint"]
        assert "collision_check" in data["robot_constraint"]
        assert "real_welding_quality" in data["out_of_scope"]
        assert "WPS/PQR" in data["out_of_scope"]


def test_task_specs_exclude_forbidden_physics_terms():
    payload = json.dumps(
        [spec.to_dict() for spec in default_simulation_task_specs()],
        ensure_ascii=False,
    ).lower()

    for forbidden in ("molten", "weld_pool", "thermal", "metallurgy", "熔池", "热过程", "冶金"):
        assert forbidden not in payload
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_task_specs.py
```

Expected: FAIL because `default_simulation_task_specs` does not exist.

- [ ] **Step 3: Implement task spec generation**

Create `weld-experience-engine/weldcore/simulation_bakeoff/task_specs.py`.

Implementation requirements:

- Import `CORNER_HORIZONTAL_TRANSITION` and `LONG_STRAIGHT_HORIZONTAL_TRACKING`.
- Return exactly two specs in `DEFAULT_SIMULATION_TASK_SPECS`.
- Use deterministic path points.
- Long-straight path: straight line, at least 5 points.
- Corner path: at least 5 points with a turn.
- No U-seam default task.
- No molten/thermal/metallurgy terms.

Public API:

```python
DEFAULT_SIMULATION_TASK_SPECS = (...)

def default_simulation_task_specs() -> tuple[SimulationTaskSpec, ...]:
    return DEFAULT_SIMULATION_TASK_SPECS
```

- [ ] **Step 4: Update package exports**

Modify `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py` to export:

- `DEFAULT_SIMULATION_TASK_SPECS`
- `default_simulation_task_specs`

- [ ] **Step 5: Run GREEN tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_task_specs.py tests/test_skill_unit_model.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff weld-experience-engine/tests/test_simulation_bakeoff_task_specs.py
git commit -m "feat: add weld skill unit simulation task specs"
```

---

## Task 3: Add Adapter Attempts And R0 Baseline

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/adapters.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_adapters.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_simulation_bakeoff_adapters.py`:

```python
from weldcore.simulation_bakeoff import (
    attempt_gazebo_moveit,
    attempt_maniskill_sapien,
    default_simulation_task_specs,
    run_simlite_reference,
)


def test_simlite_reference_completes_each_default_task():
    for task_spec in default_simulation_task_specs():
        result = run_simlite_reference(task_spec)

        assert result.adapter_name == "simlite_reference"
        assert result.task_id == task_spec.task_id
        assert result.status == "completed"
        assert len(result.tcp_trajectory) == len(task_spec.seam_path)
        assert result.failure_boundary == ()
        assert result.metrics["path_continuity"] == 1.0
        assert result.planning_result["task_status"] == "completed"
        assert "r0_baseline" in result.evidence_notes


def test_external_adapter_spikes_attempt_same_task_and_return_standard_boundary():
    task_spec = default_simulation_task_specs()[0]

    for attempt in (attempt_maniskill_sapien, attempt_gazebo_moveit):
        result = attempt(task_spec)

        assert result.task_id == task_spec.task_id
        assert result.status in {"completed", "failed"}
        assert result.planning_result["attempted"] is True
        assert "not_final_simulator_selection" in result.evidence_notes
        if result.status == "failed":
            assert result.tcp_trajectory == ()
            assert result.failure_boundary
            assert result.failure_boundary[0] in {
                "optional_dependency_missing",
                "external_spike_not_executed",
            }
        if result.status == "completed":
            assert len(result.tcp_trajectory) == len(task_spec.seam_path)
            assert len(result.tool_orientation) == len(task_spec.seam_path)
            assert result.planning_result["validated_task_contract"] is True
            assert result.planning_result["task_status"] == "completed"
            assert result.metrics["same_task_attempted"] == 1.0
            assert result.metrics["task_contract_outputs_ready"] == 1.0


def test_external_adapter_names_are_stable():
    task_spec = default_simulation_task_specs()[0]

    assert attempt_maniskill_sapien(task_spec).adapter_name == "maniskill_sapien"
    assert attempt_gazebo_moveit(task_spec).adapter_name == "gazebo_moveit"
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_adapters.py
```

Expected: FAIL because adapter functions do not exist.

- [ ] **Step 3: Implement adapter functions**

Create `weld-experience-engine/weldcore/simulation_bakeoff/adapters.py`.

Functions:

```python
def run_simlite_reference(task_spec: SimulationTaskSpec) -> SimulatorAdapterResult: ...
def attempt_maniskill_sapien(task_spec: SimulationTaskSpec) -> SimulatorAdapterResult: ...
def attempt_gazebo_moveit(task_spec: SimulationTaskSpec) -> SimulatorAdapterResult: ...
```

Implementation requirements:

- `run_simlite_reference` always returns `status="completed"` using `task_spec.seam_path`.
- It sets metrics:
  - `path_continuity`: 1.0
  - `posture_stability`: 1.0
  - `digital_asset_ready`: 1.0
- `attempt_maniskill_sapien` checks `importlib.util.find_spec("mani_skill")` or `find_spec("sapien")`.
- `attempt_gazebo_moveit` checks `find_spec("rclpy")`, `find_spec("moveit")`, or `find_spec("moveit_configs_utils")`.
- If optional dependencies are missing, return `status="failed"` with `failure_boundary=("optional_dependency_missing", "...")`.
- If optional dependencies are present but the spike cannot actually validate the current `SimulationTaskSpec` contract, return `status="failed"` with a standardized boundary such as `("external_spike_not_executed", "task_contract_not_validated")`.
- Do not return `status="completed"` merely because `find_spec(...)` succeeds.
- A completed external result is allowed only when the adapter result includes:
  - a TCP trajectory for the same number of points as `task_spec.seam_path`
  - matching tool orientation samples
  - `planning_result["validated_task_contract"] is True`
  - `planning_result["task_status"] == "completed"`
  - explicit metrics for `same_task_attempted` and `task_contract_outputs_ready`
- This first implementation may conservatively return standardized failure boundaries for ManiSkill/SAPIEN and Gazebo/MoveIt even when dependencies are installed; that is preferable to overclaiming a real external simulation.
- Do not import heavy optional packages at module import time.
- Do not add any external dependency to `pyproject.toml`.
- Do not claim a final simulator selection.

- [ ] **Step 4: Update package exports**

Modify `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py` to export:

- `attempt_gazebo_moveit`
- `attempt_maniskill_sapien`
- `run_simlite_reference`

- [ ] **Step 5: Run GREEN tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_adapters.py tests/test_simulation_bakeoff_task_specs.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff weld-experience-engine/tests/test_simulation_bakeoff_adapters.py
git commit -m "feat: add simulation bakeoff adapter attempts"
```

---

## Task 4: Build Simulation Evidence Bundles

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/evidence.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_evidence.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_simulation_bakeoff_evidence.py`:

```python
import json

from weldcore.model import SimulationRunStatus
from weldcore.simulation_bakeoff import (
    build_simulation_evidence_bundle,
    default_simulation_task_specs,
    run_simlite_reference,
    attempt_gazebo_moveit,
)


def test_completed_adapter_result_builds_existing_run_record_and_dataset():
    task_spec = default_simulation_task_specs()[0]
    adapter_result = run_simlite_reference(task_spec)

    bundle = build_simulation_evidence_bundle(task_spec, adapter_result)
    data = bundle.to_dict()

    assert bundle.run_record.status == SimulationRunStatus.COMPLETED
    assert bundle.run_record.input_id == task_spec.task_id
    assert bundle.dataset is not None
    assert bundle.dataset.source_type.value == "simulation"
    assert bundle.dataset.task == task_spec.unit_id
    assert data["adapter_result"]["status"] == "completed"
    assert data["dataset"]["samples"][0]["metadata"]["task_spec"]["task_id"] == task_spec.task_id
    assert data["dataset"]["samples"][0]["metadata"]["adapter_result"]["adapter_name"] == "simlite_reference"
    assert "not WPS/PQR" in data["dataset"]["samples"][0]["metadata"]["generation_boundary"]
    assert data["rerun_replay_status"] == "not_attempted"
    assert data["rerun_replay_uri"] is None
    assert "rerun_optional" in " ".join(data["rerun_notes"])


def test_failed_adapter_result_builds_failure_evidence_without_dataset_samples():
    task_spec = default_simulation_task_specs()[0]
    adapter_result = attempt_gazebo_moveit(task_spec)

    bundle = build_simulation_evidence_bundle(task_spec, adapter_result)

    if adapter_result.status == "failed":
        assert bundle.run_record.status == SimulationRunStatus.FAILED
        assert bundle.dataset is None
        assert bundle.adapter_result.failure_boundary
        assert "not final simulator selection" in " ".join(bundle.run_record.boundary_notes)


def test_evidence_bundle_excludes_forbidden_physics_terms():
    task_spec = default_simulation_task_specs()[0]
    bundle = build_simulation_evidence_bundle(task_spec, run_simlite_reference(task_spec))
    payload = json.dumps(bundle.to_dict(), ensure_ascii=False).lower()

    for forbidden in ("molten", "weld_pool", "thermal", "metallurgy", "熔池", "热过程", "冶金"):
        assert forbidden not in payload
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_evidence.py
```

Expected: FAIL because `build_simulation_evidence_bundle` does not exist.

- [ ] **Step 3: Implement evidence builder**

Create `weld-experience-engine/weldcore/simulation_bakeoff/evidence.py`.

Function:

```python
def build_simulation_evidence_bundle(
    task_spec: SimulationTaskSpec,
    adapter_result: SimulatorAdapterResult,
) -> SimulationEvidenceBundle: ...
```

Implementation requirements:

- Always create a `SimulationRunRecord`.
- Map `adapter_result.status == "completed"` to `SimulationRunStatus.COMPLETED`, otherwise `SimulationRunStatus.FAILED`.
- Use `SimulatorName.SIMLITE` for `simlite_reference`.
- Use `SimulatorName.MANISKILL` for `maniskill_sapien`.
- Use `SimulatorName.OTHER` for `gazebo_moveit`.
- Completed results create a `SkillDataset` with one `SkillSample`.
- Failed results set `dataset=None` and preserve failure boundary in `run_record.errors` or `boundary_notes`.
- Dataset metadata must include:
  - `task_spec`
  - `adapter_result`
  - `requires_real_validation_later`
  - `generation_boundary`: includes `not WPS/PQR`, `not real welding quality validation`, `not final simulator selection`
- Set initial Rerun fields on every `SimulationEvidenceBundle`:
  - `rerun_replay_uri=None`
  - `rerun_replay_status="not_attempted"`
  - `rerun_notes=("rerun_optional_not_attempted_by_evidence_builder",)`
- Do not call Rerun from this builder. The report command owns the optional replay attempt.
- Use `Trajectory` / `TrajectorySample` from existing model.
- Use `WeldCondition` with lightweight values derived from task spec; do not add process physics.

- [ ] **Step 4: Update package exports**

Modify `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py` to export:

- `build_simulation_evidence_bundle`

- [ ] **Step 5: Run GREEN tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_evidence.py tests/test_simulation_bakeoff_models.py tests/test_simulation_io_models.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff weld-experience-engine/tests/test_simulation_bakeoff_evidence.py
git commit -m "feat: build simulation bakeoff evidence bundles"
```

---

## Task 5: Add Minimal Bake-off Runner And Scorecard

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/bakeoff.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_runner.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_simulation_bakeoff_runner.py`:

```python
from weldcore.simulation_bakeoff import run_minimal_simulation_bakeoff


def test_minimal_bakeoff_attempts_same_two_tasks_across_routes():
    result = run_minimal_simulation_bakeoff()

    task_ids = {task.task_id for task in result.task_specs}
    assert task_ids == {
        "task-long-straight-horizontal-tracking",
        "task-corner-horizontal-transition",
    }

    attempts_by_adapter = {}
    for bundle in result.evidence_bundles:
        attempts_by_adapter.setdefault(bundle.adapter_result.adapter_name, set()).add(
            bundle.task_spec.task_id
        )

    assert attempts_by_adapter["simlite_reference"] == task_ids
    assert attempts_by_adapter["maniskill_sapien"] == task_ids
    assert attempts_by_adapter["gazebo_moveit"] == task_ids


def test_minimal_bakeoff_has_r0_completed_evidence_and_no_final_selection():
    result = run_minimal_simulation_bakeoff()
    data = result.to_dict()

    assert any(
        bundle.adapter_result.adapter_name == "simlite_reference"
        and bundle.adapter_result.status == "completed"
        and bundle.dataset is not None
        for bundle in result.evidence_bundles
    )
    assert result.scorecard.final_simulator_selected is False
    assert "not_final_simulator_selection" in result.scorecard.evidence_notes
    assert data["scorecard"]["final_simulator_selected"] is False
    assert data["scorecard"]["dimension_weights"] == {
        "digital_asset_writeback": 0.35,
        "robot_executability": 0.30,
        "skill_unit_expression": 0.20,
        "engineering_access_cost": 0.15,
    }
    assert set(data["scorecard"]["route_dimension_scores"]) == {
        "simlite_reference",
        "maniskill_sapien",
        "gazebo_moveit",
    }


def test_minimal_bakeoff_scores_external_failures_as_boundaries():
    result = run_minimal_simulation_bakeoff()

    external_bundles = [
        bundle
        for bundle in result.evidence_bundles
        if bundle.adapter_result.adapter_name in {"maniskill_sapien", "gazebo_moveit"}
    ]
    assert len(external_bundles) == 4

    for bundle in external_bundles:
        assert bundle.adapter_result.status in {"completed", "failed"}
        if bundle.adapter_result.status == "failed":
            assert bundle.adapter_result.failure_boundary
        if bundle.adapter_result.status == "completed":
            assert bundle.adapter_result.planning_result["validated_task_contract"] is True
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_runner.py
```

Expected: FAIL because `run_minimal_simulation_bakeoff` does not exist.

- [ ] **Step 3: Implement bake-off runner**

Create `weld-experience-engine/weldcore/simulation_bakeoff/bakeoff.py`.

Add:

```python
@dataclass(frozen=True)
class MinimalBakeoffResult:
    task_specs: tuple[SimulationTaskSpec, ...]
    evidence_bundles: tuple[SimulationEvidenceBundle, ...]
    scorecard: BakeoffScorecard

    def to_dict(self) -> dict[str, object]: ...


def run_minimal_simulation_bakeoff() -> MinimalBakeoffResult: ...
```

Implementation requirements:

- Use `default_simulation_task_specs()`.
- For each task, run:
  - `run_simlite_reference`
  - `attempt_maniskill_sapien`
  - `attempt_gazebo_moveit`
- Convert every adapter result to `SimulationEvidenceBundle`.
- Score each route using the fixed spec dimensions:
  - `digital_asset_writeback` weight 0.35
  - `robot_executability` weight 0.30
  - `skill_unit_expression` weight 0.20
  - `engineering_access_cost` weight 0.15
- Store both:
  - `route_dimension_scores`: per-route values for each dimension
  - `route_scores`: weighted total per route
- Suggested dimension scoring:
  - `digital_asset_writeback`: 1.0 for completed bundles with datasets for all tasks, 0.35 for standardized failure evidence only, 0.0 for malformed output.
  - `robot_executability`: 1.0 only when a completed external route validates planning/IK/collision or equivalent task-contract fields, 0.4 for R0 baseline path-only evidence, 0.25 for standardized external failure boundary, 0.0 for malformed output.
  - `skill_unit_expression`: 1.0 when the route attempts both default task IDs, 0.5 for partial attempts, 0.0 for missing attempts.
  - `engineering_access_cost`: 1.0 for default runnable R0, 0.75 for available lightweight route, 0.25 for missing optional dependency with clean boundary, 0.0 for default workflow failure.
- Use weighted totals to populate `route_scores`; do not replace the fixed dimensions with a single completed/failed scalar.
- `final_simulator_selected` must always be `False`.
- Recommendation:
  - If no external route completes: `continue_with_r0_baseline_and_prepare_external_dependency_spikes`.
  - If one external route completes all tasks: `candidate_ready_for_next_adapter_plan:<adapter_name>`.
  - If both external routes complete all tasks: `compare_external_routes_before_final_selection`.
- Do not import optional simulator packages here; adapter functions handle optional checks.

- [ ] **Step 4: Update package exports**

Modify `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py` to export:

- `MinimalBakeoffResult`
- `run_minimal_simulation_bakeoff`

- [ ] **Step 5: Run GREEN tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_runner.py tests/test_simulation_bakeoff_evidence.py tests/test_simulation_bakeoff_adapters.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff weld-experience-engine/tests/test_simulation_bakeoff_runner.py
git commit -m "feat: run minimal simulation bakeoff"
```

---

## Task 6: Add Bake-off Report Command And Optional Rerun Evidence Attempt

**Files:**
- Create: `weld-experience-engine/weldcore/report/simulation_bakeoff_report.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_report.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_simulation_bakeoff_report.py`:

```python
import json
from pathlib import Path

from weldcore.report.simulation_bakeoff_report import main, run_simulation_bakeoff_report


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_simulation_bakeoff_report_writes_runtime_outputs(tmp_path: Path):
    evidence = run_simulation_bakeoff_report(outdir=tmp_path / "out", docs_report_dir=None)

    outdir = tmp_path / "out"
    assert (outdir / "tasks.json").exists()
    assert (outdir / "evidence_bundles.json").exists()
    assert (outdir / "scorecard.json").exists()
    assert (outdir / "report.md").exists()
    assert evidence["scorecard"]["final_simulator_selected"] is False
    assert evidence["rerun_replay"]["attempted"] is True
    assert evidence["rerun_replay"]["status"] in {"logged", "skipped"}
    if evidence["rerun_replay"]["status"] == "logged":
        assert evidence["rerun_replay"]["uri"]
    if evidence["rerun_replay"]["status"] == "skipped":
        assert evidence["rerun_replay"]["skip_reason"]

    tasks = _read_json(outdir / "tasks.json")
    assert {task["task_id"] for task in tasks} == {
        "task-long-straight-horizontal-tracking",
        "task-corner-horizontal-transition",
    }

    markdown = (outdir / "report.md").read_text(encoding="utf-8")
    assert "WeldSkillUnit Simulation Bake-off Evidence" in markdown
    assert "ManiSkill/SAPIEN" in markdown
    assert "Gazebo/MoveIt" in markdown
    assert "不是最终仿真器选择" in markdown
    assert "Rerun" in markdown
    assert "rerun_replay_status" in markdown or "Rerun replay status" in markdown


def test_simulation_bakeoff_report_can_write_docs_copy(tmp_path: Path):
    docs_dir = tmp_path / "docs"

    run_simulation_bakeoff_report(outdir=tmp_path / "out", docs_report_dir=docs_dir)

    assert (docs_dir / "simulation_bakeoff_evidence.md").exists()


def test_simulation_bakeoff_report_cli_no_docs_copy(tmp_path: Path):
    outdir = tmp_path / "cli-out"
    docs_dir = tmp_path / "cli-docs"

    main(["--outdir", str(outdir), "--docs-report-dir", str(docs_dir), "--no-docs-copy"])

    assert (outdir / "report.md").exists()
    assert not (docs_dir / "simulation_bakeoff_evidence.md").exists()
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_report.py
```

Expected: FAIL because `weldcore.report.simulation_bakeoff_report` does not exist.

- [ ] **Step 3: Implement report command**

Create `weld-experience-engine/weldcore/report/simulation_bakeoff_report.py`.

Implementation requirements:

- Public function:

```python
def run_simulation_bakeoff_report(
    outdir: str | Path = "simulation_bakeoff_report_out",
    docs_report_dir: str | Path | None = DEFAULT_DOCS_REPORT_DIR,
) -> dict[str, Any]: ...
```

- CLI function:

```python
def main(argv: list[str] | None = None) -> None: ...
```

- Default docs dir:

```python
DEFAULT_DOCS_REPORT_DIR = DEFAULT_FOUNDATION_ROOT / "reports"
```

- It runs `run_minimal_simulation_bakeoff()`.
- It writes:
  - `tasks.json`
  - `evidence_bundles.json`
  - `scorecard.json`
  - `report.md`
- If `docs_report_dir` is not `None`, write `simulation_bakeoff_evidence.md`.
- Attempt Rerun replay only for the first completed bundle with dataset:
  - Call existing `log_simulation_dataset_evidence(dataset, run_record, spawn=False)`.
  - Store a structured report summary:
    - `attempted`: `True` once a completed dataset bundle exists and replay was attempted
    - `status`: `"logged"` or `"skipped"`
    - `uri`: replay/log path or identifier when available, otherwise `None`
    - `skip_reason`: exception class/message or `rerun_sdk_unavailable` style reason when skipped
  - If Rerun is unavailable, report still succeeds.
- The returned evidence dict must include top-level `rerun_replay` with the structured summary above.
- The Markdown report must include the replay status and either the URI/record path or the skip reason.
- Markdown must include:
  - The two `WeldSkillUnit` task IDs.
  - Route summary for R0, ManiSkill/SAPIEN, Gazebo/MoveIt.
  - External failures as failure boundaries, not errors in the default workflow.
  - "不是最终仿真器选择".
  - "不证明真实焊接质量".
  - "不替代 WPS/PQR".

- [ ] **Step 4: Run GREEN tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_report.py tests/test_rerun_bridge.py tests/test_simulation_bakeoff_runner.py
```

Expected: all selected tests pass.

- [ ] **Step 5: Run report command manually**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.simulation_bakeoff_report
```

Expected:

- Command exits 0.
- Prints a short summary.
- Writes `simulation_bakeoff_report_out/`.
- Refreshes docs copy under `../docs/evidence/data-foundation/reports/simulation_bakeoff_evidence.md`.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/report/simulation_bakeoff_report.py weld-experience-engine/tests/test_simulation_bakeoff_report.py docs/evidence/data-foundation/reports/simulation_bakeoff_evidence.md
git commit -m "feat: add simulation bakeoff report"
```

---

## Task 7: Update Current-Route Docs And HTML Reading Copies

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `README.html`
- Modify: `details.html`
- Modify: `docs/simulation/robot-like-simulation-route.md`

- [ ] **Step 1: Update root README**

Modify `README.md`:

- In "如何验证", add a new command block after `simulation_ingest_report`:

```bash
uv run python -m weldcore.report.simulation_bakeoff_report
```

- Add one sentence after the command:

```markdown
`simulation_bakeoff_report` 用于生成第一轮 `WeldSkillUnit` 仿真最小验证证据；它记录 R0 baseline、ManiSkill/SAPIEN 与 Gazebo/MoveIt 的同任务尝试和失败边界，不表示最终仿真器已选择。
```

- [ ] **Step 2: Update details.md**

Modify the "下一步" section with one concise paragraph:

```markdown
当前下一步已经从路线准备推进到最小仿真验证：先用两个核心 `WeldSkillUnit` 做 R0 baseline 和 R2 候选路线 bake-off，把仿真尝试、失败边界、评分和 Rerun 回放沉淀为数字资产证据。
```

Keep the existing warning that the final simulator has not been selected.

- [ ] **Step 3: Update simulation route doc**

Modify `docs/simulation/robot-like-simulation-route.md` under "第一轮最小验证建议" or after it:

```markdown
第一版实现应形成 `simulation_bakeoff_report`：同一组两个核心 `SimulationTaskSpec` 同时进入 R0/simlite、ManiSkill/SAPIEN 和 Gazebo/MoveIt 尝试；外部路线不可用时记录统一 failure boundary，而不是阻断默认测试。
```

- [ ] **Step 4: Refresh README.html and details.html**

Use the existing root HTML copies as reading artifacts. It is acceptable to regenerate them with a small local script, but do not add a generator script unless explicitly needed. The HTML must contain the new `simulation_bakeoff_report` text.

- [ ] **Step 5: Verify docs**

Run:

```bash
rg -n "simulation_bakeoff_report|WeldSkillUnit|最终仿真器|failure boundary|Rerun|HTML 阅读版" README.md details.md README.html details.html docs/simulation/robot-like-simulation-route.md
```

Expected:

- The report command appears in README and README.html.
- `details.md` and `details.html` mention minimal simulation validation.
- Final simulator language remains boundary language.

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md details.md README.html details.html docs/simulation/robot-like-simulation-route.md
git commit -m "docs: document simulation bakeoff workflow"
```

---

## Task 8: Full Verification And Boundary Audit

**Files:**
- Read only unless fixes are required.

- [ ] **Step 1: Run full test suite**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run evidence/report commands**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.simulation_ingest_report
uv run python -m weldcore.report.simulation_bakeoff_report
```

Expected: all commands exit 0.

- [ ] **Step 3: Verify same-task bake-off evidence**

Run:

```bash
cd weld-experience-engine
uv run python - <<'PY'
from weldcore.simulation_bakeoff import run_minimal_simulation_bakeoff
result = run_minimal_simulation_bakeoff()
task_ids = {task.task_id for task in result.task_specs}
attempts = {}
for bundle in result.evidence_bundles:
    attempts.setdefault(bundle.adapter_result.adapter_name, set()).add(bundle.task_spec.task_id)
print(task_ids)
print(attempts)
assert attempts["simlite_reference"] == task_ids
assert attempts["maniskill_sapien"] == task_ids
assert attempts["gazebo_moveit"] == task_ids
assert result.scorecard.final_simulator_selected is False
PY
```

Expected: command exits 0.

- [ ] **Step 4: Audit forbidden overclaims**

Run:

```bash
rg -n "真实焊接质量已经验证|替代 WPS|替代 PQR|完整 ManiSkill|完整 Isaac|熔池闭环已经完成|已选择最终仿真器|最终仿真器已选择" README.md details.md docs/architecture docs/skill-assets docs/simulation docs/evidence weld-experience-engine/README.md weld-experience-engine/weldcore weld-experience-engine/tests || true
```

Expected: no completion claims. Negative/boundary language is acceptable.

- [ ] **Step 5: Audit forbidden physics fields in new package**

Run:

```bash
rg -n "molten|weld_pool|thermal|metallurgy|熔池|热过程|冶金" weld-experience-engine/weldcore/simulation_bakeoff weld-experience-engine/tests/test_simulation_bakeoff_* || true
```

Expected:

- No matches in implementation.
- Test files may contain forbidden terms only as negative assertions.

- [ ] **Step 6: Audit optional dependency boundary**

Run:

```bash
rg -n "^import rerun|from rerun|import mani_skill|from mani_skill|import sapien|from sapien|import rclpy|from rclpy|import moveit|from moveit" weld-experience-engine/weldcore weld-experience-engine/tests || true
```

Expected:

- No module-level imports of optional simulator dependencies.
- Existing local `import rerun as rr` inside bridge functions is acceptable, but this exact regex should not match because it searches line starts.

- [ ] **Step 7: Check generated/staged files**

Run:

```bash
git status --short
git diff --cached --name-only
git ls-files -o --exclude-standard | sed -n '1,120p'
```

Expected:

- Existing untracked `weld-experience-engine/uv.lock` may remain.
- Runtime output directories may be ignored.
- No generated runtime artifacts are staged unless explicitly committed docs evidence.

- [ ] **Step 8: Commit fixes only if needed**

If verification requires fixes, make minimal edits with `apply_patch`, rerun the failing command, then commit:

```bash
git add <fixed files>
git commit -m "fix: complete simulation bakeoff verification"
```

If no fixes are needed, commit nothing.

---

## Task 9: Completion Handoff

**Files:**
- Read only.

- [ ] **Step 1: Summarize commits and state**

Run:

```bash
git log --oneline -n 10
git status --short --branch
```

Expected:

- Recent commits include the spec, plan, and implementation commits.
- Only expected untracked files remain.

- [ ] **Step 2: Prepare final summary**

Final summary must state:

- `SimulationTaskSpec`, `SimulatorAdapterResult`, and `SimulationEvidenceBundle` now exist.
- Two core `WeldSkillUnit` tasks are used.
- R0/simlite baseline produces completed digital evidence.
- ManiSkill/SAPIEN and Gazebo/MoveIt are attempted on the same two tasks and produce standardized failure boundaries when optional dependencies are absent.
- Rerun remains optional.
- No final simulator has been selected.
- External complete adapter implementation remains a future phase.
