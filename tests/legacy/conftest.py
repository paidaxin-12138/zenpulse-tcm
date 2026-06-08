import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "/legacy/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(
                pytest.mark.skip(
                    reason="Legacy manual scripts; use tests/unit and tests/integration."
                )
            )
