import subprocess
import time

from keyboard_controller import press_key, write_text


def main() -> None:
    print("Apertura di Blocco note tra 2 secondi...")
    time.sleep(2)

    subprocess.Popen(["notepad.exe"])
    time.sleep(2)

    write_text("Pixel Bot sta controllando la tastiera.")
    press_key("enter")
    write_text("Primo test completato con successo.")

    print("Test della tastiera completato.")


if __name__ == "__main__":
    main()
