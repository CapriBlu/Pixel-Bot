import pytest

from pixel_bot.core.planner import Planner


def test_create_single_step_plan():
    planner = Planner()

    plan = planner.create_plan("screenshot")

    assert plan.goal == "screenshot"
    assert plan.status == "ready"
    assert len(plan.steps) == 1
    assert plan.steps[0].id == 1
    assert plan.steps[0].action == "screenshot"
    assert plan.steps[0].parameters == {}
    assert plan.steps[0].status == "pending"


def test_create_multiple_step_plan():
    planner = Planner()

    plan = planner.create_plan(
        "apri blocco note; aspetta 2 secondi; scrivi Ciao"
    )

    assert [step.action for step in plan.steps] == [
        "open_app",
        "wait",
        "write_text",
    ]

    assert [step.id for step in plan.steps] == [1, 2, 3]


def test_convert_plan_to_actions():
    planner = Planner()
    plan = planner.create_plan("aspetta 1 secondo")

    actions = planner.plan_to_actions(plan)

    assert len(actions) == 1
    assert actions[0].name == "wait"
    assert actions[0].parameters == {"seconds": 1.0}


def test_reject_empty_goal():
    planner = Planner()

    with pytest.raises(ValueError):
        planner.create_plan("   ")


def test_plan_to_dict():
    planner = Planner()
    plan = planner.create_plan("screenshot")

    data = plan.to_dict()

    assert data["goal"] == "screenshot"
    assert data["status"] == "ready"
    assert data["steps"][0]["action"] == "screenshot"