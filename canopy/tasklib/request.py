"""Provides tasks for making HTTP calls"""

from contextvars import ContextVar
from typing import Any, Optional

import aiohttp

from canopy.tree import Node, Parallel, Status

session_var: ContextVar[Optional[aiohttp.ClientSession]] = ContextVar(
    "aiohttp-client-session", default=None
)


class HttpSessionTask(Parallel):
    """Sets up a persistent aiohttp session."""

    async def update(self, user_data: dict) -> Optional[Status]:
        session_handle = session_var.set(aiohttp.ClientSession())

        try:
            await super().update(user_data)
        finally:
            aiohttp_session = session_var.get()
            if aiohttp_session is not None:
                await aiohttp_session.close()

            if session_handle is not None:
                session_var.reset(session_handle)
        return Status.SUCCESS


class RequestTask(Node):
    """Makes a aiohttp get request."""

    def __init__(self, url: str, **kwargs: Any):
        super().__init__(**kwargs)
        self.url = url

    async def update(self, user_data: dict) -> Optional[Status]:
        aiohttp_session = session_var.get()
        if aiohttp_session is not None:
            user_data["output"] = await aiohttp_session.get(self.url)
        return Status.SUCCESS
