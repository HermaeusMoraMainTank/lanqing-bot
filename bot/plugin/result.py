# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

PluginReply = Union[str, "PluginResult", None]


@dataclass
class PluginResult:
    """插件回复：文字 + 可选本地图片（支持多图顺序发送）。"""

    text: str
    image_path: Optional[Path] = None
    image_paths: list[Path] = field(default_factory=list)
