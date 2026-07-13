from pixel_bot.core.command_parser import parse_command
from pixel_bot.core.executor import execute_action
from pixel_bot.core.safety import validate_action


def main() -> None:
    print("Pixel Bot v0.2")
    print("Console dell'assistente desktop")
    print("Scrivi 'esci' per terminare.")
    print()

    while True:
        command = input("Comando: ").strip()

        if command.lower() in {"esci", "exit", "quit"}:
            print("Pixel Bot terminato.")
            break

        try:
            actions = parse_command(command)

            print(f"Azioni generate: {len(actions)}")

            for action in actions:
                validate_action(action)
                print(f"- {action.name}: {action.parameters}")

            answer = input("Eseguire il piano? [s/N]: ").strip().lower()

            if answer not in {"s", "si", "sì", "y", "yes"}:
                print("Operazione annullata.")
                print()
                continue

            for index, action in enumerate(actions, start=1):
                print(
                    f"[{index}/{len(actions)}] "
                    f"Esecuzione: {action.name}"
                )

                result = execute_action(action)

                if result is not None:
                    print(f"Risultato: {result}")

            print("Piano completato.")

        except Exception as error:
            print(f"Errore: {error}")

        print()


if __name__ == "__main__":
    main()
