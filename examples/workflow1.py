import asyncio
import json

from canopy.tree import Parallel
from canopy.tasklib.cmd import CmdTask


async def main() -> None:
    r = Parallel(
        children=[
            CmdTask("black ."),
            CmdTask("flake8 ."),
            CmdTask("pytest ."),
        ]
    )

    bb: dict = {}
    await r.tick(bb)
    print(json.dumps(bb, default=str, indent=2))


asyncio.run(main())
