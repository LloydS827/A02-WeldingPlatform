# WeldSkillUnit 驱动类机器人仿真路线准备 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the approved WeldSkillUnit simulation-route design into a compact, runnable preparation layer for future robot-like simulation work.

**Architecture:** Update existing current-route docs instead of creating new document sprawl. Add one minimal `weldcore.skill_unit` code boundary and one optional Rerun simulation-evidence bridge, while keeping simlite as the stable L0 baseline and keeping all external simulators as candidates only.

**Tech Stack:** Markdown docs, Python 3.10+, dataclasses, pathlib, pytest, existing `weldcore` package, optional `rerun-sdk`, `uv`, git.

---

## 0. Scope Boundary

Design spec:

- `docs/superpowers/specs/2026-06-04-WeldSkillUnit驱动类机器人仿真路线准备-design.md`

This plan implements the preparation layer only.

It does:

- Update existing current-route docs with `WeldSkillUnit`, R0-R3 role layers, decision matrix, and Rerun evidence boundary.
- Add a minimal `weldcore.skill_unit` package with first-batch skill units and no welding-physics fields.
- Add an optional Rerun bridge for simulation dataset evidence replay without making Rerun a core dependency.
- Keep external simulator routes as decision candidates, not runtime dependencies.
- Keep default tests and core report commands passing.

It does not:

- Choose a final simulator.
- Install or import ManiSkill, Isaac, SAPIEN, Gazebo, MoveIt, RoboDK, RobotStudio, or Process Simulate.
- Implement a real simulator adapter.
- Implement molten-pool, thermal, metallurgical, weld-pool, or in-process closed-loop simulation.
- Claim real welding quality validation.
- Generate or replace WPS/PQR.
- Add new standalone route, matrix, research, or report documents beyond this implementation plan.

---

## 1. File Structure

### Modified Docs

- Modify: `docs/skill-assets/weld-skill-units.md`
  - Responsibility: `WeldSkillUnit` three-layer framework, first-batch units, minimal fields, no-go boundaries.
- Modify: `docs/simulation/robot-like-simulation-route.md`
  - Responsibility: preserve existing L0-L3 simulation maturity layers and add R0-R3 candidate route role overlay plus decision matrix.
- Modify: `docs/evidence/README.md`
  - Responsibility: describe Rerun as optional evidence replay/data inspection layer, not simulator/control bus.
- Modify: `details.md`
  - Responsibility: non-technical progress ledger for this next-stage preparation work.

### New Code Boundary

- Create: `weld-experience-engine/weldcore/skill_unit/__init__.py`
- Create: `weld-experience-engine/weldcore/skill_unit/unit.py`
  - Responsibility: minimal `WeldSkillUnit` dataclass and first-batch unit definitions.

### Modified Code

- Modify: `weld-experience-engine/weldcore/viz/rerun_bridge.py`
  - Responsibility: add optional simulation dataset evidence replay function; core still works without `rerun-sdk`.

### New Tests

- Create: `weld-experience-engine/tests/test_skill_unit_model.py`
- Modify: `weld-experience-engine/tests/test_rerun_bridge.py`

---

## Task 0: Baseline Safety Check

**Files:**
- Read only.

- [ ] **Step 1: Confirm branch and worktree state**

Run from repo root:

```bash
git status --short --branch
```

Expected:

- Branch shown.
- Existing untracked `weld-experience-engine/uv.lock` may appear. Do not stage or delete it unless separately instructed.
- The spec commit may already make local `main` ahead of `origin/main`.

- [ ] **Step 2: Confirm design spec exists**

Run:

```bash
test -f docs/superpowers/specs/2026-06-04-WeldSkillUnit驱动类机器人仿真路线准备-design.md
```

Expected: exit code 0.

- [ ] **Step 3: Run baseline tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass. Current known baseline: `162 passed`.

- [ ] **Step 4: Commit nothing**

No commit for this task.

---

## Task 1: Update WeldSkillUnit Current-Route Documentation

**Files:**
- Modify: `docs/skill-assets/weld-skill-units.md`

- [ ] **Step 1: Replace `docs/skill-assets/weld-skill-units.md`**

Use `apply_patch` to replace the file with:

````markdown
# 焊接技能单元

本页记录第一版 `WeldSkillUnit` 框架，用于后续资料补强、类机器人仿真任务拆分和 `WeldSkillPackage` 组织。

`WeldSkillUnit` 不是生产工艺卡，也不是 WPS/PQR。它描述的是一个可复用、可训练、可评测的焊接动作能力。

## 三层结构

```text
焊缝形态 / seam geometry
× 操作姿态 / welding position or robot posture
× 动作技能 / motion skill
```

## 第一批技能单元

| unit_id | 焊缝形态 | 操作姿态 | 动作技能 | 当前角色 |
| --- | --- | --- | --- | --- |
| `long-straight-horizontal-tracking` | 长直焊缝 | 横焊/近横焊 | 沿缝跟踪、枪姿保持、速度稳定 | 第一批核心 |
| `corner-horizontal-transition` | 包角/转角 | 横焊/近横焊 | 转角过渡、姿态连续、起收弧边界 | 第一批核心 |
| `u-seam-vertical-extension` | U 型缝 | 立焊 | U 型路径、复杂姿态、可达性扩展 | 后续复杂扩展 |

## 最小字段

第一版只需要：

- `unit_id`
- `name`
- `seam_geometry`
- `welding_position`
- `motion_skill`
- `robot_constraints`
- `required_sim_outputs`
- `evaluation_metrics`
- `evidence_requirements`
- `out_of_scope`

## 仿真需求

第一批技能单元需要类机器人仿真优先回答：

- 焊枪 TCP 是否能沿目标路径连续运动。
- 姿态是否能在横焊/近横焊约束下保持稳定。
- 转角处是否出现速度、姿态或路径不连续。
- 机器人约束是否导致不可达、碰撞或关节异常。
- 输出是否能进入 `SkillDataset` 和 `WeldSkillPackage`。

## 当前不做事项

- 不把 `WeldSkillUnit` 写成真实焊接质量结论。
- 不加入熔池、热过程、冶金或真实成形预测字段。
- 不替代 WPS/PQR。
- 不把 `u-seam-vertical-extension` 作为第一批实现起点。
````

- [ ] **Step 2: Verify doc has no forbidden physics route**

Run:

```bash
rg -n "熔池|热过程|冶金|WPS/PQR|long-straight-horizontal-tracking|corner-horizontal-transition" docs/skill-assets/weld-skill-units.md
```

Expected:

- The command finds the two core unit IDs.
- Any `熔池` / `热过程` / `冶金` / `WPS/PQR` matches are in explicit no-go boundary language.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/skill-assets/weld-skill-units.md
git commit -m "docs: define weld skill unit framework"
```

Expected: commit succeeds.

---

## Task 2: Add Minimal WeldSkillUnit Code Boundary

**Files:**
- Create: `weld-experience-engine/tests/test_skill_unit_model.py`
- Create: `weld-experience-engine/weldcore/skill_unit/unit.py`
- Create: `weld-experience-engine/weldcore/skill_unit/__init__.py`

Use TDD for this task.

- [ ] **Step 1: Write failing tests**

Create `weld-experience-engine/tests/test_skill_unit_model.py`:

```python
import json

from weldcore.skill_unit import WeldSkillUnit, default_weld_skill_units


def test_default_weld_skill_units_cover_core_and_reserved_extension_units():
    units = default_weld_skill_units()
    unit_ids = {unit.unit_id for unit in units}

    assert "long-straight-horizontal-tracking" in unit_ids
    assert "corner-horizontal-transition" in unit_ids
    assert "u-seam-vertical-extension" in unit_ids


def test_weld_skill_unit_serializes_minimal_contract():
    unit = WeldSkillUnit(
        unit_id="long-straight-horizontal-tracking",
        name="长直横焊沿缝跟踪",
        seam_geometry="long_straight",
        welding_position="horizontal",
        motion_skill="tracking",
        robot_constraints=("tcp_path_continuity", "torch_posture_stability"),
        required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
        evaluation_metrics=("path_continuity", "posture_stability"),
        evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
        out_of_scope=("real_welding_quality", "WPS/PQR"),
    )

    assert unit.to_dict() == {
        "unit_id": "long-straight-horizontal-tracking",
        "name": "长直横焊沿缝跟踪",
        "seam_geometry": "long_straight",
        "welding_position": "horizontal",
        "motion_skill": "tracking",
        "robot_constraints": ["tcp_path_continuity", "torch_posture_stability"],
        "required_sim_outputs": ["tcp_trajectory", "tool_orientation", "task_status"],
        "evaluation_metrics": ["path_continuity", "posture_stability"],
        "evidence_requirements": [
            "simulation_boundary",
            "requires_real_validation_later",
        ],
        "out_of_scope": ["real_welding_quality", "WPS/PQR"],
    }


def test_default_weld_skill_units_exclude_current_forbidden_physics_fields():
    payload = json.dumps(
        [unit.to_dict() for unit in default_weld_skill_units()],
        ensure_ascii=False,
    ).lower()

    assert "molten" not in payload
    assert "weld_pool" not in payload
    assert "thermal" not in payload
    assert "metallurgy" not in payload
    assert "熔池" not in payload
    assert "热过程" not in payload
    assert "冶金" not in payload
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_skill_unit_model.py
```

Expected: FAIL because `weldcore.skill_unit` does not exist.

- [ ] **Step 3: Create minimal implementation**

Create `weld-experience-engine/weldcore/skill_unit/unit.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WeldSkillUnit:
    unit_id: str
    name: str
    seam_geometry: str
    welding_position: str
    motion_skill: str
    robot_constraints: tuple[str, ...] = ()
    required_sim_outputs: tuple[str, ...] = ()
    evaluation_metrics: tuple[str, ...] = ()
    evidence_requirements: tuple[str, ...] = ()
    out_of_scope: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "robot_constraints",
            "required_sim_outputs",
            "evaluation_metrics",
            "evidence_requirements",
            "out_of_scope",
        ):
            payload[key] = list(payload[key])
        return payload


LONG_STRAIGHT_HORIZONTAL_TRACKING = WeldSkillUnit(
    unit_id="long-straight-horizontal-tracking",
    name="长直横焊沿缝跟踪",
    seam_geometry="long_straight",
    welding_position="horizontal",
    motion_skill="tracking",
    robot_constraints=("tcp_path_continuity", "torch_posture_stability"),
    required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
    evaluation_metrics=("path_continuity", "posture_stability", "speed_stability"),
    evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
    out_of_scope=("real_welding_quality", "WPS/PQR"),
)

CORNER_HORIZONTAL_TRANSITION = WeldSkillUnit(
    unit_id="corner-horizontal-transition",
    name="包角横焊转角过渡",
    seam_geometry="corner",
    welding_position="horizontal",
    motion_skill="corner_transition",
    robot_constraints=("corner_reachability", "orientation_continuity"),
    required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
    evaluation_metrics=("corner_continuity", "posture_stability", "stop_start_boundary"),
    evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
    out_of_scope=("real_welding_quality", "WPS/PQR"),
)

U_SEAM_VERTICAL_EXTENSION = WeldSkillUnit(
    unit_id="u-seam-vertical-extension",
    name="U 型缝立焊扩展单元",
    seam_geometry="u_seam",
    welding_position="vertical",
    motion_skill="complex_path_extension",
    robot_constraints=("reachability_extension", "complex_orientation_change"),
    required_sim_outputs=("tcp_trajectory", "tool_orientation", "task_status"),
    evaluation_metrics=("reachability", "path_continuity", "posture_stability"),
    evidence_requirements=("simulation_boundary", "requires_real_validation_later"),
    out_of_scope=("first_batch_implementation", "real_welding_quality", "WPS/PQR"),
)

DEFAULT_WELD_SKILL_UNITS = (
    LONG_STRAIGHT_HORIZONTAL_TRACKING,
    CORNER_HORIZONTAL_TRANSITION,
    U_SEAM_VERTICAL_EXTENSION,
)


def default_weld_skill_units() -> tuple[WeldSkillUnit, ...]:
    return DEFAULT_WELD_SKILL_UNITS
```

Create `weld-experience-engine/weldcore/skill_unit/__init__.py`:

```python
from .unit import (
    CORNER_HORIZONTAL_TRANSITION,
    DEFAULT_WELD_SKILL_UNITS,
    LONG_STRAIGHT_HORIZONTAL_TRACKING,
    U_SEAM_VERTICAL_EXTENSION,
    WeldSkillUnit,
    default_weld_skill_units,
)

__all__ = [
    "CORNER_HORIZONTAL_TRANSITION",
    "DEFAULT_WELD_SKILL_UNITS",
    "LONG_STRAIGHT_HORIZONTAL_TRACKING",
    "U_SEAM_VERTICAL_EXTENSION",
    "WeldSkillUnit",
    "default_weld_skill_units",
]
```

- [ ] **Step 4: Run skill unit tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_skill_unit_model.py
```

Expected: PASS.

- [ ] **Step 5: Run focused model tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_skill_unit_model.py tests/test_skill_asset_facade.py tests/test_skill_model.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/skill_unit weld-experience-engine/tests/test_skill_unit_model.py
git commit -m "feat: add weld skill unit boundary"
```

Expected: commit succeeds.

---

## Task 3: Update Robot-Like Simulation Route With R0-R3 Decision Matrix

**Files:**
- Modify: `docs/simulation/robot-like-simulation-route.md`

- [ ] **Step 1: Replace `docs/simulation/robot-like-simulation-route.md`**

Use `apply_patch` to replace the file with a compact route page:

````markdown
# 类机器人仿真路线

本页保留 L0-L3 仿真成熟度层，并新增 R0-R3 候选路线角色层。L 层描述仿真能力成熟度，R 层描述候选工具在项目中的角色，二者不能混用。

## L0 几何与轨迹轻量仿真

用于稳定生成和测试几何、轨迹、姿态和 bundle 接入能力。当前 simlite/mock 输出属于这一层。

## L1 机器人运动学、可达性与碰撞仿真

用于评估机器人是否能在给定工位、姿态和路径约束下执行技能资产建议。下一阶段优先关注可达性、关节约束、碰撞和轨迹可执行性。

## L2 机器人任务学习与 demonstration 仿真

用于支持 demonstration、任务学习、策略评估和机器人大脑训练输入。该层依赖更清晰的 `WeldSkillUnit` 和 L1 执行边界。

## L3 焊接过程、热输入和质量物理仿真

用于更高成本的热输入、熔池、成形和质量相关物理分析。该层不是当前起点，也不能替代真实焊接质量验证。

## R0-R3 候选路线角色层

| 角色层 | 候选 | 项目定位 | 当前动作 |
| --- | --- | --- | --- |
| R0 稳定样板 | simlite/mock bundle | 默认测试和 bundle 接入 baseline | 保持稳定，不扩展成复杂仿真器 |
| R1 数据与证据回放 | Rerun | 时间轴记录、回放、标注和调试证据 | 做可选回放样板，不成为核心依赖 |
| R2 机器人学习与任务仿真 | ManiSkill、SAPIEN、Isaac Lab、Gazebo/MoveIt、MuJoCo、PyBullet | 技能数据生成、可执行性、训练与评测 | 下一轮最多选择 2 条路线做最小 bake-off |
| R3 工业落地对照 | RoboDK、ABB RobotStudio、Siemens Process Simulate | 离线编程、工位、机器人型号和虚拟调试对照 | 先调研，不进入第一轮代码实现 |

## 决策矩阵

评估顺序固定为：

```text
技能数据生成 -> 机器人可执行性 -> 训练机器人大脑 -> 工业落地对照
```

| 维度 | 权重 | 检查问题 |
| --- | ---: | --- |
| 技能数据生成 | 40% | 能否输出 `SkillDataset` / `WeldSkillPackage` 需要的轨迹、姿态、任务状态、评测和 evidence |
| 机器人可执行性 | 30% | 是否支持机器人模型、IK、碰撞、运动规划、姿态约束 |
| 训练机器人大脑 | 20% | 是否支持 demonstration、RL/IL、policy evaluation、benchmark |
| 工业落地对照 | 10% | 是否有离线编程、真实机器人生态、工位/夹具/部署参考 |

## 第一轮最小验证建议

- R1：用 Rerun 回放 simlite 或 `SimulationOutputBundle` 导入后的轨迹、姿态、任务状态和评测证据。
- R2：优先比较 ManiSkill/SAPIEN 方向和 Gazebo/MoveIt 方向。
- R3：只调研 API、路径导入导出、机器人品牌和虚拟调试约束，不写入核心 schema。

## Adapter 评估口径

- adapter 是否能输出或转换为项目 canonical schema。
- adapter 是否能补强 `WeldSkillPackage` 的 trajectory、posture、applicability、failure boundary 或 robot execution suggestion。
- adapter 是否能围绕同一组 `WeldSkillUnit` 比较。
- adapter 是否保持证据边界，不把仿真输出直接写成真实质量结论。
````

- [ ] **Step 2: Verify L/R layer clarity**

Run:

```bash
rg -n "L0|L1|L2|L3|R0|R1|R2|R3|熔池|WPS/PQR" docs/simulation/robot-like-simulation-route.md
```

Expected:

- L0-L3 and R0-R3 both appear.
- L3 / `熔池` / `WPS/PQR` only appear in boundary language.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs/simulation/robot-like-simulation-route.md
git commit -m "docs: add simulation route decision matrix"
```

Expected: commit succeeds.

---

## Task 4: Add Optional Rerun Simulation Evidence Replay Boundary

**Files:**
- Modify: `weld-experience-engine/weldcore/viz/rerun_bridge.py`
- Modify: `weld-experience-engine/tests/test_rerun_bridge.py`

Use TDD for this task.

- [ ] **Step 1: Write failing test**

Append this test to `weld-experience-engine/tests/test_rerun_bridge.py`:

```python
from pathlib import Path

from weldcore.ingest import import_simulation_bundle
from weldcore.knowledge.synthetic_manifest import load_synthetic_input_foundation
from weldcore.sim import write_simlite_bundle
from weldcore.viz.rerun_bridge import log_simulation_dataset_evidence


def test_rerun_bridge_can_attempt_simulation_dataset_evidence_without_rerun(
    tmp_path: Path,
):
    foundation = load_synthetic_input_foundation()
    bundle = write_simlite_bundle(
        tmp_path,
        input_id="input-panel-butt-001",
        sample_count=1,
        seed=21,
        foundation=foundation,
    )
    result = import_simulation_bundle(bundle, foundation=foundation)

    logged = log_simulation_dataset_evidence(
        result.dataset,
        result.run_record,
        spawn=False,
    )

    assert logged in {True, False}
```

If this creates duplicate imports, normalize the imports at the top of the file after the test is written.

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_rerun_bridge.py::test_rerun_bridge_can_attempt_simulation_dataset_evidence_without_rerun
```

Expected: FAIL because `log_simulation_dataset_evidence` does not exist.

- [ ] **Step 3: Add minimal optional Rerun implementation**

Modify `weld-experience-engine/weldcore/viz/rerun_bridge.py`.

Add imports:

```python
import json

from ..model import SimulationRunRecord, SkillDataset
```

Add this function below `log_skill_transfer`:

```python
def log_simulation_dataset_evidence(
    dataset: SkillDataset,
    run_record: SimulationRunRecord | None = None,
    spawn: bool = True,
) -> bool:
    try:
        import rerun as rr
    except ImportError:
        print("rerun 未安装，跳过仿真证据回放 (pip install rerun-sdk)")
        return False

    rr.init(f"weld-simulation-evidence-{dataset.dataset_id}", spawn=spawn)
    rr.log("simulation/dataset_id", rr.TextDocument(dataset.dataset_id))
    rr.log("simulation/task", rr.TextDocument(dataset.task))

    if run_record is not None:
        rr.log(
            "simulation/run_record",
            rr.TextDocument(
                json.dumps(run_record.to_dict(), ensure_ascii=False, indent=2)
            ),
        )

    for sample in dataset.samples:
        sample_path = f"simulation/samples/{sample.sample_id}"
        rr.log(
            f"{sample_path}/metadata",
            rr.TextDocument(
                json.dumps(sample.metadata, ensure_ascii=False, indent=2)
            ),
        )
        for point in sample.trajectory.samples:
            rr.set_time_seconds("weld_time", point.t)
            rr.log(
                f"{sample_path}/tcp",
                rr.Points3D([[point.x, point.y, point.z]], colors=[[0, 128, 255]]),
            )

    return True
```

Keep `rerun-sdk` optional. Do not import `rerun` at module import time.

- [ ] **Step 4: Run Rerun bridge tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_rerun_bridge.py
```

Expected: all Rerun bridge tests pass whether or not `rerun-sdk` is installed.

- [ ] **Step 5: Run focused simulation tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_rerun_bridge.py tests/test_simlite_bundle.py tests/test_simulation_bundle_import.py tests/test_simulation_io_models.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/viz/rerun_bridge.py weld-experience-engine/tests/test_rerun_bridge.py
git commit -m "feat: add optional rerun simulation evidence replay"
```

Expected: commit succeeds.

---

## Task 5: Update Evidence And Progress Boundaries

**Files:**
- Modify: `docs/evidence/README.md`
- Modify: `details.md`

- [ ] **Step 1: Update `docs/evidence/README.md`**

Use `apply_patch` to extend the file with:

````markdown
## Rerun 回放边界

Rerun 可作为 R1 数据接入、时间轴回放、标注和证据可视化工具。

它用于帮助检查：

- 仿真输出轨迹是否可回放。
- 姿态、任务状态和过程信号是否能与时间轴对齐。
- `WeldSkillPackage` 的 evidence 是否可追溯。

Rerun 不是仿真器，不是机器人控制总线，也不是生产数据库。未安装 `rerun-sdk` 时，基础测试和默认报告命令必须仍然可运行。
````

- [ ] **Step 2: Update `details.md`**

Modify the "下一步" and "风险提醒" sections so non-technical readers can see:

- The current next-stage preparation is `WeldSkillUnit` plus robot-like simulation route preparation.
- The project is still not choosing a final simulator.
- Rerun is a data replay/evidence tool, not a simulator.
- External tools remain candidates or industrial reference routes.

Keep the update concise; do not rewrite the whole file.

- [ ] **Step 3: Verify boundary wording**

Run:

```bash
rg -n "Rerun|WeldSkillUnit|最终仿真器|真实焊接质量|WPS/PQR|仿真器" docs/evidence/README.md details.md
```

Expected:

- Rerun appears as a replay/evidence boundary.
- Any real quality / WPS/PQR matches are boundary warnings, not completion claims.

- [ ] **Step 4: Commit**

Run:

```bash
git add docs/evidence/README.md details.md
git commit -m "docs: clarify evidence replay and next simulation prep"
```

Expected: commit succeeds.

---

## Task 6: Full Verification And Reference Audit

**Files:**
- Read only unless fixing issues found by verification.

- [ ] **Step 1: Run full test suite**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run focused report commands**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.simulation_ingest_report
```

Expected:

- Both commands complete.
- `simulation_ingest_report` still writes/refreshes docs copy under `../docs/evidence/data-foundation/reports/`.

- [ ] **Step 3: Audit document sprawl**

Run from repo root:

```bash
git diff --name-only 5141900..HEAD
```

Expected:

- No new standalone docs beyond this plan and the approved spec.
- Current-route changes should be limited to existing docs listed in this plan.

- [ ] **Step 4: Audit forbidden overclaims**

Run:

```bash
rg -n "真实焊接质量已经验证|替代 WPS|替代 PQR|完整 ManiSkill|完整 Isaac|熔池闭环已经完成|已选择最终仿真器" README.md details.md docs/architecture docs/skill-assets docs/simulation docs/evidence weld-experience-engine/README.md || true
```

Expected: no matches that make a forbidden claim. Negative/boundary language is acceptable.

- [ ] **Step 5: Audit optional dependency boundary**

Run:

```bash
rg -n "^import rerun|from rerun" weld-experience-engine/weldcore weld-experience-engine/tests || true
```

Expected:

- No module-level `import rerun` or `from rerun` outside local imports inside bridge functions.

- [ ] **Step 6: Verify generated outputs are not staged**

Run:

```bash
git status --short
git diff --cached --name-only
```

Expected:

- Existing untracked `weld-experience-engine/uv.lock` may remain.
- No generated `*_report_out/`, `__pycache__/`, `.pytest_cache/`, or runtime artifacts staged.

- [ ] **Step 7: Commit fixes only if needed**

If Steps 1-6 require fixes, make them with `apply_patch`, rerun the failing command, then commit:

```bash
git add <fixed files>
git commit -m "fix: complete weld skill unit simulation prep verification"
```

If no fixes are required, commit nothing.

---

## Task 7: Completion Handoff

**Files:**
- Read only.

- [ ] **Step 1: Summarize commits and status**

Run:

```bash
git log --oneline -n 8
git status --short --branch
```

Expected:

- Recent commits include the design spec and implementation commits.
- Only expected untracked files remain.

- [ ] **Step 2: Prepare final implementation summary**

Summary must include:

- `WeldSkillUnit` framework updates.
- R0-R3 role overlay and preserved L0-L3 maturity layers.
- Minimal code boundary added.
- Rerun optional replay boundary.
- Tests and report commands run.
- Any remaining untracked runtime outputs.
- Clear statement that simulator selection and simulator adapter implementation are still future work.

- [ ] **Step 3: Do not mark simulation work complete**

This plan completes route-preparation work only. It does not complete final simulator selection, simulator adapter implementation, robot execution validation, or real welding quality validation.
