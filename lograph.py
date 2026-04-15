"""Entry point for LoGraph CLI and GUI commands.

This script routes user commands to config initialization, one-shot runs,
continuous monitoring, or the desktop control GUI.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from lograph_tool.cli import run_monitor, run_once
from lograph_tool.config import is_setup_completed, write_default_config
from lograph_tool.gui import launch_gui
from lograph_tool.reset import reset_generated_data
from lograph_tool.setup import run_setup_wizard_cli


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LoGraph deploy-and-use command")
    parser.add_argument("command", choices=["init", "setup", "run", "monitor", "reset", "gui"], help="Command")
    parser.add_argument("--config", default="lograph-tool.json", help="Config file path")
    parser.add_argument("--model", default="models/lograph_tool_model.json", help="Model output file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    model_path = Path(args.model).resolve()

    if args.command == "init":
        write_default_config(config_path)
        print(f"Config ready at {config_path}")
        return

    if args.command == "setup":
        run_setup_wizard_cli(config_path, model_path, start_command="run")
        return

    if args.command == "reset":
        summary = reset_generated_data(config_path.parent, model_path)
        print("Reset completed")
        print(f"- deleted files: {summary['deleted_count']}")
        if summary["errors"]:
            print("- errors:")
            for item in summary["errors"]:
                print(f"  - {item}")
        return

    if not config_path.exists():
        run_setup_wizard_cli(config_path, model_path, start_command=args.command)
        return

    if args.command in {"run", "monitor"} and not is_setup_completed(config_path):
        run_setup_wizard_cli(config_path, model_path, start_command=args.command)
        return

    if args.command == "run":
        run_once(config_path, model_path)
        return

    if args.command == "monitor":
        run_monitor(config_path, model_path)
        return

    launch_gui(config_path, model_path)


if __name__ == "__main__":
    main()
