"""Legacy entry point preserved for compatibility.

This module simply forwards execution to the new application bootstrapper
located at ``app/main.py`` so that existing workflows that expect to run
``python aractakip.py`` continue to work after the architecture overhaul.
"""

from app.main import main


def run() -> None:
    """Launch the application via the shared ``main`` function."""

    main()


if __name__ == "__main__":
    run()
