# 统一仿真 Adapter 第一轮 Facade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first-round unified simulation adapter facade / registry around existing simlite, ManiSkill/SAPIEN, and Gazebo/MoveIt route runners without adding batch generation or entry-locking logic.

**Architecture:** Add a small `weldcore.simulation_bakeoff.routes` facade that owns route metadata, default route lookup, route execution, comparison execution, and unexpected runner failure conversion. Keep existing adapter runners in `adapters.py` and keep `SimulationEvidenceBundle` construction in `evidence.py`. Update `bakeoff.py` to consume the registry instead of maintaining its own route runner tuple.

**Tech Stack:** Python dataclasses, `typing.Literal`, pytest, existing `weldcore.simulation_bakeoff` package.

---

## Scope Boundary

This plan implements only **第一轮：统一 Adapter Facade** from:

`docs/superpowers/specs/2026-06-08-统一仿真Adapter框架与阶段性默认入口-design.md`

Do not implement in this round:

- `SimulationBatchSpec`
- `SimulationBatchResult`
- 2-3 `WeldSkillUnit` x 10 sample batch generation
- `DefaultSimulationEntryDecision`
- ManiSkill/SAPIEN entry locking report
- real ManiSkill/SAPIEN environment validation
- final simulator selection

The first round is complete when route metadata and unified route execution exist, existing bake-off behavior still works, and default tests still pass without requiring external simulator installs.

## File Structure

- Create: `weld-experience-engine/weldcore/simulation_bakeoff/routes.py`
  - Defines `SimulationAdapterRoute`.
  - Defines route role/status literals.
  - Lists default routes.
  - Provides default route lookup and route execution facade.
  - Converts unexpected runner exceptions into failed `SimulatorAdapterResult`.

- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
  - Exports the new route facade API.

- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/bakeoff.py`
  - Uses the route registry instead of its local `ROUTE_RUNNERS`.
  - Preserves existing route ids, scorecard behavior, and report outputs.

- Create: `weld-experience-engine/tests/test_simulation_adapter_routes.py`
  - Tests route metadata, default route lookup, route execution, comparison route execution, and runner exception boundaries.

- Modify: `weld-experience-engine/tests/test_simulation_bakeoff_runner.py`
  - Add or adjust one regression test proving `run_minimal_simulation_bakeoff()` consumes the registry while preserving existing route score keys.

- Modify: `details.md` and `details.html`
  - After implementation and verification, record that 第一轮 adapter facade / registry is complete.
  - Do not update README unless project default positioning or default user commands change.

## Task 1: Route Metadata And Default Registry

**Files:**
- Create: `weld-experience-engine/weldcore/simulation_bakeoff/routes.py`
- Create: `weld-experience-engine/tests/test_simulation_adapter_routes.py`

- [ ] **Step 1: Write failing tests for route metadata**

Add this test file:

```python
from weldcore.simulation_bakeoff import (
    default_simulation_adapter_routes,
    get_default_batch_route,
)


def test_default_simulation_adapter_routes_declares_current_route_roles():
    routes = default_simulation_adapter_routes()
    by_id = {route.route_id: route for route in routes}

    assert tuple(by_id) == (
        "simlite_reference",
        "maniskill_sapien",
        "gazebo_moveit",
    )
    assert by_id["simlite_reference"].role == "baseline"
    assert by_id["simlite_reference"].default_for_batch is False
    assert by_id["maniskill_sapien"].role == "default_candidate"
    assert by_id["maniskill_sapien"].default_for_batch is True
    assert by_id["gazebo_moveit"].role == "planning_candidate"
    assert by_id["gazebo_moveit"].default_for_batch is False
    assert "not_final_simulator_selection" in by_id["maniskill_sapien"].evidence_boundary


def test_get_default_batch_route_returns_maniskill_candidate_without_locking_it():
    route = get_default_batch_route()

    assert route.route_id == "maniskill_sapien"
    assert route.role == "default_candidate"
    assert route.default_for_batch is True
    assert "not_locked_for_robot_execution" in route.evidence_boundary
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_simulation_adapter_routes.py -q
```

Expected: FAIL because `default_simulation_adapter_routes` and `get_default_batch_route` do not exist.

- [ ] **Step 3: Implement minimal route metadata**

Create `weldcore/simulation_bakeoff/routes.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from weldcore.simulation_bakeoff.adapters import (
    attempt_gazebo_moveit,
    attempt_maniskill_sapien,
    run_simlite_reference,
)
from weldcore.simulation_bakeoff.model import SimulationTaskSpec, SimulatorAdapterResult


SimulationAdapterRole = Literal["baseline", "default_candidate", "planning_candidate"]
SimulationAdapterStatus = Literal["available", "optional_dependency", "not_integrated"]
SimulationAdapterRunner = Callable[[SimulationTaskSpec], SimulatorAdapterResult]


@dataclass(frozen=True)
class SimulationAdapterRoute:
    route_id: str
    display_name: str
    role: SimulationAdapterRole
    status: SimulationAdapterStatus
    runner: SimulationAdapterRunner
    default_for_batch: bool
    dependency_boundary: tuple[str, ...]
    evidence_boundary: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "display_name": self.display_name,
            "role": self.role,
            "status": self.status,
            "default_for_batch": self.default_for_batch,
            "dependency_boundary": list(self.dependency_boundary),
            "evidence_boundary": list(self.evidence_boundary),
        }


def default_simulation_adapter_routes() -> tuple[SimulationAdapterRoute, ...]:
    return (
        SimulationAdapterRoute(
            route_id="simlite_reference",
            display_name="R0 / simlite reference",
            role="baseline",
            status="available",
            runner=run_simlite_reference,
            default_for_batch=False,
            dependency_boundary=(),
            evidence_boundary=("r0_baseline", "not_final_simulator_selection"),
        ),
        SimulationAdapterRoute(
            route_id="maniskill_sapien",
            display_name="ManiSkill/SAPIEN",
            role="default_candidate",
            status="optional_dependency",
            runner=attempt_maniskill_sapien,
            default_for_batch=True,
            dependency_boundary=("mani_skill_or_sapien_optional",),
            evidence_boundary=(
                "stage_default_candidate",
                "not_final_simulator_selection",
                "not_locked_for_robot_execution",
            ),
        ),
        SimulationAdapterRoute(
            route_id="gazebo_moveit",
            display_name="Gazebo/MoveIt",
            role="planning_candidate",
            status="not_integrated",
            runner=attempt_gazebo_moveit,
            default_for_batch=False,
            dependency_boundary=("rclpy_moveit_or_moveit_configs_utils_optional",),
            evidence_boundary=(
                "planning_candidate_only",
                "not_final_simulator_selection",
            ),
        ),
    )


def get_default_batch_route() -> SimulationAdapterRoute:
    defaults = tuple(
        route for route in default_simulation_adapter_routes() if route.default_for_batch
    )
    if len(defaults) != 1:
        raise ValueError("Expected exactly one default simulation adapter route")
    return defaults[0]
```

- [ ] **Step 4: Export route API**

Modify `weldcore/simulation_bakeoff/__init__.py`:

```python
from .routes import (
    SimulationAdapterRole,
    SimulationAdapterRoute,
    SimulationAdapterRunner,
    SimulationAdapterStatus,
    default_simulation_adapter_routes,
    get_default_batch_route,
)
```

Add the names to `__all__`.

- [ ] **Step 5: Run tests and verify they pass**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_simulation_adapter_routes.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 1**

```bash
git add weldcore/simulation_bakeoff/routes.py weldcore/simulation_bakeoff/__init__.py tests/test_simulation_adapter_routes.py
git commit -m "feat: add simulation adapter route registry"
```

## Task 2: Unified Route Execution Facade

**Files:**
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/routes.py`
- Modify: `weld-experience-engine/tests/test_simulation_adapter_routes.py`

- [ ] **Step 1: Write failing tests for route execution**

Append tests:

```python
import pytest

from weldcore.simulation_bakeoff import (
    SimulationAdapterRoute,
    default_simulation_task_specs,
    run_adapter_route,
    run_comparison_routes,
)
from weldcore.simulation_bakeoff.model import SimulatorAdapterResult


def test_run_adapter_route_executes_selected_route():
    task_spec = default_simulation_task_specs()[0]

    result = run_adapter_route("simlite_reference", task_spec)

    assert result.adapter_name == "simlite_reference"
    assert result.task_id == task_spec.task_id
    assert result.status == "completed"


def test_run_adapter_route_rejects_unknown_route_id():
    task_spec = default_simulation_task_specs()[0]

    with pytest.raises(ValueError, match="Unknown simulation adapter route"):
        run_adapter_route("missing_route", task_spec)


def test_run_adapter_route_converts_unexpected_runner_error_to_failure_boundary():
    task_spec = default_simulation_task_specs()[0]

    def broken_runner(_task_spec):
        raise RuntimeError("backend broke")

    route = SimulationAdapterRoute(
        route_id="broken_route",
        display_name="Broken Route",
        role="planning_candidate",
        status="not_integrated",
        runner=broken_runner,
        default_for_batch=False,
        dependency_boundary=("optional_dependency",),
        evidence_boundary=("test_route",),
    )

    result = run_adapter_route("broken_route", task_spec, routes=(route,))

    assert result.adapter_name == "broken_route"
    assert result.status == "failed"
    assert result.failure_boundary == ("simulation_run_failed",)
    assert result.planning_result["attempted"] is True
    assert result.planning_result["validated_task_contract"] is False


def test_run_comparison_routes_returns_each_current_route_result():
    task_spec = default_simulation_task_specs()[0]

    results = run_comparison_routes(task_spec)

    assert {result.adapter_name for result in results} == {
        "simlite_reference",
        "maniskill_sapien",
        "gazebo_moveit",
    }
    assert all(isinstance(result, SimulatorAdapterResult) for result in results)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_simulation_adapter_routes.py -q
```

Expected: FAIL because `run_adapter_route` and `run_comparison_routes` do not exist.

- [ ] **Step 3: Implement route execution facade**

Add to `routes.py`:

```python
def run_adapter_route(
    route_id: str,
    task_spec: SimulationTaskSpec,
    routes: tuple[SimulationAdapterRoute, ...] | None = None,
) -> SimulatorAdapterResult:
    selected_routes = default_simulation_adapter_routes() if routes is None else routes
    route = _route_by_id(route_id, selected_routes)
    try:
        return route.runner(task_spec)
    except Exception:
        return _failed_route_result(route.route_id, task_spec, ("simulation_run_failed",))


def run_comparison_routes(
    task_spec: SimulationTaskSpec,
    routes: tuple[SimulationAdapterRoute, ...] | None = None,
) -> tuple[SimulatorAdapterResult, ...]:
    selected_routes = default_simulation_adapter_routes() if routes is None else routes
    return tuple(
        run_adapter_route(route.route_id, task_spec, routes=selected_routes)
        for route in selected_routes
    )


def _route_by_id(
    route_id: str,
    routes: tuple[SimulationAdapterRoute, ...],
) -> SimulationAdapterRoute:
    for route in routes:
        if route.route_id == route_id:
            return route
    raise ValueError(f"Unknown simulation adapter route: {route_id}")


def _failed_route_result(
    route_id: str,
    task_spec: SimulationTaskSpec,
    failure_boundary: tuple[str, ...],
) -> SimulatorAdapterResult:
    return SimulatorAdapterResult(
        adapter_name=route_id,
        task_id=task_spec.task_id,
        status="failed",
        tcp_trajectory=(),
        tool_orientation=(),
        planning_result={
            "attempted": True,
            "validated_task_contract": False,
            "task_status": "failed",
        },
        failure_boundary=failure_boundary,
        metrics={
            "same_task_attempted": 1.0,
            "task_contract_outputs_ready": 0.0,
        },
        artifacts={},
        evidence_notes=("not_final_simulator_selection",),
    )
```

- [ ] **Step 4: Export facade API**

Modify `weldcore/simulation_bakeoff/__init__.py` to export:

```python
run_adapter_route,
run_comparison_routes,
```

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_simulation_adapter_routes.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 2**

```bash
git add weldcore/simulation_bakeoff/routes.py weldcore/simulation_bakeoff/__init__.py tests/test_simulation_adapter_routes.py
git commit -m "feat: run simulation adapter routes through facade"
```

## Task 3: Make Bake-Off Consume The Registry

**Files:**
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/bakeoff.py`
- Modify: `weld-experience-engine/tests/test_simulation_bakeoff_runner.py`

- [ ] **Step 1: Add a regression test for registry route ids**

In `tests/test_simulation_bakeoff_runner.py`, add:

```python
from weldcore.simulation_bakeoff import default_simulation_adapter_routes


def test_minimal_bakeoff_scorecard_uses_registered_route_ids():
    result = run_minimal_simulation_bakeoff()

    registered_route_ids = {
        route.route_id for route in default_simulation_adapter_routes()
    }

    assert set(result.scorecard.route_dimension_scores) == registered_route_ids
    assert set(result.scorecard.route_scores) == registered_route_ids
```

- [ ] **Step 2: Run the current bake-off tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_simulation_bakeoff_runner.py -q
```

Expected: PASS before refactor. This confirms the test describes current behavior and protects it during the registry migration.

- [ ] **Step 3: Refactor `bakeoff.py` to use registry**

Replace imports of route runners with:

```python
from weldcore.simulation_bakeoff.routes import (
    default_simulation_adapter_routes,
    run_adapter_route,
)
```

Replace the local `ROUTE_RUNNERS` tuple with helper functions:

```python
def _route_ids() -> tuple[str, ...]:
    return tuple(route.route_id for route in default_simulation_adapter_routes())
```

Update `run_minimal_simulation_bakeoff()`:

```python
route_ids = _route_ids()
evidence_bundles = tuple(
    build_simulation_evidence_bundle(task_spec, run_adapter_route(route_id, task_spec))
    for route_id in route_ids
    for task_spec in task_specs
)
```

Update scorecard loops to iterate over `_route_ids()` instead of `ROUTE_RUNNERS`.

Update `_recommendation` logic only if necessary; preserve existing recommendation strings.

- [ ] **Step 4: Run focused bake-off tests**

Run:

```bash
cd weld-experience-engine
uv run pytest tests/test_simulation_bakeoff_runner.py tests/test_simulation_bakeoff_report.py -q
```

Expected: PASS. Route score keys and report route summary remain unchanged.

- [ ] **Step 5: Commit Task 3**

```bash
git add weldcore/simulation_bakeoff/bakeoff.py tests/test_simulation_bakeoff_runner.py
git commit -m "refactor: drive simulation bakeoff from adapter registry"
```

## Task 4: Public Exports And Documentation Update

**Files:**
- Modify: `weld-experience-engine/weldcore/simulation_bakeoff/__init__.py`
- Modify: `details.md`
- Modify: `details.html`

- [ ] **Step 1: Verify public exports**

Run:

```bash
cd weld-experience-engine
uv run python - <<'PY'
from weldcore.simulation_bakeoff import (
    SimulationAdapterRoute,
    default_simulation_adapter_routes,
    get_default_batch_route,
    run_adapter_route,
    run_comparison_routes,
)

routes = default_simulation_adapter_routes()
print([route.route_id for route in routes])
print(get_default_batch_route().route_id)
PY
```

Expected output includes:

```text
['simlite_reference', 'maniskill_sapien', 'gazebo_moveit']
maniskill_sapien
```

- [ ] **Step 2: Update `details.md`**

Add a 2026-06-08 update note under 近期更新 or current progress:

```markdown
### 2026-06-08

- 完成统一仿真 adapter 第一轮 facade / registry：simlite、ManiSkill/SAPIEN、Gazebo/MoveIt 已进入同一 route 元数据和执行入口。
- ManiSkill/SAPIEN 仍是阶段性默认入口候选，不是最终仿真器定型。
- 本轮不做小批量样本生成和入口锁定报告；下一轮将围绕 ManiSkill/SAPIEN 小批量默认入口推进。
```

Keep wording clear that this is software structure progress, not real simulation selection or real welding validation.

- [ ] **Step 3: Update `details.html`**

Mirror the same 2026-06-08 note in the HTML reading copy.

- [ ] **Step 4: Commit Task 4**

```bash
git add weldcore/simulation_bakeoff/__init__.py details.md details.html
git commit -m "docs: record simulation adapter registry progress"
```

## Task 5: Full Verification

**Files:**
- No new source files unless verification reveals a bug.

- [ ] **Step 1: Run focused tests**

Run:

```bash
cd weld-experience-engine
uv run pytest \
  tests/test_simulation_adapter_routes.py \
  tests/test_simulation_bakeoff_runner.py \
  tests/test_simulation_bakeoff_report.py \
  tests/test_simulation_bakeoff_adapters.py \
  -q
```

Expected: all selected tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Check stale or overclaiming language**

Run:

```bash
rg -n "最终仿真器定型|真实焊接质量验证|ready_for_robot_execution.*已|ManiSkill/SAPIEN.*最终" README.md details.md docs weld-experience-engine/weldcore
```

Expected: no overclaiming statement introduced by this implementation. Boundary statements that explicitly say these are **not** done are acceptable.

- [ ] **Step 4: Inspect git status and recent commits**

Run:

```bash
git status --short --branch
git log --oneline -5
```

Expected: working tree contains only intentional files. The implementation commits are separate from the already-existing README/details edits unless those docs were intentionally updated in Task 4.

## Execution Notes

- Keep each task small and independently reviewable.
- Do not add batch generation in this first-round plan.
- Do not require installed ManiSkill/SAPIEN, Gazebo, MoveIt, ROS, or Isaac in default tests.
- Do not change `RobotProcessPackageDraft`, `RobotContextSpec`, or `RobotFeasibilityResult` in this round.
- Preserve existing report behavior unless a test explicitly justifies changing it.
- If existing uncommitted README/details edits are present, do not revert them. Work with them and stage only files required by each task.
