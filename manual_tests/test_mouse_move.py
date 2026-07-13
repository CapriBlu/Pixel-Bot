import time

from mouse_controller import get_mouse_position, move_mouse


def main():
    start_position = get_mouse_position()

    print(f"Posizione iniziale: {start_position}")
    print("Il mouse si muoverà tra 3 secondi.")

    time.sleep(3)

    move_mouse(100, 100)

    print("Movimento completato.")
    print("Sposta il mouse nell'angolo in alto a sinistra per arresto di emergenza.")


if __name__ == "__main__":
    main()
