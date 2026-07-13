import argparse

from pixel_bot.core.executor import execute_action
from pixel_bot.core.logger import get_logger
from pixel_bot.core.task_loader import load_task


logger = get_logger(__name__)


def run_task(
    task_path: str,
    dry_run: bool = False,
    confirm: bool = True,
) -> None:
    actions = load_task(task_path)

    print(f"Task caricato: {len(actions)} azioni")

    for index, action in enumerate(actions, start=1):
        print(
            f"[{index}/{len(actions)}] "
            f"{action.name} {action.parameters}"
        )

        if dry_run:
            print("  Anteprima: azione non eseguita.")
            continue

        if confirm:
            answer = input("  Eseguire? [s/N]: ").strip().lower()

            if answer not in {"s", "si", "sì", "y", "yes"}:
                print("  Azione saltata.")
                continue

        try:
            result = execute_action(action)

            if result is not None:
                print(f"  Risultato: {result}")

        except Exception as error:
            logger.exception(
                "Errore durante l'azione numero %s: %s",
                index,
                error,
            )

            print(f"Task interrotto: {error}")
            return

    print("Task terminato.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Esegue un task del Pixel Bot."
    )

    parser.add_argument(
        "task",
        nargs="?",
        default="tasks/demo_task.json",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    parser.add_argument(
        "--no-confirm",
        action="store_true",
    )

    args = parser.parse_args()

    run_task(
        task_path=args.task,
        dry_run=args.dry_run,
        confirm=not args.no_confirm,
    )


if __name__ == "__main__":
    main()
