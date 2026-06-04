# Physical AI 焊接技能资产项目级重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure this repository from a POC/gate/report collection into a Physical AI welding skill-asset development base centered on `WeldSkillPackage`, while keeping the default project runnable and verified.

**Architecture:** Keep the Python engine stable first, then add a clearer documentation and code boundary around skill assets. Move evidence materials under `docs/evidence`, archive prior POC/MVP/gate artifacts with indexes, and keep current report commands working by updating hard-coded paths and tests. Do not implement a new simulator in this phase.

**Tech Stack:** Markdown docs, Python 3.10+, dataclasses, pathlib, pytest, existing `weldcore` package, `uv`, git.

---

## 0. Scope Boundary

Design spec:

- `docs/superpowers/specs/2026-06-04-PhysicalAI焊接技能资产项目级重构-design.md`

This plan implements the first-stage project-level restructure only.

It does:

- Reframe the repository around `WeldSkillPackage` / industrial skill assets.
- Create current-route documentation under `docs/architecture`, `docs/skill-assets`, `docs/simulation`, and `docs/evidence`.
- Move `docs/data-foundation` to `docs/evidence/data-foundation` and update code/tests that depend on that path.
- Archive older POC/MVP/gate docs and the whitepaper report so they remain accessible but no longer dominate the default route.
- Update root README, `details.md`, and `weld-experience-engine/README.md`.
- Add a small `weldcore.skill_asset` facade so the codebase has a stable skill-asset import boundary without moving all existing model code.
- Verify tests and required report commands.

It does not:

- Choose a final simulator.
- Implement ROS/MoveIt/Gazebo, Isaac, ManiSkill, SAPIEN, RoboDK, or robot SDK integration.
- Generate a new bulk dataset.
- Claim real welding quality validation.
- Generate or replace WPS/PQR.
- Add molten-pool / weld-pool fields or in-process closed-loop control.
- Delete historical work.

---

## 1. Migration Map

Use this table as the implementation source of truth.

| Current path | Target path / action | Reason | Required updates |
| --- | --- | --- | --- |
| `README.md` | Rewrite in place | Default entry becomes Physical AI welding skill-asset base | Root links, default commands, current phase language |
| `details.md` | Rewrite/update in place | Non-technical progress ledger must reflect project-level restructure | Stage judgment, completed vs current vs next |
| `weld-experience-engine/README.md` | Rewrite/update in place | Engine entry should point to skill-asset core and report boundaries | Keep commands; demote historical report language |
| `docs/strategy/` | Keep in place | Strategic source of truth | Link from root README and architecture docs |
| `docs/project/` | Keep in place | Project/contract/previous plan materials | Link as project background, not default technical route |
| `docs/reference/` | Keep in place | External/pre-project references | Link from archive/project index if needed |
| `docs/data-foundation/` | `docs/evidence/data-foundation/` via `git mv` | Evidence materials belong under evidence boundary | Update `DEFAULT_FOUNDATION_ROOT`, tests, README/details links |
| `docs/specs/2026-05-*` | `docs/archive/poc-mvp/specs/` via `git mv` | Historical POC/MVP specs | Update root README links; archive index |
| `docs/plans/2026-05-*` | `docs/archive/poc-mvp/plans/` via `git mv` | Historical POC/MVP plans | Update root README links; archive index |
| `docs/plans/2026-06-04-下一阶段场景仿真与接入计划.md` | `docs/archive/old-plans/` via `git mv` | Superseded by skill-asset restructure | Archive index states it is superseded |
| `docs/superpowers/specs/2026-06-01-*` and `2026-06-02-*` and `2026-06-03-*` | `docs/archive/gates/superpowers/specs/` via `git mv` | Historical gate specs | Keep current 2026-06-04 restructure spec in place |
| `docs/superpowers/plans/2026-06-01-*` through `2026-06-03-*` | `docs/archive/gates/superpowers/plans/` via `git mv` | Historical gate implementation plans | Keep current plan in place |
| `report/` | `docs/archive/whitepaper/report/` via `git mv` | Whitepaper is historical evidence package | Root README and archive index |
| `weld-experience-engine/weldcore/model/skill.py` | Keep in place | Existing core model remains stable | Add facade rather than moving model code now |
| `weld-experience-engine/weldcore/knowledge/manifest.py` | Modify | Hard-coded foundation path changes | `DEFAULT_FOUNDATION_ROOT` becomes `docs/evidence/data-foundation` |
| `weld-experience-engine/weldcore/report/*` | Modify only if needed for path constants | Report commands must still work | Tests should prove docs copy paths |
| `weld-experience-engine/weldcore/skill_asset/` | Create | Stable current-route code boundary | Re-export existing skill package builders |
| Runtime dirs such as `*_report_out/` | Do not stage; leave ignored/untracked | Generated artifacts | Verify no generated output is committed |

Historical documents moved to archive may retain old internal links as historical text. Current-route documents (`README.md`, `details.md`, `docs/architecture`, `docs/skill-assets`, `docs/simulation`, `docs/evidence`, `weld-experience-engine/README.md`) must use the new paths.

---

## 2. File Structure

### New / Current Route Docs

- Create: `docs/architecture/README.md`
  - Purpose: current architecture index and five-layer system pointer.
- Create: `docs/architecture/five-layer-system.md`
  - Purpose: define knowledge, skill data, skill asset, robot execution, evidence/boundary layers.
- Create: `docs/architecture/module-boundaries.md`
  - Purpose: map docs and code modules to strategic layers and adapter principles.
- Create: `docs/skill-assets/README.md`
  - Purpose: default skill-asset route.
- Create: `docs/skill-assets/weld-skill-package.md`
  - Purpose: define `WeldSkillPackage` fields and relation to existing code.
- Create: `docs/skill-assets/weld-skill-units.md`
  - Purpose: first-pass framework for U-shaped seams, corners, long straight seams, horizontal/vertical welding, and other weld-skill units.
- Create: `docs/simulation/README.md`
  - Purpose: class-robot simulation route index.
- Create: `docs/simulation/robot-like-simulation-route.md`
  - Purpose: L0/L1/L2/L3 simulation layers and adapter candidates.
- Create: `docs/evidence/README.md`
  - Purpose: evidence boundary index.
- Create: `docs/archive/README.md`
  - Purpose: archive index explaining POC/MVP/gate/whitepaper locations and status.

### Moved Docs / Evidence

- Move: `docs/data-foundation/` -> `docs/evidence/data-foundation/`
- Move: `docs/specs/2026-05-30-焊接经验结构化论证白皮书-design.md` -> `docs/archive/poc-mvp/specs/2026-05-30-焊接经验结构化论证白皮书-design.md`
- Move: `docs/specs/2026-05-31-焊接技能迁移MVP-design.md` -> `docs/archive/poc-mvp/specs/2026-05-31-焊接技能迁移MVP-design.md`
- Move: `docs/plans/2026-05-30-焊接经验结构化POC与论证白皮书.md` -> `docs/archive/poc-mvp/plans/2026-05-30-焊接经验结构化POC与论证白皮书.md`
- Move: `docs/plans/2026-05-31-焊接技能迁移MVP实施计划.md` -> `docs/archive/poc-mvp/plans/2026-05-31-焊接技能迁移MVP实施计划.md`
- Move: `docs/plans/2026-06-04-下一阶段场景仿真与接入计划.md` -> `docs/archive/old-plans/2026-06-04-下一阶段场景仿真与接入计划.md`
- Move older gate specs/plans from `docs/superpowers/` to `docs/archive/gates/superpowers/`.
- Move: `report/` -> `docs/archive/whitepaper/report/`

### Modified Code

- Modify: `weld-experience-engine/weldcore/knowledge/manifest.py`
  - Change default docs evidence root to `docs/evidence/data-foundation`.
- Modify if needed: `weld-experience-engine/weldcore/report/data_foundation_report.py`
- Modify if needed: `weld-experience-engine/weldcore/report/synthetic_v2_input_report.py`
- Modify if needed: `weld-experience-engine/weldcore/report/simulation_ingest_report.py`
- Create: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Create: `weld-experience-engine/weldcore/skill_asset/package.py`

### Modified Tests

- Modify: `weld-experience-engine/tests/test_data_foundation_report.py`
- Modify: `weld-experience-engine/tests/test_synthetic_v2_input_report.py`
- Create: `weld-experience-engine/tests/test_skill_asset_facade.py`

### Modified Docs

- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Modify if needed: `docs/strategy/README.md`

---

## 3. Report Command Classification

The implementation must preserve these command classes:

| Command | Class | Must pass? | Notes |
| --- | --- | --- | --- |
| `uv run pytest -q` | Default verification | Yes | Primary required check |
| `uv run python -m weldcore.report.mvp_report` | Skill-asset evidence | Yes | Proves early `WeldSkillPackage` loop still works |
| `uv run python -m weldcore.report.simulation_ingest_report` | Simulation ingest evidence | Yes | Proves adapter-style ingest still works after evidence path move |
| `uv run python -m weldcore.report.data_foundation_report` | Evidence boundary | Yes | Must write docs copy to `docs/evidence/data-foundation/reports` |
| `uv run python -m weldcore.report.synthetic_v2_input_report` | Evidence boundary | Yes | Must write docs copy to `docs/evidence/data-foundation/reports` |
| `uv run python -m weldcore.report.generate` | Historical POC evidence | Should pass | Historical, but should not break in this phase |
| `uv run python -m weldcore.report.scenario_report` | Historical gate evidence | Should pass | Historical, but should not break in this phase |

Generated output directories must not be staged.

---

## Task 0: Baseline Safety Check

**Files:**
- Read only.

- [ ] **Step 1: Confirm worktree state**

Run:

```bash
git status --short --branch
```

Expected:

- Branch shown.
- The design spec commit may already exist.
- Untracked runtime outputs such as `weld-experience-engine/simulation_ingest_report_out/`, `weld-experience-engine/synthetic_v2_input_report_out/`, and `weld-experience-engine/uv.lock` may appear. Do not stage or delete them unless separately instructed.

- [ ] **Step 2: Confirm design spec exists**

Run:

```bash
test -f docs/superpowers/specs/2026-06-04-PhysicalAI焊接技能资产项目级重构-design.md
```

Expected: exit code 0.

- [ ] **Step 3: Run baseline tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q
```

Expected: all tests pass. Current known baseline: `160 passed`.

- [ ] **Step 4: Commit nothing**

No commit for this task.

---

## Task 1: Current Route Documentation Skeleton

**Files:**
- Create: `docs/architecture/README.md`
- Create: `docs/architecture/five-layer-system.md`
- Create: `docs/architecture/module-boundaries.md`
- Create: `docs/skill-assets/README.md`
- Create: `docs/skill-assets/weld-skill-package.md`
- Create: `docs/skill-assets/weld-skill-units.md`
- Create: `docs/simulation/README.md`
- Create: `docs/simulation/robot-like-simulation-route.md`
- Create: `docs/evidence/README.md`
- Create: `docs/archive/README.md`

- [ ] **Step 1: Create directory skeleton**

Run:

```bash
mkdir -p docs/architecture docs/skill-assets docs/simulation docs/evidence docs/archive
```

Expected: directories exist.

- [ ] **Step 2: Write `docs/architecture/README.md`**

Use `apply_patch` to create:

```markdown
# 架构总览

本目录描述 A02 焊接技能大师平台在 Physical AI 方向下的当前架构。

当前主线不是单一仿真器、机器人程序或报告命令，而是围绕 `WeldSkillPackage`
沉淀可学习、可迁移、可执行、可审计的焊接技能资产。

## 当前入口

- [五层系统架构](five-layer-system.md)
- [模块边界与 adapter 原则](module-boundaries.md)

## 核心判断

```text
工艺知识 / 动作经验 / 过程数据
-> SkillDataset
-> WeldSkillPackage
-> 机器人训练 / 类机器人仿真 / 执行基线
-> 评测、证据、边界
```
```

- [ ] **Step 3: Write `docs/architecture/five-layer-system.md`**

Create a concise five-section document with these headings:

```markdown
# 五层系统架构

## 1. 工艺知识层
## 2. 技能数据层
## 3. 技能资产层
## 4. 机器人执行层
## 5. 证据与边界层
## 不做事项
```

Each layer must include `职责`、`输入`、`输出`、`当前项目对应物`、`不做事项`.

- [ ] **Step 4: Write `docs/architecture/module-boundaries.md`**

Create a module map:

```markdown
# 模块边界与 Adapter 原则

## 核心对象

`WeldSkillPackage` 是项目核心对象。

## 当前代码边界

| 模块 | 当前职责 | 重构后定位 |
| --- | --- | --- |
| `weldcore.model` | 数据模型 | 保留基础模型 |
| `weldcore.transfer` | 技能迁移与评测 | 技能资产能力 |
| `weldcore.knowledge` | 资料和字段约束 | 工艺知识与证据来源 |
| `weldcore.sim` | simlite/mock 输出 | L0 稳定仿真 |
| `weldcore.ingest` | 仿真 bundle 导入 | Adapter 输入边界 |
| `weldcore.report` | 证据报告 | 证据输出 |

## Adapter 原则

- 仿真器、机器人、焊机、工作站都通过 adapter 接入。
- adapter 必须输出或转换为项目 canonical schema。
- adapter 不能替代 `WeldSkillPackage`。
```

- [ ] **Step 5: Write skill asset docs**

Create `docs/skill-assets/README.md` with links to:

- `weld-skill-package.md`
- `weld-skill-units.md`

Create `docs/skill-assets/weld-skill-package.md` with sections:

```markdown
# WeldSkillPackage

## 定位
## 最小字段
## 与 SkillDataset 的关系
## 与机器人执行的关系
## 与证据边界的关系
## 当前代码对应
```

Include the minimum field list from the spec:

- task
- source
- trajectory
- posture
- process parameters
- applicability
- transfer rules
- failure boundary
- robot execution suggestion
- evidence status

Create `docs/skill-assets/weld-skill-units.md` with a first-pass weld-skill unit table:

| 技能单元 | 说明 | 当前证据状态 |
| --- | --- | --- |
| 长直焊缝 | 长距离连续轨迹与姿态稳定 | 待资料补强 |
| U 型缝 | U 型路径或近似 U 型焊缝运动 | 待术语校正和资料补强 |
| 包角 / 转角 | 转角过渡、姿态变化和停留策略 | 待资料补强 |
| 横焊 | 横向姿态约束和枪姿稳定 | 待资料补强 |
| 立焊 | 立向姿态、重力影响和参数边界 | 待资料补强 |

- [ ] **Step 6: Write simulation docs**

Create `docs/simulation/README.md` with the current simulation boundary:

- Current route: class-robot simulation.
- L0 simlite remains a stable test tool.
- L1 robot kinematics/reachability/collision is the next likely priority.
- L2 task learning / demonstration simulation is a later evaluation layer.
- L3 welding process/quality physics is not the current start.

Create `docs/simulation/robot-like-simulation-route.md` with sections:

```markdown
# 类机器人仿真路线

## L0 几何与轨迹轻量仿真
## L1 机器人运动学、可达性与碰撞仿真
## L2 机器人任务学习与 demonstration 仿真
## L3 焊接过程、热输入和质量物理仿真
## Adapter 评估口径
```

- [ ] **Step 7: Write evidence and archive indexes**

Create `docs/evidence/README.md`:

```markdown
# 证据与边界

本目录保存资料来源、字段覆盖、证据报告和质量边界材料。

证据用于约束技能资产，不等于真实焊接质量验证，不替代 WPS/PQR。

## 当前目录

- `data-foundation/`：资料来源、manifest、字段覆盖、任务证据和报告。
```

Create `docs/archive/README.md` with these sections:

```markdown
# 历史证据与归档

归档不是否定前期成果，而是把阶段性 POC、MVP、gate、白皮书放回正确上下文。

## POC / MVP
## Gate 设计与实施计划
## 白皮书
## 旧计划
## 仍可运行的历史命令
```

- [ ] **Step 8: Verify docs exist**

Run:

```bash
test -f docs/architecture/README.md
test -f docs/skill-assets/weld-skill-package.md
test -f docs/simulation/robot-like-simulation-route.md
test -f docs/evidence/README.md
test -f docs/archive/README.md
```

Expected: all exit code 0.

- [ ] **Step 9: Commit**

Run:

```bash
git add docs/architecture docs/skill-assets docs/simulation docs/evidence/README.md docs/archive/README.md
git commit -m "docs: add skill asset route skeleton"
```

Expected: commit succeeds.

---

## Task 2: Move Data Foundation Into Evidence Boundary

**Files:**
- Move: `docs/data-foundation/` -> `docs/evidence/data-foundation/`
- Modify: `weld-experience-engine/weldcore/knowledge/manifest.py`
- Modify: `weld-experience-engine/tests/test_data_foundation_report.py`
- Modify: `weld-experience-engine/tests/test_synthetic_v2_input_report.py`
- Modify: `README.md`, `details.md`, `weld-experience-engine/README.md` only for narrow `docs/data-foundation` -> `docs/evidence/data-foundation` path updates.
- Keep Task 4 responsible for the full narrative rewrite of those files.

- [ ] **Step 1: Move directory with git**

Run:

```bash
git mv docs/data-foundation docs/evidence/data-foundation
```

Expected: `docs/evidence/data-foundation/README.md` exists.

- [ ] **Step 2: Update `DEFAULT_FOUNDATION_ROOT`**

In `weld-experience-engine/weldcore/knowledge/manifest.py`, change:

```python
DEFAULT_FOUNDATION_ROOT = Path(__file__).resolve().parents[3] / "docs" / "data-foundation"
```

to:

```python
DEFAULT_FOUNDATION_ROOT = (
    Path(__file__).resolve().parents[3] / "docs" / "evidence" / "data-foundation"
)
```

- [ ] **Step 3: Update default docs path tests**

In `weld-experience-engine/tests/test_data_foundation_report.py`, update `test_data_foundation_report_default_docs_dir_points_to_repo_docs` to assert the new path:

```python
def test_data_foundation_report_default_docs_dir_points_to_repo_docs():
    assert DEFAULT_DOCS_REPORT_DIR.name == "reports"
    assert DEFAULT_DOCS_REPORT_DIR.parent.name == "data-foundation"
    assert DEFAULT_DOCS_REPORT_DIR.parent.parent.name == "evidence"
    assert DEFAULT_DOCS_REPORT_DIR.parent.parent.parent.name == "docs"
```

In `weld-experience-engine/tests/test_synthetic_v2_input_report.py`, update `test_synthetic_v2_input_report_default_docs_dir_points_to_repo_docs` the same way.

Also add the same default docs path regression coverage for `weld-experience-engine/tests/test_simulation_ingest_report.py`, because `simulation_ingest_report` derives its docs copy destination from the migrated foundation root.

- [ ] **Step 4: Update moved evidence docs internal references**

Modify `docs/evidence/README.md` so the `data-foundation/` entry points to the moved directory and says it is the evidence boundary for sources, manifests, field coverage, and reports.

Then update moved `data-foundation` internal self-references from `docs/data-foundation/...` to `docs/evidence/data-foundation/...`, at minimum:

- `docs/evidence/data-foundation/research/synthetic_v2_input_research.md`
- any moved manifest `source_refs` or report text that should point to the current evidence path rather than historical text.

Use this command to locate the references after the move:

```bash
rg -n "docs/data-foundation" docs/evidence/data-foundation
```

Expected after edits: no matches under `docs/evidence/data-foundation`.

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q \
  tests/test_data_foundation_manifests.py \
  tests/test_data_foundation_report.py \
  tests/test_synthetic_input_manifests.py \
  tests/test_synthetic_v2_input_report.py \
  tests/test_simulation_ingest_report.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Run report commands that depend on the moved path**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
```

Expected:

- commands complete without gate failure.
- docs copies are written under `docs/evidence/data-foundation/reports/`.

- [ ] **Step 7: Verify no old current-route path remains outside archive/history**

Run from repo root:

```bash
rg -n "docs/data-foundation" README.md details.md weld-experience-engine/README.md project-sync-overview.html docs/architecture docs/skill-assets docs/simulation docs/evidence weld-experience-engine/weldcore weld-experience-engine/tests || true
```

Expected: no matches in current-route files. Matches inside archive are acceptable after Task 3.

Include `README.md`, `details.md`, and `weld-experience-engine/README.md` in this audit only for stale `docs/data-foundation` path references. Task 4 still owns the full narrative rewrite.

- [ ] **Step 8: Commit**

Run:

```bash
git add docs/evidence/data-foundation docs/evidence/README.md \
  weld-experience-engine/weldcore/knowledge/manifest.py \
  weld-experience-engine/tests/test_data_foundation_report.py \
  weld-experience-engine/tests/test_synthetic_v2_input_report.py
git commit -m "docs: move data foundation under evidence"
```

Expected: commit succeeds. Generated report output directories must not be staged.

---

## Task 3: Archive Historical POC, MVP, Gate, And Whitepaper Materials

**Files:**
- Move: `docs/specs/2026-05-*`
- Move: `docs/plans/2026-05-*`
- Move: `docs/plans/2026-06-04-下一阶段场景仿真与接入计划.md`
- Move: older `docs/superpowers/specs/2026-06-01-*`, `2026-06-02-*`, `2026-06-03-*`
- Move: older `docs/superpowers/plans/2026-06-01-*`, `2026-06-02-*`, `2026-06-03-*`
- Move: `report/`
- Modify: `docs/archive/README.md`

- [ ] **Step 1: Create archive subdirectories**

Run:

```bash
mkdir -p \
  docs/archive/poc-mvp/specs \
  docs/archive/poc-mvp/plans \
  docs/archive/gates/superpowers/specs \
  docs/archive/gates/superpowers/plans \
  docs/archive/old-plans \
  docs/archive/whitepaper
```

Expected: directories exist.

- [ ] **Step 2: Move POC/MVP specs and plans**

Run:

```bash
git mv docs/specs/2026-05-30-焊接经验结构化论证白皮书-design.md docs/archive/poc-mvp/specs/
git mv docs/specs/2026-05-31-焊接技能迁移MVP-design.md docs/archive/poc-mvp/specs/
git mv docs/plans/2026-05-30-焊接经验结构化POC与论证白皮书.md docs/archive/poc-mvp/plans/
git mv docs/plans/2026-05-31-焊接技能迁移MVP实施计划.md docs/archive/poc-mvp/plans/
```

Expected: old `docs/specs` may become empty; old `docs/plans` still contains the 2026-06-04 plan until Step 3.

- [ ] **Step 3: Move superseded next-stage plan**

Run:

```bash
git mv docs/plans/2026-06-04-下一阶段场景仿真与接入计划.md docs/archive/old-plans/
```

Expected: file is moved.

- [ ] **Step 4: Move old gate superpowers specs**

Run:

```bash
git mv docs/superpowers/specs/2026-06-01-* docs/archive/gates/superpowers/specs/
git mv docs/superpowers/specs/2026-06-02-* docs/archive/gates/superpowers/specs/
git mv docs/superpowers/specs/2026-06-03-* docs/archive/gates/superpowers/specs/
```

Expected:

- `docs/superpowers/specs/2026-06-04-PhysicalAI焊接技能资产项目级重构-design.md` remains in `docs/superpowers/specs/`.

- [ ] **Step 5: Move old gate superpowers plans**

Run:

```bash
git mv docs/superpowers/plans/2026-06-01-* docs/archive/gates/superpowers/plans/
git mv docs/superpowers/plans/2026-06-02-* docs/archive/gates/superpowers/plans/
git mv docs/superpowers/plans/2026-06-03-* docs/archive/gates/superpowers/plans/
```

Expected:

- Current `docs/superpowers/plans/2026-06-04-PhysicalAI焊接技能资产项目级重构实施计划.md` remains in `docs/superpowers/plans/`.

- [ ] **Step 6: Move whitepaper report package**

Run:

```bash
git mv report docs/archive/whitepaper/report
```

Expected: `docs/archive/whitepaper/report/船舶焊接工艺大脑平台_风险驱动论证白皮书.md` exists.

- [ ] **Step 7: Update archive index**

Update `docs/archive/README.md` so it includes a concrete index:

```markdown
## POC / MVP

- `poc-mvp/specs/`
- `poc-mvp/plans/`

## Gate 设计与实施计划

- `gates/superpowers/specs/`
- `gates/superpowers/plans/`

## 白皮书

- `whitepaper/report/`

## 旧计划

- `old-plans/2026-06-04-下一阶段场景仿真与接入计划.md`：已被 Physical AI 焊接技能资产项目级重构路线取代。
```

- [ ] **Step 8: Verify current superpowers docs remain**

Run:

```bash
test -f docs/superpowers/specs/2026-06-04-PhysicalAI焊接技能资产项目级重构-design.md
test -f docs/superpowers/plans/2026-06-04-PhysicalAI焊接技能资产项目级重构实施计划.md
```

Expected: both files exist.

- [ ] **Step 9: Commit**

Run:

```bash
git add docs/archive docs/superpowers
git commit -m "docs: archive historical poc and gate materials"
```

Expected: commit succeeds.

---

## Task 4: Rewrite Default Project Entries

**Files:**
- Modify: `README.md`
- Modify: `details.md`
- Modify: `weld-experience-engine/README.md`
- Modify if needed: `docs/strategy/README.md`

- [ ] **Step 1: Rewrite root README around skill assets**

Replace the current README narrative with these sections:

```markdown
# Physical AI 焊接技能资产底座

## 一句话定义
## 当前阶段
## 核心对象：WeldSkillPackage
## 当前主线
## 已完成基础能力
## 当前目录结构
## 如何验证
## 当前不做事项
## 历史证据与归档
## Agent 维护规则
```

Required language:

- State that this repository supports the A02 welding skill master platform under the Physical AI direction.
- State that `WeldSkillPackage` is the core object.
- State that current work is first-stage project-level restructure.
- State that second stage is weld-skill units plus class-robot simulation route.
- State that `stiffened-panel-fillet` is now a historical/industry instance, not the default project mainline.
- Keep the default verification command:

```bash
cd weld-experience-engine
uv sync --extra dev --extra viz
uv run pytest -q
```

- Keep report commands, but classify them as evidence/historical support.

- [ ] **Step 2: Update `details.md`**

Update `details.md` with non-technical language:

- Current stage: project-level restructure around `WeldSkillPackage`.
- Already completed: baseline code/data structures/gates.
- Current work: reduce project bulk and align repository with strategic direction.
- Next work after restructure: weld-skill units and class-robot simulation route.
- Not completed: real welding quality validation, WPS/PQR, final simulator selection.

Keep the maintenance rule that future agents must check `details.md` when stage or scope changes.

- [ ] **Step 3: Update engine README**

Update `weld-experience-engine/README.md` so it starts with:

```markdown
# weldcore — 焊接技能资产引擎
```

Required points:

- Existing POC/MVP/report commands are still available.
- The core model is `SkillDataset -> WeldSkillPackage -> evaluation/evidence`.
- `simlite` is L0 stable simulation, not the final class-robot route.
- External simulators remain adapter candidates.

- [ ] **Step 4: Update strategy README if needed**

Open `docs/strategy/README.md`. If it still describes strategy docs only, add one sentence linking the strategy to the new architecture:

```markdown
当前项目级重构以“Physical AI 公司顶层战略与方向”为依据，把仓库默认主线收束到 `WeldSkillPackage` / 工业技能资产。
```

- [ ] **Step 5: Verify current-route references**

Run:

```bash
rg -n "docs/data-foundation|docs/specs/|docs/plans/|report/" README.md details.md weld-experience-engine/README.md docs/architecture docs/skill-assets docs/simulation docs/evidence docs/strategy || true
```

Expected:

- No stale references to `docs/data-foundation`.
- No current-route links to old `docs/specs` or `docs/plans`.
- If `report/` appears, it must be `docs/archive/whitepaper/report/`.

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md details.md weld-experience-engine/README.md docs/strategy/README.md
git commit -m "docs: align default entries to skill asset route"
```

Expected: commit succeeds.

---

## Task 5: Add Minimal Skill Asset Code Boundary

**Files:**
- Create: `weld-experience-engine/weldcore/skill_asset/__init__.py`
- Create: `weld-experience-engine/weldcore/skill_asset/package.py`
- Create: `weld-experience-engine/tests/test_skill_asset_facade.py`

- [ ] **Step 1: Write facade test**

Create `weld-experience-engine/tests/test_skill_asset_facade.py`:

```python
from weldcore.skill_asset import WeldSkillPackage, package_from_sample
from weldcore.transfer.package import package_from_sample as existing_package_from_sample
from weldcore.model.skill import WeldSkillPackage as ExistingWeldSkillPackage


def test_skill_asset_facade_reexports_existing_package_contract():
    assert WeldSkillPackage is ExistingWeldSkillPackage
    assert package_from_sample is existing_package_from_sample
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_skill_asset_facade.py
```

Expected: FAIL because `weldcore.skill_asset` does not exist.

- [ ] **Step 3: Create `weldcore.skill_asset` facade**

Create `weld-experience-engine/weldcore/skill_asset/package.py`:

```python
from __future__ import annotations

from ..model.skill import WeldSkillPackage
from ..transfer.package import package_from_sample

__all__ = ["WeldSkillPackage", "package_from_sample"]
```

Create `weld-experience-engine/weldcore/skill_asset/__init__.py`:

```python
from .package import WeldSkillPackage, package_from_sample

__all__ = ["WeldSkillPackage", "package_from_sample"]
```

- [ ] **Step 4: Run facade test**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_skill_asset_facade.py
```

Expected: PASS.

- [ ] **Step 5: Run focused skill tests**

Run:

```bash
cd weld-experience-engine
uv run pytest -q tests/test_skill_model.py tests/test_transfer_package.py tests/test_transfer_evaluate.py tests/test_skill_asset_facade.py
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

Run:

```bash
git add weld-experience-engine/weldcore/skill_asset weld-experience-engine/tests/test_skill_asset_facade.py
git commit -m "feat: add skill asset facade"
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

- [ ] **Step 2: Run required report commands**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.mvp_report
uv run python -m weldcore.report.data_foundation_report
uv run python -m weldcore.report.synthetic_v2_input_report
uv run python -m weldcore.report.simulation_ingest_report
```

Expected:

- All commands complete.
- `data_foundation_report`, `synthetic_v2_input_report`, and `simulation_ingest_report` write docs copies under `../docs/evidence/data-foundation/reports/`.

- [ ] **Step 3: Run historical report commands**

Run:

```bash
cd weld-experience-engine
uv run python -m weldcore.report.generate
uv run python -m weldcore.report.scenario_report
```

Expected: both commands complete. If either fails due to a pre-existing unrelated issue, document the failure and do not claim it passed.

- [ ] **Step 4: Verify no generated outputs are staged**

Run:

```bash
git status --short
```

Expected:

- Generated directories may be untracked.
- No `*_report_out/`, `__pycache__/`, `.pytest_cache/`, or generated runtime artifacts are staged.

- [ ] **Step 5: Audit stale current-route references**

Run:

```bash
rg -n "docs/data-foundation|docs/specs/|docs/plans/|\\breport/" README.md details.md weld-experience-engine/README.md docs/architecture docs/skill-assets docs/simulation docs/evidence docs/strategy || true
```

Expected:

- No stale `docs/data-foundation`.
- No stale `docs/specs/` or `docs/plans/`.
- Any `report/` reference points to `docs/archive/whitepaper/report/` or is in a historical context.

- [ ] **Step 6: Audit forbidden overclaims**

Run:

```bash
rg -n "真实焊接质量已经验证|替代 WPS|替代 PQR|完整 ManiSkill|完整 Isaac|熔池闭环已经完成" README.md details.md docs/architecture docs/skill-assets docs/simulation docs/evidence weld-experience-engine/README.md || true
```

Expected: no matches that make a forbidden claim.

- [ ] **Step 7: Commit fixes if verification required edits**

If Steps 1-6 require any fixes, make them with `apply_patch`, rerun the failing command, then commit:

```bash
git add <fixed files>
git commit -m "fix: complete skill asset restructure verification"
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
- Only expected untracked generated files remain.

- [ ] **Step 2: Prepare final implementation summary**

Summary must include:

- New default project framing.
- Major moved directories.
- New current-route docs.
- Code facade added.
- Tests and report commands run.
- Any remaining untracked runtime outputs.
- Clear statement that second stage is still future work: weld-skill units and class-robot simulation route research/access.

- [ ] **Step 3: Do not mark second stage complete**

This plan completes first-stage project restructure only. It does not complete simulator selection, weld-skill unit research, or simulator adapter implementation.
