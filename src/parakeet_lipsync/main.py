"""Entry point for Parakeet Lipsync application."""

from parakeet_lipsync.app import ParakeetApp


def main():
    """Run the Parakeet Lipsync application."""
    app = ParakeetApp()
    app.run()


if __name__ == "__main__":
    main()
