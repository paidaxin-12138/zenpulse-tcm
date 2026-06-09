# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

from tcm_ai.api.app import create_app


def test_create_app_registers_pulse_and_pages():
    app = create_app()
    paths = {getattr(route, "path", None) for route in app.routes}
    assert "/api/pulse/analyze" in paths
    assert "/api/vitals/analyze" in paths
    assert any(path and path.startswith("/") for path in paths)
