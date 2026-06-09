# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if "/legacy/" in str(item.fspath).replace("\\", "/"):
            item.add_marker(
                pytest.mark.skip(
                    reason="Legacy manual scripts; use tests/unit and tests/integration."
                )
            )
