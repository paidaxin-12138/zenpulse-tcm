# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""应用入口 — 兼容旧启动方式: python web_server.py"""

import os

from tcm_ai.api.app import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("TCM_HOST", "0.0.0.0")
    port = int(os.getenv("TCM_PORT", "8000"))
    uvicorn.run("web_server:app", host=host, port=port, reload=False)
