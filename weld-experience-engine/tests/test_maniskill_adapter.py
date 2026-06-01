from weldcore.sim.adapters.maniskill import ManiSkillAdapterSpec


def test_maniskill_adapter_is_non_runtime_boundary():
    spec = ManiSkillAdapterSpec()

    assert spec.name == "maniskill"
    assert spec.required_dependency == "mani_skill"
    assert "demonstration" in spec.mvp_role
    assert spec.runtime_required is False
    assert "optional" in spec.explain_boundary()
