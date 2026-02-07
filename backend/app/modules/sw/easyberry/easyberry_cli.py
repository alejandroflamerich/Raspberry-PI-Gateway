"""Simple CLI to run EasyberryConnector

Usage:
  python easyberry_cli.py --config ../../../../easyberry_config.json --once
  python easyberry_cli.py --config ../../../../easyberry_config.json --loop
"""
import argparse
import logging

from .connector import run_once, run_loop
from .store import database


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true")
    group.add_argument("--loop", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.once:
        run_once(args.config, database)
    else:
        try:
            run_loop(args.config, database)
        except KeyboardInterrupt:
            print("Interrupted")


if __name__ == "__main__":
    main()
