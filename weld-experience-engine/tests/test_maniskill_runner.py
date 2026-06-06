import sys
import types

from weldcore.simulation_bakeoff import (
    default_maniskill_task_configs,
    generate_rule_based_demo,
    run_maniskill_lightweight,
)
from weldcore.simulation_bakeoff.maniskill_runner import _run_backend


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


def test_runner_treats_sapien_without_maniskill_as_missing_backend(monkeypatch):
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)

    def fake_find_spec(module_name):
        if module_name in {"gymnasium", "sapien"}:
            return object()
        return None

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner.importlib.util.find_spec",
        fake_find_spec,
    )

    artifact = run_maniskill_lightweight(config, demo)

    assert artifact.failure_boundary == ("environment_missing",)


def test_runner_maps_backend_import_errors_to_environment_missing(monkeypatch):
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._maniskill_backend_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner._run_backend",
        lambda config, demo: (_ for _ in ()).throw(ImportError("missing")),
    )

    artifact = run_maniskill_lightweight(config, demo)

    assert artifact.failure_boundary == ("environment_missing",)


def test_runner_treats_bad_backend_specs_as_environment_missing(monkeypatch):
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)

    def bad_find_spec(module_name):
        raise ValueError("bad spec")

    monkeypatch.setattr(
        "weldcore.simulation_bakeoff.maniskill_runner.importlib.util.find_spec",
        bad_find_spec,
    )

    artifact = run_maniskill_lightweight(config, demo)

    assert artifact.failure_boundary == ("environment_missing",)


def test_runner_uses_mocked_backend_for_contract_success(monkeypatch):
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


def test_backend_probe_uses_headless_empty_env(monkeypatch):
    config = default_maniskill_task_configs()[0]
    demo = generate_rule_based_demo(config)
    calls = []

    class FakeActionSpace:
        def sample(self):
            return "sample-action"

    class FakeEnv:
        action_space = FakeActionSpace()

        def reset(self, seed):
            return {}, {"seed": seed}

        def step(self, action):
            return {}, 0.0, False, False, {"action": action}

        def close(self):
            calls.append(("close",))

    fake_gym = types.ModuleType("gymnasium")

    def fake_make(env_id, **kwargs):
        calls.append(("make", env_id, kwargs))
        return FakeEnv()

    fake_gym.make = fake_make
    fake_mani_skill = types.ModuleType("mani_skill")
    fake_mani_skill_envs = types.ModuleType("mani_skill.envs")
    fake_mani_skill.envs = fake_mani_skill_envs
    monkeypatch.setitem(sys.modules, "gymnasium", fake_gym)
    monkeypatch.setitem(sys.modules, "mani_skill", fake_mani_skill)
    monkeypatch.setitem(sys.modules, "mani_skill.envs", fake_mani_skill_envs)

    result = _run_backend(config, demo)

    assert calls[0] == (
        "make",
        "Empty-v1",
        {
            "obs_mode": "state",
            "render_mode": None,
            "render_backend": "none",
        },
    )
    assert calls[-1] == ("close",)
    assert result["task_state"]["backend_probe"] == "mani_skill_gymnasium_empty_reset_step"


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
