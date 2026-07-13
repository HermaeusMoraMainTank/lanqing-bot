# -*- coding: utf-8 -*-
"""蓝晴-bot 日志（参考 NcatBot BoundLogger）。"""
from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Optional

from bot.config import ROOT_DIR

_LOG_DIR = ROOT_DIR / "logs"
_INITIALIZED = False
_DEBUG_MODE = False
_MANAGED_LOGGERS: set[str] = set()

_CONSOLE_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_FILE_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class BoundLogger:
    """支持 bind 上下文的 logger 包装器。"""

    __slots__ = ("_logger", "_context")

    def __init__(self, logger: logging.Logger, context: dict[str, Any] | None = None):
        self._logger = logger
        self._context = context or {}

    def bind(self, **kwargs: Any) -> BoundLogger:
        return BoundLogger(self._logger, {**self._context, **kwargs})

    def debug(self, msg: str, *args, **kwargs):
        self._log(logging.DEBUG, msg, args, kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._log(logging.INFO, msg, args, kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._log(logging.WARNING, msg, args, kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._log(logging.ERROR, msg, args, kwargs)

    def exception(self, msg: str, *args, **kwargs):
        kwargs.setdefault("exc_info", True)
        self._log(logging.ERROR, msg, args, kwargs)

    def _log(self, level: int, msg: str, args: tuple, kwargs: dict):
        if not self._logger.isEnabledFor(level):
            return
        if self._context:
            prefix = " ".join(f"{k}={v}" for k, v in self._context.items() if v not in (None, ""))
            if prefix:
                msg = f"{prefix} | {msg}"
        kwargs.setdefault("stacklevel", 3)
        self._logger.log(level, msg, *args, **kwargs)


def get_log(name: str | None = "lanqing") -> BoundLogger:
    logger = logging.getLogger(name or "lanqing")
    if name:
        logger.setLevel(logging.DEBUG if _DEBUG_MODE else logging.INFO)
        _MANAGED_LOGGERS.add(name)
    return BoundLogger(logger)


def setup_logging(*, debug: bool | None = None) -> None:
    """初始化蓝晴日志（写入 logs/bot.log + 控制台）。"""
    global _INITIALIZED, _DEBUG_MODE
    if _INITIALIZED:
        return
    _INITIALIZED = True

    if debug is None:
        debug = "-d" in sys.argv or "--debug" in sys.argv
    _DEBUG_MODE = debug

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if debug else logging.INFO

    console_formatter = logging.Formatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT)
    file_formatter = logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT)

    root = logging.getLogger("lanqing")
    root.setLevel(level)
    root.propagate = False
    root.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    root.addHandler(console_handler)

    file_handler = TimedRotatingFileHandler(
        _LOG_DIR / "bot.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    root.addHandler(file_handler)

    for child in ("handler", "plugin", "client", "media"):
        logging.getLogger(f"lanqing.{child}").setLevel(level)

    get_log().info(
        "日志已初始化 debug=%s log_file=%s",
        debug,
        _LOG_DIR / "bot.log",
    )
