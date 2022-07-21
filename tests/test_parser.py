"""Parser tests."""

from canopy.parser import create_job


async def test_create_job() -> None:
    """Test parser.create_job()."""
    create_job({"task": "Sequence", "args": {}})
