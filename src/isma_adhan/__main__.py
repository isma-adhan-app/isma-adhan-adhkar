"""Entry point: python -m isma_adhan [--minimized] [--self-test]"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    from . import bootstrap

    bootstrap.init()  # first: every later crash must leave a trace in app.log

    parser = argparse.ArgumentParser(prog="isma_adhan")
    parser.add_argument(
        "--minimized",
        action="store_true",
        help="start hidden in the system tray (used by Windows autostart)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run a headless self-test of all subsystems and exit",
    )
    args = parser.parse_args()

    if args.self_test:
        from .selftest import run_self_test

        return run_self_test()

    try:
        from .app import run
    except ImportError as exc:
        print(f"Missing dependency: {exc}")
        print("Install requirements first:  pip install -r requirements.txt")
        return 1
    return run(minimized=args.minimized)


if __name__ == "__main__":
    sys.exit(main())
