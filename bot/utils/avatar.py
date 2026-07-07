# -*- coding: utf-8 -*-
"""
QQ 官方 Bot 用户头像（未公开文档的隐藏接口）。

URL 格式::
    https://thirdqq.qlogo.cn/qqapp/{appid}/{openid}/0

- ``appid``：机器人 AppID（config.yaml 中的 appid）
- ``openid``：用户 openid（群聊为 member_openid，单聊为 user_openid）
- 末尾 ``/0``：尺寸参数（实测可用）

限制：仅适用于**用户**头像，无法获取**群**头像。
"""
from __future__ import annotations

import io
import logging
from pathlib import Path

import requests
from PIL import Image as PILImage, ImageDraw

from bot.config import ROOT_DIR, load_config
from bot.utils.pil_helpers import load_font, placeholder_avatar

_log = logging.getLogger(__name__)

AVATAR_URL_TEMPLATE = "https://thirdqq.qlogo.cn/qqapp/{appid}/{openid}/0"
CACHE_DIR = ROOT_DIR / "data" / "avatar_cache"
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; LanqingBot/1.0)",
})


def avatar_url(openid: str, appid: str | None = None) -> str:
    if not appid:
        appid = str(load_config().get("appid", ""))
    return AVATAR_URL_TEMPLATE.format(appid=appid, openid=openid)


def _cache_path(openid: str) -> Path:
    safe = openid.replace("/", "_").replace("\\", "_")
    return CACHE_DIR / f"{safe}.jpg"


def download_avatar(openid: str, *, appid: str | None = None, force: bool = False) -> Path | None:
    """下载用户头像到本地缓存，成功返回路径。"""
    if not openid:
        return None
    path = _cache_path(openid)
    if path.exists() and not force:
        return path
    url = avatar_url(openid, appid)
    try:
        resp = _SESSION.get(url, timeout=15)
        resp.raise_for_status()
        if not resp.content or len(resp.content) < 128:
            return None
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(resp.content)
        return path
    except requests.RequestException as exc:
        _log.debug("头像下载失败 %s: %s", openid[:8], exc)
        return None


def _circle_mask(size: int) -> PILImage.Image:
    mask = PILImage.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def load_avatar(openid: str, size: int = 48, *, circular: bool = True) -> PILImage.Image:
    """
    加载用户头像为 PIL 图；失败时降级为 placeholder_avatar。
    circular=True 时返回带透明底的圆形 RGBA。
    """
    path = download_avatar(openid)
    if path and path.exists():
        try:
            raw = PILImage.open(path).convert("RGB").resize((size, size), PILImage.Resampling.LANCZOS)
            if not circular:
                return raw
            out = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
            out.paste(raw, (0, 0), _circle_mask(size))
            return out
        except OSError as exc:
            _log.debug("头像读取失败 %s: %s", openid[:8], exc)
    return placeholder_avatar(openid, size)


def load_avatar_bytes(openid: str, size: int = 48) -> bytes:
    img = load_avatar(openid, size, circular=False)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()
