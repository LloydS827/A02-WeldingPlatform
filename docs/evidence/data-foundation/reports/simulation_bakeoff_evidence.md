# WeldSkillUnit Simulation Bake-off Evidence

## Summary

- task_count: 2
- evidence_bundle_count: 6
- final_simulator_selected: False
- recommendation: `continue_with_r0_baseline_and_prepare_external_dependency_spikes`
- rerun_replay_status: `skipped`

本报告用于记录 WeldSkillUnit 最小仿真 bake-off 证据；当前结论不是最终仿真器选择。
外部仿真器失败被记录为 failure boundary，不作为默认工作流错误。

## WeldSkillUnit Tasks

| task_id | unit_id | name |
| --- | --- | --- |
| `task-long-straight-horizontal-tracking` | `long-straight-horizontal-tracking` | 长直横焊沿缝跟踪 |
| `task-corner-horizontal-transition` | `corner-horizontal-transition` | 包角横焊转角过渡 |

## Route Summary

| route | task_count | completed | failed | score | failure_boundaries |
| --- | ---: | ---: | ---: | ---: | --- |
| R0 / simlite reference | 2 | 2 | 0 | 0.82 | none |
| ManiSkill/SAPIEN | 2 | 0 | 2 | 0.435 | mani_skill_or_sapien_not_available, optional_dependency_missing |
| Gazebo/MoveIt | 2 | 0 | 2 | 0.435 | optional_dependency_missing, rclpy_moveit_or_moveit_configs_utils_not_available |

## Scorecard

| route | digital_asset_writeback | robot_executability | skill_unit_expression | engineering_access_cost | weighted_score |
| --- | ---: | ---: | ---: | ---: | ---: |
| R0 / simlite reference | 1.0 | 0.4 | 1.0 | 1.0 | 0.82 |
| ManiSkill/SAPIEN | 0.35 | 0.25 | 1.0 | 0.25 | 0.435 |
| Gazebo/MoveIt | 0.35 | 0.25 | 1.0 | 0.25 | 0.435 |

## Rerun Replay

- attempted: True
- Rerun replay status: `skipped`
- rerun_replay_status: `skipped`
- dataset_id: `dataset-simlite_reference-task-long-straight-horizontal-tracking`
- bundle_id: `evidence-simlite_reference-task-long-straight-horizontal-tracking`
- uri: `None`
- skip_reason: `rerun_sdk_unavailable_or_logging_skipped`

## Evidence Boundaries

- 不是最终仿真器选择。
- 不证明真实焊接质量。
- 不替代 WPS/PQR。
- R0/simlite reference 只提供平台内可复现基线。
- ManiSkill/SAPIEN 与 Gazebo/MoveIt 的外部依赖失败记录为 failure boundary，不破坏默认报告命令。
