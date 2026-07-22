from pixel_bot.developer.autonomous_loop import AutonomousVerificationLoop
from pixel_bot.developer.autonomous_planner import AutonomousPlanner
from pixel_bot.developer.checklist_engine import Checklist
from pixel_bot.developer.task_memory import PersistentTaskMemory


def test_loop_completes_all_steps(tmp_path):
    checklist = Checklist.from_text("1. Analizza\n2. Verifica")
    loop = AutonomousVerificationLoop(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "task.json"),
        executor=lambda step: {"step": step.id},
        verifier=lambda step, output: (output["step"] == step.id, "ok"),
    )
    result = loop.run("task-1", "goal", checklist)
    assert result.status == "completed"
    assert result.completed_steps == 2
    assert checklist.is_complete


def test_loop_stops_on_failed_verification(tmp_path):
    checklist = Checklist.from_text("1. Analizza")
    loop = AutonomousVerificationLoop(
        planner=AutonomousPlanner(),
        memory=PersistentTaskMemory(tmp_path / "task.json"),
        executor=lambda step: None,
        verifier=lambda step, output: (False, "manca evidenza"),
    )
    result = loop.run("task-1", "goal", checklist)
    assert result.status == "failed"
    assert "evidenza" in result.reason
