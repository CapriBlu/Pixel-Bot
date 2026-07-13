from action_executor import execute_action
from safety import Action


def main() -> None:
    print("Avvio test dell'esecutore sicuro.")

    screenshot = execute_action(
        Action(
            name="screenshot",
            parameters={},
        )
    )

    print(f"Screenshot creato: {screenshot}")

    execute_action(
        Action(
            name="wait",
            parameters={"seconds": 1},
        )
    )

    print("Test completato.")
    print("Controlla il file logs\\pixel_bot.log")


if __name__ == "__main__":
    main()
