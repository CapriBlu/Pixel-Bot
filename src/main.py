from screen_capture import capture_screen


def main():
    print("Pixel Bot avviato")

    path = capture_screen()

    print(f"Screenshot salvato in: {path}")


if __name__ == "__main__":
    main()
