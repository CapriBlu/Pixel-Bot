from pixel_bot.developer.autonomous_planner import AutonomousPlanner


def test_builds_sequential_dependencies():
    planner = AutonomousPlanner()
    steps = planner.build("goal", ["analizza", "modifica", "verifica"])
    assert steps[0].depends_on == ()
    assert steps[1].depends_on == (1,)
    assert steps[2].depends_on == (2,)


def test_next_ready_respects_dependencies():
    planner = AutonomousPlanner()
    steps = planner.build("goal", ["uno", "due"])
    assert planner.next_ready(steps).id == 1
    steps[0].status = "completed"
    assert planner.next_ready(steps).id == 2
