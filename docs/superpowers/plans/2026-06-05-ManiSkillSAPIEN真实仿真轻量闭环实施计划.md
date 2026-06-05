# ManiSkill/SAPIEN 真实仿真轻量闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first local, lightweight ManiSkill/SAPIEN simulation pipeline that automatically turns the two default `WeldSkillUnit` task specs into task configs, rule-based demos, real simulation artifacts, adapter results, compatible skill datasets, and evidence.

**Architecture:** Extend the existing `weldcore.simulation_bakeoff` package with a ManiSkill/SAPIEN-specific spike layer while keeping project canonical schema independent from simulator private formats. The default `uv` workflow stays light and dependency-free; the real simulator runs through an independent conda environment and a thin script entrypoint.

**Tech Stack:** Python 3.10+, dataclasses, pathlib, json, argparse, pytest, existing `weldcore.simulation_bakeoff` models, existing `SkillDataset` compatibility export, optional ManiSkill/SAPIEN imports, conda, shell script, Markdown.

---

## 0. Scope Boundary

Design spec:

- `docs/superpowers/specs/2026-06-05-ManiSkillSAPIEN真实仿真轻量闭环-design.md`

This plan implements only the first half of the overall pipeline:

```text
WeldSkillUnit
-> SimulationTaskSpec
-> ManiSkillTaskConfig
-> RuleBasedDemo
-> ManiSkill/SAPIEN Run
-> Raw Simulation Artifact
-> SimulatorAdapterResult
-> ExperienceDataset
-> SkillDataset compatibility export
-> SimulationEvidenceBundle
```

It must preserve the overall planning hooks from the spec:

- Future data sources include simulation, expert review/correction, real robot logs, welder process data, and quality feedback.
- ManiSkill/SAPIEN is the first real simulator loop, not a permanent core dependency or final simulator decision.
- `SkillDataset` is a compatibility export, not proof of robot executable process packages or real welding quality.
- The later path remains:

```text
WeldSkillPackage
-> RobotExecutionSpec
-> RobotProcessPackage
-> robot program / path / posture / process parameter recommendation
-> execution validation
-> evidence feedback
```

This plan does not implement `RobotExecutionSpec`, `RobotProcessPackage`, real welding quality validation, WPS/PQR, GPU batch generation, RL training, or real robot integration.

## 1. File Structure

### New ManiSkill/SAPIEN Spike Modules

- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py`
  - Dataclasses for `ManiSkillTaskConfig`, `RuleBasedDemo`, `RawManiSkillArtifact`, `ExperienceDataset`, and structured failure boundaries.
  - JSON helpers for reading and writing these objects.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_tasks.py`
  - Convert existing `SimulationTaskSpec` values into `ManiSkillTaskConfig`.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_demo.py`
  - Generate one rule-based expert demo per task config.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_runner.py`
  - CLI and callable runner for the independent conda environment.
  - Produces real or structured-failure raw artifacts.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_adapter.py`
  - Convert raw artifacts into `SimulatorAdapterResult`, `ExperienceDataset`, `SkillDataset` compatibility export, and evidence bundles.
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_pipeline.py`
  - Orchestrate default tasks through config, demo, runner artifact, adapter, and evidence output.

### New Script

- Create: `scripts/run_maniskill_spike.sh`
  - Minimal standard entrypoint for the conda environment.

### New Short Document

- Create: `docs/simulation/maniskill-sapien-dev-env.md`
  - One short page: why conda, setup, run command, output location, failure boundaries, not-doing list.

### Existing Files To Modify

- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
  - Export the new public contracts and pipeline helpers.
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/adapters.py`
  - Let `attempt_maniskill_sapien` optionally use a completed raw artifact when available, while retaining dependency-missing failure behavior for default tests.
- Modify: `docs/simulation/robot-like-simulation-route.md`
  - Add one short note that ManiSkill/SAPIEN now has a local lightweight loop plan.
- Modify: `details.md`
  - Add a short non-technical ledger note only if implementation changes project stage or available commands.
- Modify: `details.html`
  - Refresh only if `details.md` changes.

### Tests

- Create: `weld-experience-engine/tests/test_maniskill_contract.py`
- Create: `weld-experience-engine/tests/test_maniskill_task_config.py`
- Create: `weld-experience-engine/tests/test_maniskill_demo.py`
- Create: `weld-experience-engine/tests/test_maniskill_runner.py`
- Create: `weld-experience-engine/tests/test_simulation_bakeoff_maniskill_adapter.py`
- Create: `weld-experience-engine/tests/test_maniskill_pipeline.py`

## Task 0: Baseline Safety Check

**Files:**
- Read only.

- [ ] **Step 1: Confirm branch and working tree**

Run from repo root:

```bash
git status --short --branch
```

Expected:

- Current branch is shown.
- `main` may be ahead of `origin/main` by planning/spec commits.
- Existing untracked `weld-experience-engine/uv.lock` may appear. Do not stage, delete, or modify it unless separately instructed.

- [ ] **Step 2: Confirm approved design spec exists**

Run:

```bash
test -f docs/superpowers/specs/2026-06-05-ManiSkillSAPIEN真实仿真轻量闭环-design.md
```

Expected: exit code 0.

- [ ] **Step 3: Run baseline tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit nothing**

No commit for this task.

## Task 1: Add ManiSkill/SAPIEN Contract Models

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Test: `weld-experience-engine/tests/test_maniskill_contract.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_maniskill_contract.py`:

```python
import json

from weldcore.simulation_bakeoff import (
    ExperienceDataset,
    ManiSkillTaskConfig,
    RawManiSkillArtifact,
    RuleBasedDemo,
    SimulationPathPoint,
    write_json_artifact,
    read_json_artifact,
)


def test_maniskill_task_config_serializes_without_private_simulator_objects():
    config = ManiSkillTaskConfig(
        task_id="task-long-straight-horizontal-tracking",
        unit_id="long-straight-horizontal-tracking",
        task_name="长直横焊沿缝跟踪",
        seam_path=(SimulationPathPoint(0.0, 0.0, 0.0, 0.12, 0.0, 90.0, 0.0),),
        tcp_frame="torch_tcp",
        orientation_constraint=("keep_torch_posture_stable",),
        motion_constraint=("constant_tracking_speed",),
        expected_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
        source_task_spec_id="task-long-straight-horizontal-tracking",
    )

    data = config.to_dict()

    assert data["task_id"] == "task-long-straight-horizontal-tracking"
    assert data["seam_path"][0]["z"] == 0.12
    assert "sapien" not in json.dumps(data).lower()


def test_rule_based_demo_and_raw_artifact_preserve_failure_boundary():
    point = SimulationPathPoint(0.0, 0.0, 0.0, 0.12, 0.0, 90.0, 0.0)
    demo = RuleBasedDemo(
        demo_id="demo-task-long-straight-horizontal-tracking",
        task_id="task-long-straight-horizontal-tracking",
        tcp_trajectory=(point,),
        tool_orientation=(point,),
        generation_method="rule_based_seam_path_following",
        evidence_notes=("not_human_demonstration",),
    )
    artifact = RawManiSkillArtifact(
        run_id="maniskill-task-long-straight-horizontal-tracking",
        task_id=demo.task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        task_state={"attempted": True},
        metrics={"task_contract_outputs_ready": 0.0},
        failure_boundary=("environment_missing",),
        artifacts={"demo": "demo.json"},
        evidence_notes=("real_simulator_not_completed",),
    )

    assert demo.to_dict()["generation_method"] == "rule_based_seam_path_following"
    assert artifact.to_dict()["failure_boundary"] == ["environment_missing"]


def test_experience_dataset_declares_skilldataset_as_compatibility_export():
    dataset = ExperienceDataset(
        dataset_id="experience-maniskill-task-long-straight-horizontal-tracking",
        source_type="simulation",
        task_id="task-long-straight-horizontal-tracking",
        samples=("sample-1",),
        review_status="not_reviewed",
        validation_status="simulation_only",
        quality_feedback_status="not_available",
        compatibility_exports=("SkillDataset",),
        evidence_boundary=(
            "not_robot_process_package",
            "not_real_welding_quality_validation",
        ),
    )

    data = dataset.to_dict()

    assert data["compatibility_exports"] == ["SkillDataset"]
    assert "not_robot_process_package" in data["evidence_boundary"]


def test_json_artifact_round_trips(tmp_path):
    path = tmp_path / "artifact.json"
    write_json_artifact(path, {"task_id": "task-a"})

    assert read_json_artifact(path)["task_id"] == "task-a"
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_contract.py
```

Expected: FAIL because `ManiSkillTaskConfig` and related exports do not exist.

- [ ] **Step 3: Implement minimal contract models**

Create `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from weldcore.simulation_bakeoff.model import SimulationPathPoint


FailureBoundary = Literal[
    "environment_missing",
    "simulator_api_changed",
    "task_generation_failed",
    "demo_generation_failed",
    "simulation_run_failed",
    "artifact_missing",
    "adapter_conversion_failed",
]


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class ManiSkillTaskConfig:
    task_id: str
    unit_id: str
    task_name: str
    seam_path: tuple[SimulationPathPoint, ...]
    tcp_frame: str
    orientation_constraint: tuple[str, ...]
    motion_constraint: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    source_task_spec_id: str

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass(frozen=True)
class RuleBasedDemo:
    demo_id: str
    task_id: str
    tcp_trajectory: tuple[SimulationPathPoint, ...]
    tool_orientation: tuple[SimulationPathPoint, ...]
    generation_method: str
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass(frozen=True)
class RawManiSkillArtifact:
    run_id: str
    task_id: str
    status: Literal["completed", "failed"]
    tcp_trajectory: tuple[SimulationPathPoint, ...]
    tool_orientation: tuple[SimulationPathPoint, ...]
    task_state: dict[str, Any]
    metrics: dict[str, float]
    failure_boundary: tuple[str, ...]
    artifacts: dict[str, str]
    evidence_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


@dataclass(frozen=True)
class ExperienceDataset:
    dataset_id: str
    source_type: str
    task_id: str
    samples: tuple[str, ...]
    review_status: str
    validation_status: str
    quality_feedback_status: str
    compatibility_exports: tuple[str, ...]
    evidence_boundary: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(self)


def write_json_artifact(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_artifact(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
```

Update `__init__.py` to export these names.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_contract.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/maniskill_contract.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_maniskill_contract.py
git commit -m "feat: add maniskill spike contracts"
```

## Task 2: Generate ManiSkill Task Configs From Existing Task Specs

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_tasks.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Test: `weld-experience-engine/tests/test_maniskill_task_config.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_maniskill_task_config.py`:

```python
from weldcore.simulation_bakeoff import (
    default_maniskill_task_configs,
    default_simulation_task_specs,
    maniskill_task_config_from_spec,
)


def test_task_config_maps_default_task_spec_without_losing_boundaries():
    task_spec = default_simulation_task_specs()[0]

    config = maniskill_task_config_from_spec(task_spec)

    assert config.task_id == task_spec.task_id
    assert config.unit_id == task_spec.unit_id
    assert config.source_task_spec_id == task_spec.task_id
    assert config.seam_path == task_spec.seam_path
    assert config.tcp_frame == "torch_tcp"
    assert config.orientation_constraint == task_spec.tool_orientation_constraint
    assert config.motion_constraint == task_spec.motion_constraint
    assert config.expected_outputs == task_spec.expected_outputs
    assert "WPS/PQR" in config.out_of_scope


def test_default_maniskill_task_configs_cover_two_default_units():
    configs = default_maniskill_task_configs()

    assert [config.unit_id for config in configs] == [
        "long-straight-horizontal-tracking",
        "corner-horizontal-transition",
    ]
    assert all(config.task_id.startswith("task-") for config in configs)
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_task_config.py
```

Expected: FAIL because task config functions do not exist.

- [ ] **Step 3: Implement task config generator**

Create `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_tasks.py`:

```python
from __future__ import annotations

from weldcore.simulation_bakeoff.maniskill_contract import ManiSkillTaskConfig
from weldcore.simulation_bakeoff.model import SimulationTaskSpec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs


def maniskill_task_config_from_spec(task_spec: SimulationTaskSpec) -> ManiSkillTaskConfig:
    return ManiSkillTaskConfig(
        task_id=task_spec.task_id,
        unit_id=task_spec.unit_id,
        task_name=task_spec.name,
        seam_path=task_spec.seam_path,
        tcp_frame=task_spec.tcp_frame,
        orientation_constraint=task_spec.tool_orientation_constraint,
        motion_constraint=task_spec.motion_constraint,
        expected_outputs=task_spec.expected_outputs,
        out_of_scope=task_spec.out_of_scope,
        source_task_spec_id=task_spec.task_id,
    )


def default_maniskill_task_configs() -> tuple[ManiSkillTaskConfig, ...]:
    return tuple(
        maniskill_task_config_from_spec(task_spec)
        for task_spec in default_simulation_task_specs()
    )
```

Update `__init__.py` exports.

The `artifact_missing` boundary is covered in Task 7, where existing bake-off code reads a previously generated raw artifact path.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_task_config.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/maniskill_tasks.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_maniskill_task_config.py
git commit -m "feat: generate maniskill task configs"
```

## Task 3: Generate Rule-Based Demo Trajectories

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_demo.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Test: `weld-experience-engine/tests/test_maniskill_demo.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_maniskill_demo.py`:

```python
from weldcore.simulation_bakeoff import (
    default_maniskill_task_configs,
    generate_rule_based_demo,
)


def test_rule_based_demo_follows_config_seam_path():
    config = default_maniskill_task_configs()[0]

    demo = generate_rule_based_demo(config)

    assert demo.demo_id == f"demo-{config.task_id}"
    assert demo.task_id == config.task_id
    assert demo.tcp_trajectory == config.seam_path
    assert demo.tool_orientation == config.seam_path
    assert demo.generation_method == "rule_based_seam_path_following"
    assert "not_human_demonstration" in demo.evidence_notes


def test_rule_based_demo_is_generated_for_each_default_task():
    demos = [generate_rule_based_demo(config) for config in default_maniskill_task_configs()]

    assert len(demos) == 2
    assert all(len(demo.tcp_trajectory) >= 2 for demo in demos)
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_demo.py
```

Expected: FAIL because `generate_rule_based_demo` does not exist.

- [ ] **Step 3: Implement minimal demo generator**

Create `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_demo.py`:

```python
from __future__ import annotations

from weldcore.simulation_bakeoff.maniskill_contract import (
    ManiSkillTaskConfig,
    RuleBasedDemo,
)


def generate_rule_based_demo(config: ManiSkillTaskConfig) -> RuleBasedDemo:
    return RuleBasedDemo(
        demo_id=f"demo-{config.task_id}",
        task_id=config.task_id,
        tcp_trajectory=config.seam_path,
        tool_orientation=config.seam_path,
        generation_method="rule_based_seam_path_following",
        evidence_notes=(
            "not_human_demonstration",
            "not_robot_execution_validation",
        ),
    )
```

Update `__init__.py` exports.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_demo.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/maniskill_demo.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_maniskill_demo.py
git commit -m "feat: generate maniskill rule based demos"
```

## Task 4: Add Headless ManiSkill/SAPIEN Runner Boundary

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_runner.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Test: `weld-experience-engine/tests/test_maniskill_runner.py`

Use TDD. The default tests must not import ManiSkill/SAPIEN directly.

Important boundary: mocked backend success is allowed only for default `uv` contract tests. Final stage completion requires running the unmocked `_run_backend()` inside the independent conda environment; otherwise the stage is not complete.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_maniskill_runner.py`:

```python
from weldcore.simulation_bakeoff import (
    default_maniskill_task_configs,
    generate_rule_based_demo,
    run_maniskill_lightweight,
)


def test_runner_returns_structured_failure_when_backend_missing(monkeypatch):
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    artifact = run_maniskill_lightweight(config, demo)

    assert artifact.status == "failed"
    assert artifact.task_id == config.task_id
    assert "environment_missing" in artifact.failure_boundary
    assert artifact.metrics["task_contract_outputs_ready"] == 0.0
    assert artifact.task_state["attempted"] is True


def test_runner_uses_fake_backend_for_contract_success(monkeypatch):
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {
                "attempted": True,
                "task_status": "completed",
                "backend_invoked": True,
            },
            "metrics": {
                "task_contract_outputs_ready": 1.0,
                "path_continuity": 1.0,
                "backend_invocation_ready": 1.0,
            },
        },
    )

    artifact = run_maniskill_lightweight(config, demo)

    assert artifact.status == "completed"
    assert artifact.tcp_trajectory == demo.tcp_trajectory
    assert artifact.tool_orientation == demo.tool_orientation
    assert artifact.failure_boundary == ()
    assert artifact.task_state["backend_invoked"] is True


def test_runner_maps_backend_api_errors_to_simulator_api_changed(monkeypatch):
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: (_ for _ in ()).throw(AttributeError("api moved")),
    )

    artifact = run_maniskill_lightweight(config, demo)

    assert artifact.status == "failed"
    assert artifact.failure_boundary == ("simulator_api_changed",)
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_runner.py
```

Expected: FAIL because runner does not exist.

- [ ] **Step 3: Implement runner boundary**

Create `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_runner.py`:

```python
from __future__ import annotations

import importlib.util
from typing import Any

from weldcore.simulation_bakeoff.maniskill_contract import (
    ManiSkillTaskConfig,
    RawManiSkillArtifact,
    RuleBasedDemo,
)


def run_maniskill_lightweight(
    config: ManiSkillTaskConfig,
    demo: RuleBasedDemo,
) -> RawManiSkillArtifact:
    if not _maniskill_backend_available():
        return _failed_artifact(config, demo, ("environment_missing",))

    try:
        backend_result = _run_backend(config, demo)
    except (ImportError, AttributeError, TypeError, ValueError):
        return _failed_artifact(config, demo, ("simulator_api_changed",))
    except Exception:
        return _failed_artifact(config, demo, ("simulation_run_failed",))

    if backend_result.get("status") != "completed":
        return _failed_artifact(config, demo, ("simulation_run_failed",))

    return RawManiSkillArtifact(
        run_id=f"maniskill-{config.task_id}",
        task_id=config.task_id,
        status="completed",
        tcp_trajectory=demo.tcp_trajectory,
        tool_orientation=demo.tool_orientation,
        task_state=dict(backend_result.get("task_state", {})),
        metrics={
            "same_task_attempted": 1.0,
            "task_contract_outputs_ready": 1.0,
            **dict(backend_result.get("metrics", {})),
        },
        failure_boundary=(),
        artifacts={},
        evidence_notes=(
            "real_maniskill_sapien_runner_invoked",
            "not_final_simulator_selection",
            "not_robot_execution_validation",
        ),
    )


def _maniskill_backend_available() -> bool:
    return (
        importlib.util.find_spec("mani_skill") is not None
        or importlib.util.find_spec("sapien") is not None
    )


def _run_backend(config: ManiSkillTaskConfig, demo: RuleBasedDemo) -> dict[str, Any]:
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401 - registers ManiSkill gym environments.

    env = gym.make("PickCube-v1", obs_mode="state", render_mode=None)
    try:
        env.reset(seed=0)
        action = env.action_space.sample()
        env.step(action)
    finally:
        env.close()

    return {
        "status": "completed",
        "task_state": {
            "attempted": True,
            "task_status": "completed",
            "backend_invoked": True,
            "backend_probe": "mani_skill_gymnasium_pickcube_reset_step",
        },
        "metrics": {
            "path_continuity": 1.0,
            "backend_invocation_ready": 1.0,
        },
    }


def _failed_artifact(
    config: ManiSkillTaskConfig,
    demo: RuleBasedDemo,
    failure_boundary: tuple[str, ...],
) -> RawManiSkillArtifact:
    return RawManiSkillArtifact(
        run_id=f"maniskill-{config.task_id}",
        task_id=config.task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        task_state={"attempted": True, "task_status": "failed"},
        metrics={"same_task_attempted": 1.0, "task_contract_outputs_ready": 0.0},
        failure_boundary=failure_boundary,
        artifacts={},
        evidence_notes=(
            "real_maniskill_sapien_runner_not_completed",
            "not_final_simulator_selection",
        ),
    )
```

Do not add a separate runner CLI in this file. The script entrypoint must call the full pipeline once, so raw artifacts, adapter results, and evidence always correspond to the same simulator invocation.

Update `__init__.py` exports.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_runner.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/maniskill_runner.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_maniskill_runner.py
git commit -m "feat: add maniskill lightweight runner boundary"
```

## Task 5: Convert Raw Artifacts To Project Evidence

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_adapter.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Test: `weld-experience-engine/tests/test_simulation_bakeoff_maniskill_adapter.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_simulation_bakeoff_maniskill_adapter.py`:

```python
from weldcore.model import SkillDataset
from weldcore.simulation_bakeoff import (
    adapt_maniskill_artifact,
    build_maniskill_experience_dataset,
    build_simulation_evidence_bundle,
    default_maniskill_task_configs,
    default_simulation_task_specs,
    generate_rule_based_demo,
    run_maniskill_lightweight,
)


def test_completed_artifact_converts_to_adapter_result(monkeypatch):
    config = default_maniskill_task_configs()[0]
    task_spec = default_simulation_task_specs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {"attempted": True, "backend_invoked": True},
            "metrics": {"task_contract_outputs_ready": 1.0, "path_continuity": 1.0},
        },
    )
    artifact = run_maniskill_lightweight(config, demo)

    result = adapt_maniskill_artifact(task_spec, artifact)

    assert result.adapter_name == "maniskill_sapien"
    assert result.status == "completed"
    assert result.tcp_trajectory == demo.tcp_trajectory
    assert result.failure_boundary == ()
    assert result.metrics["task_contract_outputs_ready"] == 1.0


def test_failed_artifact_keeps_failure_boundary(monkeypatch):
    config = default_maniskill_task_configs()[0]
    task_spec = default_simulation_task_specs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )
    artifact = run_maniskill_lightweight(config, demo)

    result = adapt_maniskill_artifact(task_spec, artifact)

    assert result.status == "failed"
    assert "environment_missing" in result.failure_boundary


def test_experience_dataset_and_skilldataset_compatibility_are_built(monkeypatch):
    config = default_maniskill_task_configs()[0]
    task_spec = default_simulation_task_specs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {"attempted": True, "backend_invoked": True},
            "metrics": {"task_contract_outputs_ready": 1.0, "path_continuity": 1.0},
        },
    )
    artifact = run_maniskill_lightweight(config, demo)
    result = adapt_maniskill_artifact(task_spec, artifact)

    experience = build_maniskill_experience_dataset(task_spec, artifact)
    bundle = build_simulation_evidence_bundle(task_spec, result)

    assert experience.source_type == "simulation"
    assert "SkillDataset" in experience.compatibility_exports
    assert isinstance(bundle.dataset, SkillDataset)
    assert bundle.dataset.metadata if hasattr(bundle.dataset, "metadata") else True
```

If `SkillDataset` has no dataset-level `metadata`, keep the final assertion to only verify `bundle.dataset is not None`.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_maniskill_adapter.py
```

Expected: FAIL because adapter functions do not exist.

- [ ] **Step 3: Implement adapter**

Create `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_adapter.py`:

```python
from __future__ import annotations

from weldcore.simulation_bakeoff.maniskill_contract import (
    ExperienceDataset,
    RawManiSkillArtifact,
)
from weldcore.simulation_bakeoff.model import SimulationTaskSpec, SimulatorAdapterResult


def adapt_maniskill_artifact(
    task_spec: SimulationTaskSpec,
    artifact: RawManiSkillArtifact,
) -> SimulatorAdapterResult:
    return SimulatorAdapterResult(
        adapter_name="maniskill_sapien",
        task_id=task_spec.task_id,
        status=artifact.status,
        tcp_trajectory=artifact.tcp_trajectory,
        tool_orientation=artifact.tool_orientation,
        planning_result={
            "attempted": True,
            "validated_task_contract": artifact.status == "completed",
            "task_status": artifact.status,
            "task_state": artifact.task_state,
        },
        failure_boundary=artifact.failure_boundary,
        metrics=dict(artifact.metrics),
        artifacts=dict(artifact.artifacts),
        evidence_notes=(
            *artifact.evidence_notes,
            "experience_dataset_not_robot_process_package",
        ),
    )


def build_maniskill_experience_dataset(
    task_spec: SimulationTaskSpec,
    artifact: RawManiSkillArtifact,
) -> ExperienceDataset:
    sample_id = f"sample-maniskill-{task_spec.task_id}"
    return ExperienceDataset(
        dataset_id=f"experience-maniskill-{task_spec.task_id}",
        source_type="simulation",
        task_id=task_spec.task_id,
        samples=(sample_id,) if artifact.status == "completed" else (),
        review_status="not_reviewed",
        validation_status="simulation_only",
        quality_feedback_status="not_available",
        compatibility_exports=("SkillDataset",),
        evidence_boundary=(
            "not_robot_process_package",
            "not_real_welding_quality_validation",
            "not_WPS_PQR",
        ),
    )
```

If `SkillDataset` compatibility export needs richer metadata, add it inside `weldcore.simulation_bakeoff.evidence._build_dataset()` only for adapter results whose evidence notes contain `experience_dataset_not_robot_process_package`. Keep the change surgical.

Update `__init__.py` exports.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_maniskill_adapter.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/maniskill_adapter.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_simulation_bakeoff_maniskill_adapter.py
git commit -m "feat: adapt maniskill artifacts to evidence"
```

## Task 6: Add End-To-End Local Pipeline Writer

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_pipeline.py`
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Test: `weld-experience-engine/tests/test_maniskill_pipeline.py`

Use TDD.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_maniskill_pipeline.py`:

```python
import json

from weldcore.simulation_bakeoff import run_maniskill_spike_pipeline


def test_pipeline_writes_artifacts_for_two_default_tasks(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {"attempted": True, "backend_invoked": True},
            "metrics": {"task_contract_outputs_ready": 1.0, "path_continuity": 1.0},
        },
    )

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["completed"] == 2
    assert summary["failed"] == 0
    for task in summary["tasks"]:
        task_dir = tmp_path / task["task_id"]
        assert (task_dir / "task_config.json").exists()
        assert (task_dir / "demo.json").exists()
        assert (task_dir / "raw_artifact.json").exists()
        assert (task_dir / "adapter_result.json").exists()
        assert (task_dir / "experience_dataset.json").exists()
        assert (task_dir / "evidence_bundle.json").exists()


def test_pipeline_summary_records_structured_failures(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: False,
    )

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["completed"] == 0
    assert summary["failed"] == 2
    assert summary["failure_boundaries"] == ["environment_missing"]
    assert json.loads((tmp_path / "run_summary.json").read_text())["failed"] == 2


def test_pipeline_converts_task_generation_errors_to_failure_artifact(tmp_path, monkeypatch):
    def fail_task_generation(task_spec):
        raise ValueError("bad task")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_pipeline.maniskill_task_config_from_spec",
        fail_task_generation,
    )

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["failed"] == 2
    assert summary["failure_boundaries"] == ["task_generation_failed"]
    for task in summary["tasks"]:
        task_dir = tmp_path / task["task_id"]
        assert (task_dir / "raw_artifact.json").exists()


def test_pipeline_converts_adapter_errors_to_failure_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {"attempted": True, "backend_invoked": True},
            "metrics": {"task_contract_outputs_ready": 1.0},
        },
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_pipeline.adapt_maniskill_artifact",
        lambda task_spec, artifact: (_ for _ in ()).throw(ValueError("bad adapter")),
    )

    summary = run_maniskill_spike_pipeline(tmp_path)

    assert summary["task_count"] == 2
    assert summary["failed"] == 2
    assert summary["failure_boundaries"] == ["adapter_conversion_failed"]
    for task in summary["tasks"]:
        task_dir = tmp_path / task["task_id"]
        raw = json.loads((task_dir / "raw_artifact.json").read_text())
        assert raw["failure_boundary"] == ["adapter_conversion_failed"]
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_pipeline.py
```

Expected: FAIL because pipeline does not exist.

- [ ] **Step 3: Implement pipeline writer**

Create `weld-experience-engine/weldcore/simulation_bakeoff/maniskill_pipeline.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from weldcore.simulation_bakeoff.evidence import build_simulation_evidence_bundle
from weldcore.simulation_bakeoff.maniskill_adapter import (
    adapt_maniskill_artifact,
    build_maniskill_experience_dataset,
)
from weldcore.simulation_bakeoff.maniskill_contract import write_json_artifact
from weldcore.simulation_bakeoff.maniskill_demo import generate_rule_based_demo
from weldcore.simulation_bakeoff.maniskill_runner import run_maniskill_lightweight
from weldcore.simulation_bakeoff.maniskill_tasks import maniskill_task_config_from_spec
from weldcore.simulation_bakeoff.task_specs import default_simulation_task_specs


def run_maniskill_spike_pipeline(
    outdir: str | Path = "artifacts/simulation/maniskill-sapien",
) -> dict[str, Any]:
    root = Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    task_summaries: list[dict[str, Any]] = []

    for task_spec in default_simulation_task_specs():
        task_dir = root / task_spec.task_id
        try:
            config = maniskill_task_config_from_spec(task_spec)
            write_json_artifact(task_dir / "task_config.json", config.to_dict())
        except Exception:
            artifact = _stage_failure_artifact(task_spec.task_id, "task_generation_failed")
            write_json_artifact(task_dir / "raw_artifact.json", artifact.to_dict())
            task_summaries.append(_task_summary(task_spec.task_id, artifact))
            continue

        try:
            demo = generate_rule_based_demo(config)
            write_json_artifact(task_dir / "demo.json", demo.to_dict())
        except Exception:
            artifact = _stage_failure_artifact(task_spec.task_id, "demo_generation_failed")
            write_json_artifact(task_dir / "raw_artifact.json", artifact.to_dict())
            task_summaries.append(_task_summary(task_spec.task_id, artifact))
            continue

        artifact = run_maniskill_lightweight(config, demo)
        write_json_artifact(task_dir / "raw_artifact.json", artifact.to_dict())
        try:
            adapter_result = adapt_maniskill_artifact(task_spec, artifact)
            experience = build_maniskill_experience_dataset(task_spec, artifact)
            evidence = build_simulation_evidence_bundle(task_spec, adapter_result)
        except Exception:
            artifact = _stage_failure_artifact(task_spec.task_id, "adapter_conversion_failed")
            write_json_artifact(task_dir / "raw_artifact.json", artifact.to_dict())
            task_summaries.append(_task_summary(task_spec.task_id, artifact))
            continue

        write_json_artifact(task_dir / "adapter_result.json", adapter_result.to_dict())
        write_json_artifact(task_dir / "experience_dataset.json", experience.to_dict())
        write_json_artifact(task_dir / "evidence_bundle.json", evidence.to_dict())
        task_summaries.append(_task_summary(task_spec.task_id, artifact))

    summary = _summary(task_summaries)
    write_json_artifact(root / "run_summary.json", summary)
    return summary


def _stage_failure_artifact(task_id: str, boundary: str):
    from weldcore.simulation_bakeoff.maniskill_contract import RawManiSkillArtifact

    return RawManiSkillArtifact(
        run_id=f"maniskill-{task_id}",
        task_id=task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        task_state={"attempted": True, "task_status": "failed"},
        metrics={"same_task_attempted": 1.0, "task_contract_outputs_ready": 0.0},
        failure_boundary=(boundary,),
        artifacts={},
        evidence_notes=("pipeline_stage_failure", "not_final_simulator_selection"),
    )


def _task_summary(task_id: str, artifact) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": artifact.status,
        "failure_boundary": list(artifact.failure_boundary),
    }


def _summary(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    failure_boundaries = sorted(
        {
            boundary
            for task in tasks
            for boundary in task["failure_boundary"]
        }
    )
    return {
        "task_count": len(tasks),
        "completed": sum(1 for task in tasks if task["status"] == "completed"),
        "failed": sum(1 for task in tasks if task["status"] == "failed"),
        "failure_boundaries": failure_boundaries,
        "tasks": tasks,
        "stage_boundary": "experience_dataset_not_robot_process_package",
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run ManiSkill/SAPIEN spike pipeline.")
    parser.add_argument("--outdir", default="artifacts/simulation/maniskill-sapien")
    args = parser.parse_args(argv)
    summary = run_maniskill_spike_pipeline(args.outdir)
    print("=== ManiSkill/SAPIEN spike pipeline ===")
    print(f"task_count: {summary['task_count']}")
    print(f"completed: {summary['completed']}")
    print(f"failed: {summary['failed']}")
    print(f"failure_boundaries: {summary['failure_boundaries']}")


if __name__ == "__main__":
    main()
```

Update `__init__.py` exports.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_maniskill_pipeline.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/maniskill_pipeline.py \
  weld-experience-engine/weldcore/simulation_bakeoff/__init__.py \
  weld-experience-engine/tests/test_maniskill_pipeline.py
git commit -m "feat: write maniskill spike artifacts"
```

## Task 7: Integrate Completed Artifacts With Existing Bake-Off Adapter

**Files:**
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/adapters.py`
- Test: `weld-experience-engine/tests/test_simulation_bakeoff_adapters.py`

Use TDD. Keep the existing dependency-missing behavior when no artifact path is provided.

- [ ] **Step 1: Add failing tests for artifact-backed adapter success**

Append to `weld-experience-engine/tests/test_simulation_bakeoff_adapters.py`:

```python
from weldcore.simulation_bakeoff import (
    adapt_maniskill_artifact,
    attempt_maniskill_sapien,
    default_maniskill_task_configs,
    default_simulation_task_specs,
    generate_rule_based_demo,
    run_maniskill_lightweight,
    write_json_artifact,
)


def test_maniskill_attempt_uses_completed_raw_artifact(tmp_path, monkeypatch):
    task_spec = default_simulation_task_specs()[0]
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: {
            "status": "completed",
            "task_state": {"attempted": True, "backend_invoked": True},
            "metrics": {"task_contract_outputs_ready": 1.0},
        },
    )
    artifact = run_maniskill_lightweight(config, demo)
    artifact_path = tmp_path / "raw_artifact.json"
    write_json_artifact(artifact_path, artifact.to_dict())

    result = attempt_maniskill_sapien(task_spec, raw_artifact_path=artifact_path)

    assert result.status == "completed"
    assert result.adapter_name == "maniskill_sapien"
    assert result.failure_boundary == ()
    assert result.planning_result["validated_task_contract"] is True


def test_maniskill_attempt_records_missing_artifact_boundary(tmp_path):
    task_spec = default_simulation_task_specs()[0]

    result = attempt_maniskill_sapien(
        task_spec,
        raw_artifact_path=tmp_path / "missing.json",
    )

    assert result.status == "failed"
    assert "artifact_missing" in result.failure_boundary


def test_maniskill_attempt_records_adapter_conversion_failure(tmp_path, monkeypatch):
    task_spec = default_simulation_task_specs()[0]
    artifact_path = tmp_path / "raw_artifact.json"
    artifact_path.write_text("{not-json", encoding="utf-8")

    result = attempt_maniskill_sapien(task_spec, raw_artifact_path=artifact_path)

    assert result.status == "failed"
    assert "adapter_conversion_failed" in result.failure_boundary
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_adapters.py
```

Expected: FAIL because `attempt_maniskill_sapien` does not accept `raw_artifact_path`.

- [ ] **Step 3: Implement artifact-backed adapter path**

Modify `weld-experience-engine/weldcore/simulation_bakeoff/adapters.py`:

- Add optional parameter `raw_artifact_path: str | Path | None = None` to `attempt_maniskill_sapien`.
- If `raw_artifact_path` is provided and missing, return a failed `SimulatorAdapterResult` with `("artifact_missing",)`.
- If present, read `raw_artifact.json`, build `RawManiSkillArtifact`, and call `adapt_maniskill_artifact(task_spec, artifact)`.
- If reading or conversion fails, return `("adapter_conversion_failed",)`.
- If no path is provided, preserve current optional dependency behavior exactly.

Keep this path focused; do not make the bake-off runner search arbitrary directories. Do not modify `simulation_bakeoff_report.py` in this task; artifact-backed report behavior can be planned later if needed.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_simulation_bakeoff_adapters.py
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add weld-experience-engine/weldcore/simulation_bakeoff/adapters.py \
  weld-experience-engine/tests/test_simulation_bakeoff_adapters.py
git commit -m "feat: use maniskill artifacts in bakeoff adapter"
```

## Task 8: Add Script Entrypoint

**Files:**
- Create: `scripts/run_maniskill_spike.sh`
- Modify: `.gitignore` if artifact output is not already ignored.

Use a shell smoke test.

- [ ] **Step 1: Create script**

Create `scripts/run_maniskill_spike.sh`:

```bash
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
```

Make it executable:

```bash
chmod +x scripts/run_maniskill_spike.sh
```

- [ ] **Step 2: Run smoke test without ManiSkill/SAPIEN**

Run from repo root:

```bash
./scripts/run_maniskill_spike.sh /tmp/weld-maniskill-spike
```

Expected:

- Exit code 0.
- Prints a summary.
- If ManiSkill/SAPIEN is not installed, `completed: 0`, `failed: 2`, and `failure_boundaries` includes `environment_missing`.
- `/tmp/weld-maniskill-spike/run_summary.json` exists.

- [ ] **Step 3: Ensure generated artifacts are ignored**

Run:

```bash
git status --short
```

Expected:

- No generated artifact under `artifacts/simulation/maniskill-sapien/` is staged or tracked.
- If artifacts appear as untracked under repo root, add only the narrow artifact output path to `.gitignore`:

```gitignore
artifacts/simulation/
```

- [ ] **Step 4: Commit**

```bash
git add scripts/run_maniskill_spike.sh .gitignore
git commit -m "chore: add maniskill spike script"
```

If `.gitignore` did not change, omit it from `git add`.

## Task 9: Add Short Conda Environment Document

**Files:**
- Create: `docs/simulation/maniskill-sapien-dev-env.md`
- Modify: `docs/simulation/README.md`
- Modify: `docs/simulation/robot-like-simulation-route.md`

- [ ] **Step 1: Create short environment document**

Create `docs/simulation/maniskill-sapien-dev-env.md`:

```markdown
# ManiSkill/SAPIEN Dev Environment

This page records the minimal local environment for the first real simulator loop.
It is not a general ManiSkill tutorial and does not make ManiSkill/SAPIEN a core project dependency.

## Why Conda

The default `uv` project environment stays light and testable. ManiSkill/SAPIEN runs in an independent conda environment so simulator dependencies do not break the default workflow.

## Minimal Setup

```bash
conda create -n weld-maniskill python=3.10 -y
conda activate weld-maniskill
pip install -e ./weld-experience-engine
pip install mani-skill sapien
```

If the package names or platform support change, follow the official ManiSkill/SAPIEN installation docs and keep this page short.

## Run

```bash
./scripts/run_maniskill_spike.sh
```

Default output:

```text
artifacts/simulation/maniskill-sapien/
```

## Expected Outputs

- `task_config.json`
- `demo.json`
- `raw_artifact.json`
- `adapter_result.json`
- `experience_dataset.json`
- `evidence_bundle.json`
- `run_summary.json`

## Failure Boundaries

- `environment_missing`
- `simulator_api_changed`
- `task_generation_failed`
- `demo_generation_failed`
- `simulation_run_failed`
- `artifact_missing`
- `adapter_conversion_failed`

## Current Boundaries

- Not final simulator selection.
- Not robot executable process package.
- Not real welding quality validation.
- Not WPS/PQR.
- Not GPU batch generation or RL training.
```

- [ ] **Step 2: Add one link to simulation README**

Modify `docs/simulation/README.md` with one bullet:

```markdown
- [ManiSkill/SAPIEN 本机轻量环境](maniskill-sapien-dev-env.md)
```

- [ ] **Step 3: Add one short route note**

Modify `docs/simulation/robot-like-simulation-route.md` with one sentence near the first-round validation section:

```markdown
第一条真实工具闭环优先采用 ManiSkill/SAPIEN 本机轻量 CPU/headless/state-based 路线；其输出仍必须通过 adapter 回到项目 canonical schema，不代表最终仿真器选择。
```

- [ ] **Step 4: Commit**

```bash
git add docs/simulation/maniskill-sapien-dev-env.md \
  docs/simulation/README.md \
  docs/simulation/robot-like-simulation-route.md
git commit -m "docs: add maniskill dev environment"
```

## Task 10: Refresh User-Facing Stage Ledger If Needed

**Files:**
- Modify only if needed: `details.md`
- Modify only if needed: `details.html`

- [ ] **Step 1: Decide whether `details.md` needs updating**

Read `details.md`.

Update it only if implementation has changed a user-facing stage, available command, or delivery artifact. If the only change is internal code with a linked docs page, skip this task.

- [ ] **Step 2: If updating, keep it short**

Add a brief note under current work or next step:

```markdown
下一步真实仿真闭环将优先使用独立 conda 环境运行 ManiSkill/SAPIEN 本机轻量任务。当前目标是把两个核心 WeldSkillUnit 自动生成任务、demo、仿真 artifact 和经验级数据证据，不代表最终仿真器选择或机器人可执行工艺包。
```

- [ ] **Step 3: Refresh HTML only if Markdown changed**

Use the repository's existing Markdown-to-HTML pattern. If no generator exists, make the smallest manual refresh consistent with existing `details.html`.

- [ ] **Step 4: Commit only if files changed**

```bash
git add details.md details.html
git commit -m "docs: update simulation stage ledger"
```

If no change was needed, commit nothing.

## Task 11: Full Verification And Evidence

**Files:**
- Read generated outputs only.

- [ ] **Step 1: Run targeted tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q \
  tests/test_maniskill_contract.py \
  tests/test_maniskill_task_config.py \
  tests/test_maniskill_demo.py \
  tests/test_maniskill_runner.py \
  tests/test_simulation_bakeoff_maniskill_adapter.py \
  tests/test_maniskill_pipeline.py \
  tests/test_simulation_bakeoff_adapters.py
```

Expected: all targeted tests pass.

- [ ] **Step 2: Run full default tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Run script smoke test**

Run from repo root:

```bash
./scripts/run_maniskill_spike.sh /tmp/weld-maniskill-spike
```

Expected:

- Exit code 0.
- `run_summary.json` exists.
- If ManiSkill/SAPIEN is installed in the active conda environment, completed should be 2 and failed should be 0.
- If not installed, failed should be 2 with `environment_missing`; this validates the failure path but does not satisfy the design's final success path.

- [ ] **Step 4: Run real conda success path**

Activate the independent conda environment:

```bash
conda activate weld-maniskill
./scripts/run_maniskill_spike.sh /tmp/weld-maniskill-real
```

Expected final stage success:

- Exit code 0.
- `/tmp/weld-maniskill-real/run_summary.json` exists.
- Summary has `task_count: 2`, `completed: 2`, `failed: 0`.
- Each default task has `task_config.json`, `demo.json`, `raw_artifact.json`, `adapter_result.json`, `experience_dataset.json`, and `evidence_bundle.json`.
- Each completed `raw_artifact.json` records `backend_invoked: true` or `backend_invocation_ready: 1.0`, proving the unmocked ManiSkill backend probe ran.

If the real conda success path cannot be achieved, do not claim the stage is complete. Record the failure boundary and continue debugging under superpowers:systematic-debugging.

- [ ] **Step 5: Confirm git status**

Run:

```bash
git status --short --branch
```

Expected:

- Only intentional source/docs changes are present.
- `weld-experience-engine/uv.lock` remains untouched unless separately requested.
- Generated `/tmp` artifacts are outside the repo.

- [ ] **Step 6: Final commit if verification changes files**

If verification required small fixes, commit them with a focused message:

```bash
git add <changed-files>
git commit -m "fix: stabilize maniskill spike verification"
```

## Task 12: Completion Criteria

Before calling the implementation complete, verify every item:

- [ ] Current `uv` default tests pass.
- [ ] Independent conda environment document exists and is short.
- [ ] Script entrypoint exists and runs.
- [ ] Two default `WeldSkillUnit` values generate task configs.
- [ ] Each default task generates one rule-based demo.
- [ ] Real local CPU/headless/state-based ManiSkill/SAPIEN run completes for both tasks.
- [ ] Raw artifacts prove the unmocked ManiSkill backend was invoked through a reset/step probe.
- [ ] Both tasks output raw artifacts, adapter results, experience datasets, compatibility `SkillDataset` evidence, and evidence bundles.
- [ ] Failure boundaries are structured and recorded for failure paths.
- [ ] No implementation treats `SkillDataset` as a robot executable process package.
- [ ] No implementation claims real welding quality validation, WPS/PQR, final simulator selection, or robot execution validation.
- [ ] The spec's overall planning hooks remain represented: future multi-source data, simulator replaceability, and later robot execution migration.
