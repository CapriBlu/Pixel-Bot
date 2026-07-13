import time

from mouse_controller import get_mouse_position


def main():
    print("Muovi il mouse. Premi CTRL+C per interrompere.")

    for _ in range(10):
        position = get_mouse_position()
        print(f"Mouse: x={position.x}, y={position.y}")
        time.sleep(1)


if __name__ == "__main__":
    main()
