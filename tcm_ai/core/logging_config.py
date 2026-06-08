"""应用日志配置（结构化输出到 stdout，供 journal / Docker 采集）。"""

from __future__ import annotations

import logging
import sys

from tcm_ai.core.runtime import is_production


def configure_logging() -> None:
    level = logging.INFO if is_production() else logging.DEBUG
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO if is_production() else logging.DEBUG)
