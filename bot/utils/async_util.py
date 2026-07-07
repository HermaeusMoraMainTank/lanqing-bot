# -*- coding: utf-8 -*-
"""将阻塞调用丢到默认线程池，避免卡住 botpy 事件循环。"""
from __future__ import annotations

import asyncio
from typing import Callable, TypeVar

T = TypeVar("T")


async def run_sync(func: Callable[..., T], /, *args, **kwargs) -> T:
    return await asyncio.to_thread(func, *args, **kwargs)
