"""Provides tasks for making subprocess calls."""

import asyncio

from typing import Any, Optional

from canopy.tree import Node, Status


class CmdTask(Node):
    """Run a subprocess to completion."""

    def __init__(self, cmd: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.cmd = cmd

    async def update(self, user_data: dict) -> Optional[Status]:
        """Run a subprocess until completion."""
        user_data["cmd"] = self.cmd
        proc = await asyncio.create_subprocess_shell(
            self.cmd,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        user_data["stdout"] = stdout
        user_data["stderr"] = stderr

        assert proc.returncode is not None
        if proc.returncode < 0:
            return Status.FAILED
        return Status.SUCCESS
