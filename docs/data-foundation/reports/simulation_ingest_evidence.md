# Simulation Ingest Evidence Report

## Run Summary

- simulation_run_id: `run-input-panel-butt-001-7-1`
- bundle_id: `simlite-input-panel-butt-001-7-1`
- input_id: `input-panel-butt-001`
- taxonomy_ref: `panel-butt`
- sample_count: `1`
- dataset_id: `simlite-input-panel-butt-001-7-1-dataset`
- evidence_binding_count: 27
- assumption_field_count: 14
- real_validation_field_count: 6
- can_extract_skill_package: True

## Bundle Summary

- bundle schema_version: `synthetic-v2-bundle-v0.1`
- bundle source_type: `simulation`
- simulator: `simlite`
- simulator_version: `0.1`
- adapter_version: `0.1`
- generation_boundary: No qualified WPS claim., No real production quality conclusion., Groove geometry remains a synthetic planning placeholder., not WPS/PQR, not real welding quality validation

## Sample Summary

- samples: 1
- trajectory points: 5
- process signal points: 5

| sample_id | trajectory points | process signal points | quality observation |
| --- | --- | --- | --- |
| sample-001 | 5 | 5 | yes |

## Input Spec Alignment

| field | value |
| --- | --- |
| bundle_input_id | `input-panel-butt-001` |
| dataset_source_type | `simulation` |
| dataset_schema_version | `synthetic-v2-dataset-v0.1` |
| bundle_schema_version | `synthetic-v2-bundle-v0.1` |
| sample_count_matches | `True` |
| bundle_is_importable | `True` |

## Evidence Binding Summary

| field_path | source_id | evidence_role | value_status | notes |
| --- | --- | --- | --- | --- |
| procedure_fields.welding_process | guide-miller-gmaw | public_process_reference | assumed | Generic GMAW process reference. |
| procedure_fields.joint_type | vendor-kobelco-shipbuilding-welding | public_process_reference | constrained | Shipbuilding joint vocabulary. |
| procedure_fields.weld_position | vendor-kobelco-shipbuilding-welding | public_process_reference | constrained | Flat position vocabulary. |
| procedure_fields.weld_object | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | constrained | Panel line object. |
| procedure_fields.manufacturing_stage | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | constrained | Panel line stage. |
| procedure_fields.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Placeholder thickness. |
| procedure_fields.groove_geometry | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Groove placeholder. |
| procedure_fields.current | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| procedure_fields.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| procedure_fields.travel_speed | guide-lincoln-electric-gmaw | public_process_reference | assumed | Generic travel speed field reference. |
| procedure_fields.trajectory | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | constrained | Panel path structure. |
| procedure_fields.torch_angle | standard-aws-swps-public-page | public_process_reference | assumed | Procedure variable placeholder. |
| procedure_fields.quality_label | dataset-zenodo-metal-arc-welding-10017718 | public_dataset_schema | requires_real_validation_later | Schema reference only. |
| procedure_fields.defect_label | guide-twi-weld-defects | public_process_reference | requires_real_validation_later | Defect vocabulary placeholder only, not real quality validation. |
| procedure_fields.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Standards index boundary. |
| geometry_spec.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Project placeholder. |
| geometry_spec.groove_geometry | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Groove placeholder. |
| geometry_spec.weld_length_mm | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Segment placeholder. |
| motion_spec.motion_template | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | constrained | Panel motion template. |
| motion_spec.trajectory | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | constrained | Straight panel path. |
| motion_spec.torch_angle | standard-aws-swps-public-page | public_process_reference | assumed | Posture placeholder. |
| process_spec.current | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| process_spec.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| process_spec.travel_speed | guide-lincoln-electric-gmaw | public_process_reference | assumed | Public process placeholder. |
| quality_spec.quality_label | dataset-zenodo-metal-arc-welding-10017718 | public_dataset_schema | requires_real_validation_later | Schema reference only. |
| quality_spec.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Validation boundary. |
| quality_spec.defect_label | dataset-gdxray-weld-xray | public_dataset_schema | requires_real_validation_later | Vocabulary only. |

## Assumption Fields

| field_path | source_id | evidence_role | value_status | notes |
| --- | --- | --- | --- | --- |
| procedure_fields.welding_process | guide-miller-gmaw | public_process_reference | assumed | Generic GMAW process reference. |
| procedure_fields.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Placeholder thickness. |
| procedure_fields.groove_geometry | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Groove placeholder. |
| procedure_fields.current | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| procedure_fields.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public WPS variable placeholder. |
| procedure_fields.travel_speed | guide-lincoln-electric-gmaw | public_process_reference | assumed | Generic travel speed field reference. |
| procedure_fields.torch_angle | standard-aws-swps-public-page | public_process_reference | assumed | Procedure variable placeholder. |
| geometry_spec.plate_thickness_mm | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Project placeholder. |
| geometry_spec.groove_geometry | project-260522-shipbuilding-welding-brain-plan | project_internal | assumed | Groove placeholder. |
| geometry_spec.weld_length_mm | vendor-kranendonk-panel-welding-gantry | shipbuilding_case | assumed | Segment placeholder. |
| motion_spec.torch_angle | standard-aws-swps-public-page | public_process_reference | assumed | Posture placeholder. |
| process_spec.current | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| process_spec.voltage | standard-aws-swps-public-page | public_process_reference | assumed | Public process placeholder. |
| process_spec.travel_speed | guide-lincoln-electric-gmaw | public_process_reference | assumed | Public process placeholder. |

## Real-Validation Fields

| field_path | source_id | evidence_role | value_status | notes |
| --- | --- | --- | --- | --- |
| procedure_fields.quality_label | dataset-zenodo-metal-arc-welding-10017718 | public_dataset_schema | requires_real_validation_later | Schema reference only. |
| procedure_fields.defect_label | guide-twi-weld-defects | public_process_reference | requires_real_validation_later | Defect vocabulary placeholder only, not real quality validation. |
| procedure_fields.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Standards index boundary. |
| quality_spec.quality_label | dataset-zenodo-metal-arc-welding-10017718 | public_dataset_schema | requires_real_validation_later | Schema reference only. |
| quality_spec.inspection_reference | standard-aws-standards-index | public_process_reference | requires_real_validation_later | Validation boundary. |
| quality_spec.defect_label | dataset-gdxray-weld-xray | public_dataset_schema | requires_real_validation_later | Vocabulary only. |

## Warnings And Errors

- warnings: 0
- errors: 0

## Skill Package Readiness

- `SimulationOutputBundle` 已经可以走通导入与抽取链路，说明平台可以接住仿真输出的结构化结果。
- 不是 WPS/PQR，也不证明真实焊接质量。
- 外部仿真器仍然只是可选 adapter；当前报告使用 simlite/mock bundle 验证平台接入能力。
- 前期调研资料继续作为后续焊接知识嵌入底座。
- 目前结论是：平台具备把仿真样本收进 skill package 的基础接口，后续再接真实来源做补强。
