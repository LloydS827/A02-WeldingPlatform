# SyntheticSkillDataset v2 输入证据报告

## Summary

- 本报告把通过 Task 3 manifest/loader 门禁的 synthetic v2 输入整理为可审计报告。
- 这些输入用于 SyntheticSkillDataset v2 首批生成前设计，不是 WPS/PQR。
- 本报告不证明真实焊接质量，不替代真实工艺评定、船厂实测数据或设备控制程序确认。

- 任务分类总数：7
- ready 任务族：3
- 工艺字段总数：15
- 必填工艺字段：14
- 首批仿真输入：3
- 证据绑定总数：81

## Task Taxonomy

| family_id | readiness | joint_type | weld_position | motion_structure | notes |
| --- | --- | --- | --- | --- | --- |
| stiffened-panel-fillet | ready_for_synthetic_v2_plan | fillet | flat_or_horizontal | long_linear_seam_with_repeatable_torch_posture | Strong public shipbuilding automation sources cover panel welding context, trajectory, travel speed, and torch angle; process and quality values remain bounded assumptions. |
| panel-butt | ready_for_synthetic_v2_plan | butt | flat | long_straight_seam_with_low_pose_complexity | Public procedure references and panel automation sources support a constrained first-batch input; groove and process values are placeholders requiring project review. |
| micro-panel-web-bulkhead | ready_for_synthetic_v2_plan | fillet | flat_horizontal_or_limited_vertical | many_short_linear_segments_with_repositioning | Autonomous welding robot public case material supports small-panel task structure and motion template boundaries; real validation remains out of scope. |
| double-bottom-inner-fillet | needs_more_sources | fillet | mixed | linear_segments_with_access_constraints | Shipbuilding application sources indicate relevance, but internal access, fixture, and validated motion constraints need additional public or project sources before first-batch planning. |
| vertical-overhead-hull-weld | defer | butt_or_fillet | vertical_or_overhead | position_dependent_motion_with_high_posture_sensitivity | Deferred because public sources do not yet support safe synthetic assumptions for vertical or overhead hull welding motion and validation boundaries. |
| thick-plate-groove-multipass | defer | groove_butt | flat_horizontal_or_mixed | pass_sequence_dependent_motion | Deferred until pass sequencing, inter-pass assumptions, and procedure qualification boundaries are sourced beyond generic public references. |
| curved-spatial-complex-weld | defer | curved_butt_or_fillet | spatially_varying | three_dimensional_curve_with_pose_replanning | Deferred because current evidence supports task discovery only, not reliable synthetic motion or procedure input generation for complex spatial geometry. |

## First-Batch Inputs

| input_id | taxonomy_ref | procedure fields | evidence bindings | boundaries |
| --- | --- | --- | --- | --- |
| input-stiffened-panel-fillet-001 | stiffened-panel-fillet | 15 | 27 | No real production quality conclusion.; No controller program reconstruction.; Process values are placeholders requiring project validation. |
| input-panel-butt-001 | panel-butt | 15 | 27 | No qualified WPS claim.; No real production quality conclusion.; Groove geometry remains a synthetic planning placeholder. |
| input-micro-panel-web-bulkhead-001 | micro-panel-web-bulkhead | 15 | 27 | No customer robot program reconstruction.; No real production quality conclusion.; Only top-level field bindings are represented in this manifest version. |

## Assumption Fields

| input_id | field_path | source_id | role | status | notes |
| --- | --- | --- | --- | --- | --- |
| input-stiffened-panel-fillet-001 | procedure_fields.welding_process | guide-lincoln-electric-gmaw | public_process_reference | assumed | Process family placeholder only. |
| input-stiffened-panel-fillet-001 | procedure_fields.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Placeholder thickness range. |
| input-stiffened-panel-fillet-001 | procedure_fields.current | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| input-stiffened-panel-fillet-001 | procedure_fields.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| input-stiffened-panel-fillet-001 | procedure_fields.travel_speed | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Public automation field coverage. |
| input-stiffened-panel-fillet-001 | procedure_fields.torch_angle | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Torch posture field coverage. |
| input-stiffened-panel-fillet-001 | geometry_spec.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Project placeholder. |
| input-stiffened-panel-fillet-001 | geometry_spec.weld_length_mm | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Segment length placeholder. |
| input-stiffened-panel-fillet-001 | motion_spec.torch_angle | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Posture placeholder. |
| input-stiffened-panel-fillet-001 | process_spec.current | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| input-stiffened-panel-fillet-001 | process_spec.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| input-stiffened-panel-fillet-001 | process_spec.travel_speed | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Public field coverage only. |
| input-panel-butt-001 | procedure_fields.welding_process | guide-miller-gmaw | public_process_reference | assumed | Generic GMAW process reference. |
| input-panel-butt-001 | procedure_fields.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Placeholder thickness. |
| input-panel-butt-001 | procedure_fields.groove_geometry | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Groove placeholder. |
| input-panel-butt-001 | procedure_fields.current | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| input-panel-butt-001 | procedure_fields.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| input-panel-butt-001 | procedure_fields.travel_speed | guide-lincoln-electric-gmaw | public_process_reference | assumed | Generic travel speed field reference. |
| input-panel-butt-001 | procedure_fields.torch_angle | standard-aws-swps-public-page | public_process_reference | assumed | Procedure variable placeholder. |
| input-panel-butt-001 | geometry_spec.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Project placeholder. |
| input-panel-butt-001 | geometry_spec.groove_geometry | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Groove placeholder. |
| input-panel-butt-001 | geometry_spec.weld_length_mm | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Segment placeholder. |
| input-panel-butt-001 | motion_spec.torch_angle | standard-aws-swps-public-page | public_process_reference | assumed | Posture placeholder. |
| input-panel-butt-001 | process_spec.current | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| input-panel-butt-001 | process_spec.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| input-panel-butt-001 | process_spec.travel_speed | guide-lincoln-electric-gmaw | public_process_reference | assumed | Public process placeholder. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.welding_process | vendor-hyundai-welding-cobot-shipbuilding-2024 | shipbuilding_case | assumed | Shipbuilding cobot context. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.weld_position | vendor-kobelco-shipbuilding-welding | public_process_reference | assumed | Position vocabulary. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Placeholder thickness. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.current | dataset-zenodo-tandem-gmaw-17951725 | public_dataset_schema | assumed | Schema reference placeholder. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.voltage | dataset-zenodo-tandem-gmaw-17951725 | public_dataset_schema | assumed | Schema reference placeholder. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.travel_speed | dataset-zenodo-tandem-gmaw-17951725 | public_dataset_schema | assumed | Schema reference placeholder. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.torch_angle | vendor-hyundai-welding-cobot-shipbuilding-2024 | shipbuilding_case | assumed | Cobot posture placeholder. |
| input-micro-panel-web-bulkhead-001 | geometry_spec.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Project placeholder. |
| input-micro-panel-web-bulkhead-001 | geometry_spec.segment_count | case-siemens-hd-hyundai-mipo-autonomous-welding | shipbuilding_case | assumed | Repeated short-seam placeholder. |
| input-micro-panel-web-bulkhead-001 | motion_spec.torch_angle | vendor-hyundai-welding-cobot-shipbuilding-2024 | shipbuilding_case | assumed | Cobot posture placeholder. |
| input-micro-panel-web-bulkhead-001 | process_spec.current | dataset-zenodo-tandem-gmaw-17951725 | public_dataset_schema | assumed | Schema reference placeholder. |
| input-micro-panel-web-bulkhead-001 | process_spec.voltage | dataset-zenodo-tandem-gmaw-17951725 | public_dataset_schema | assumed | Schema reference placeholder. |
| input-micro-panel-web-bulkhead-001 | process_spec.travel_speed | dataset-zenodo-tandem-gmaw-17951725 | public_dataset_schema | assumed | Schema reference placeholder. |

## Real-Validation Fields

| input_id | field_path | source_id | role | status | notes |
| --- | --- | --- | --- | --- | --- |
| input-stiffened-panel-fillet-001 | procedure_fields.quality_label | dataset-gdxray-weld-xray | public_dataset_schema | requires_real_validation_later | Vocabulary only; no real quality conclusion. |
| input-stiffened-panel-fillet-001 | procedure_fields.defect_label | guide-twi-weld-defects | public_process_reference | requires_real_validation_later | Defect vocabulary placeholder only, not real quality validation. |
| input-stiffened-panel-fillet-001 | procedure_fields.inspection_reference | standard-aws-swps-public-page | public_process_reference | requires_real_validation_later | Inspection reference placeholder. |
| input-stiffened-panel-fillet-001 | quality_spec.quality_label | dataset-gdxray-weld-xray | public_dataset_schema | requires_real_validation_later | Public label vocabulary only. |
| input-stiffened-panel-fillet-001 | quality_spec.inspection_reference | standard-aws-swps-public-page | public_process_reference | requires_real_validation_later | Placeholder inspection reference. |
| input-stiffened-panel-fillet-001 | quality_spec.defect_label | dataset-gdxray-weld-xray | public_dataset_schema | requires_real_validation_later | Public defect vocabulary only. |
| input-panel-butt-001 | procedure_fields.quality_label | dataset-zenodo-metal-arc-welding-10017718 | public_dataset_schema | requires_real_validation_later | Schema reference only. |
| input-panel-butt-001 | procedure_fields.defect_label | guide-twi-weld-defects | public_process_reference | requires_real_validation_later | Defect vocabulary placeholder only, not real quality validation. |
| input-panel-butt-001 | procedure_fields.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Standards index boundary. |
| input-panel-butt-001 | quality_spec.quality_label | dataset-zenodo-metal-arc-welding-10017718 | public_dataset_schema | requires_real_validation_later | Schema reference only. |
| input-panel-butt-001 | quality_spec.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Validation boundary. |
| input-panel-butt-001 | quality_spec.defect_label | dataset-gdxray-weld-xray | public_dataset_schema | requires_real_validation_later | Vocabulary only. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.quality_label | dataset-riawelc-weld-image | public_dataset_schema | requires_real_validation_later | Public label vocabulary only. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.defect_label | dataset-riawelc-weld-image | public_dataset_schema | requires_real_validation_later | Defect vocabulary placeholder only, not real quality validation. |
| input-micro-panel-web-bulkhead-001 | procedure_fields.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Inspection boundary. |
| input-micro-panel-web-bulkhead-001 | quality_spec.quality_label | dataset-riawelc-weld-image | public_dataset_schema | requires_real_validation_later | Public label vocabulary only. |
| input-micro-panel-web-bulkhead-001 | quality_spec.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Validation boundary. |
| input-micro-panel-web-bulkhead-001 | quality_spec.defect_label | dataset-riawelc-weld-image | public_dataset_schema | requires_real_validation_later | Public defect vocabulary only. |

## 边界说明

- 不是 WPS/PQR：本报告只给出 synthetic v2 输入证据绑定和字段边界。
- 不证明真实焊接质量：quality/inspection/defect 字段只是标签 schema 或待验证占位。
- 不重建客户机器人程序、控制器程序或真实生产参数。
- SyntheticSkillDataset v2 后续样本必须保留 assumption 与 requires_real_validation_later 标记。
