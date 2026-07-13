from action_executor import execute_action
from command_parser import parse_command
from safety import validate_action


def main() -> None:
    print("Pixel Bot - Console comandi")
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

            answer = input("Eseguire? [s/N]: ").strip().lower()

            if answer not in {"s", "si", "sì", "y", "yes"}:
                print("Operazione annullata.")
                continue

            for action in actions:
                result = execute_action(action)

                if result is not None:
                    print(f"Risultato: {result}")

            print("Operazione completata.")

        except Exception as error:
            print(f"Errore: {error}")

        print()


if __name__ == "__main__":
    main()
