from action_executor import execute_action
from logger import get_logger
from task_loader import load_task


logger = get_logger(__name__)


def run_task(task_path: str) -> None:
    actions = load_task(task_path)

    print(f"Task caricato: {len(actions)} azioni")

    for index, action in enumerate(actions, start=1):
        print(f"[{index}/{len(actions)}] {action.name}")

        try:
            result = execute_action(action)

            if result is not None:
                print(f"Risultato: {result}")

        except Exception as error:
            logger.exception(
                "Errore durante l'azione numero %s: %s",
                index,
                error,
            )

            print(f"Task interrotto: {error}")
            return

    print("Task completato correttamente.")


if __name__ == "__main__":
    run_task("tasks/demo_task.json")
