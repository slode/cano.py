"""Provides a command line interface for running pre-defined tasks."""
import argparse
import asyncio
import json
import pathlib

from canopy.parser import create_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Run process pipeline tasks")
    parser.add_argument("task", type=pathlib.Path, help="Create and run a task from file")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Dump task definition and blackboard",
    )
    args = parser.parse_args()

    with open(args.task) as f:
        task_definition = json.load(f)
        if args.verbose:
            print(json.dumps(task_definition, default=str, indent=2))

    job = create_job(task_definition)

    bb: dict = {}
    status = asyncio.run(job.tick(bb))
    if args.verbose:
        print(json.dumps(bb, default=str, indent=2))

    return 0 if status.value else 1


if __name__ == "__main__":
    exit(main())
