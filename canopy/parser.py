"""Creates a task tree from a json definition"""

import importlib

from typing import Any, Type

from canopy.tree import Node


def locate_task(task_name: str, prefix: str = "canopy.tasklib.") -> Type[Node]:
    """Locate a Task class definition based on a module pattern string."""
    mod_name, class_name = (prefix + task_name).rsplit(".", 1)
    mod = importlib.__import__(mod_name, fromlist=[class_name])
    class_type = getattr(mod, class_name)
    return class_type


def create_task(task: str, args: dict[str, Any]) -> Node:
    """Create a new task, recursively instantiation any children."""
    if "children" in args:
        args["children"] = [
            create_task(task["task"], task["args"]) for task in args.get("children", [])
        ]
    task_class = locate_task(task)
    return task_class(**args)


def create_job(task_definition: dict[str, Any]) -> Node:
    """Create a new tree of tasks based on a json definition."""
    return create_task("Sequence", {"children": [task_definition]})
