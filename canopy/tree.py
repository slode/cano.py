"""
A simple async behavior tree implementation.

In contrast to synchronous implementations, a task tick() is only executed
once.

This greatly simplifies the implementation, and allows the implementation to
combine the standard start->update->end logic into a single invocation of
update().
"""

import asyncio
import enum
import logging

from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class Status(enum.Enum):
    """Enum indicating a task exit state."""

    SUCCESS = True
    FAILED = False


class Node:
    """Base class for a task in the tree."""

    def __init__(
        self, name: Optional[str] = None, **kwargs: Any
    ):  # pylint: disable=unused-argument
        """Create a Node object."""
        self.uuid = uuid4().hex
        self.name = name or self.__class__.__name__

    async def tick(self, blackboard: dict) -> Status:  # pylint: disable: invalid-name
        """Run a task to completion."""
        node_data = blackboard.setdefault(self.uuid, {})
        node_data["node"] = str(self)
        user_data = node_data.setdefault("data", {})

        try:
            node_status = await self.update(user_data) or Status.SUCCESS
        except Exception:  # pylint: disable=broad-except
            logger.exception("%s update failed!", self)
            node_status = Status.FAILED

        node_data["status"] = node_status
        return node_status

    async def update(self, user_data: dict) -> Optional[Status]:  # pylint: disable=unused-argument
        """Contains the task domain logic."""
        raise NotImplementedError()

    def __repr__(self) -> str:
        """Return a textual representation of the Node"""
        return f"{self.name}:{self.uuid[:9]}"


class Composite(Node):
    """Provides an interface for nodes that affect execution behavor."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.children = kwargs["children"] if "children" in kwargs else []

    def add(self, *nodes: Node) -> None:
        """Add children to the composite Node."""
        self.children.extend(nodes)

    async def update(self, user_data: dict) -> Optional[Status]:  # pylint: disable=unused-argument
        """Contains the composite node flow implementation."""
        raise NotImplementedError()


class Sequence(Composite):
    """Runs each child in sequence until failure."""

    async def update(self, user_data: dict) -> Optional[Status]:
        for child in self.children:
            status = await child.tick(user_data)
            if status == Status.FAILED:
                return Status.FAILED
        return Status.SUCCESS


class Selector(Composite):
    """Runs each child in sequence until success."""

    async def update(self, user_data: dict) -> Optional[Status]:
        for child in self.children:
            status = await child.tick(user_data)

            if status == Status.SUCCESS:
                return Status.SUCCESS

        return Status.FAILED


class Parallel(Composite):
    """Runs all children until failure."""

    async def _raise_on_failure(self, child: Node, user_data: dict) -> Optional[Status]:
        if (status := await child.tick(user_data)) == Status.FAILED:
            raise Exception(child)
        return status

    async def update(self, user_data: dict) -> Optional[Status]:

        try:
            await asyncio.wait(
                {self._raise_on_failure(child, user_data) for child in self.children},
                return_when=asyncio.FIRST_EXCEPTION,
            )
        except Exception:  # pylint: disable=broad-except
            return Status.FAILED

        return Status.SUCCESS


class Repeater(Parallel):
    """Runs child tasks in parallel, and retries if any tasks fail."""

    def __init__(self, *args: Any, count: int = 1, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.count = count

    async def update(self, user_data: dict) -> Optional[Status]:
        for _ in range(self.count):
            status = await super().update(user_data)
            if status == Status.SUCCESS:
                return Status.SUCCESS
        return Status.FAILED


class Succeeder(Node):
    """Always returns success."""

    async def update(self, user_data: dict) -> Optional[Status]:
        return Status.SUCCESS


class Failer(Node):
    """Always returns failure."""

    async def update(self, user_data: dict) -> Optional[Status]:
        return Status.FAILED
