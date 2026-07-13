# -*- coding: utf-8 -*-
import base64
from pathlib import Path
from typing import Any

from botpy.http import Route
from botpy.message import C2CMessage, GroupMessage

from bot.utils.async_util import run_sync
from bot.utils.logger import get_log

_log = get_log("lanqing.media")


def _clean_payload(**fields: Any) -> dict:
    return {k: v for k, v in fields.items() if v is not None}


async def upload_group_image(api, group_openid: str, image_path: Path) -> dict:
    raw = await run_sync(image_path.read_bytes)
    file_data = base64.b64encode(raw).decode("utf-8")
    route = Route("POST", "/v2/groups/{group_openid}/files", group_openid=group_openid)
    try:
        result = await api._http.request(route, json={"file_type": 1, "file_data": file_data})
    except Exception:
        _log.exception("群图片上传失败 group=%s file=%s", group_openid, image_path.name)
        raise
    if not isinstance(result, dict) or not result.get("file_info"):
        _log.error("群图片上传返回异常 group=%s result=%r", group_openid, result)
        raise RuntimeError(f"群图片上传失败: {result}")
    _log.debug("群图片上传成功 group=%s file=%s", group_openid, image_path.name)
    return result


async def upload_c2c_image(api, openid: str, image_path: Path) -> dict:
    raw = await run_sync(image_path.read_bytes)
    file_data = base64.b64encode(raw).decode("utf-8")
    route = Route("POST", "/v2/users/{openid}/files", openid=openid)
    try:
        result = await api._http.request(route, json={"file_type": 1, "file_data": file_data})
    except Exception:
        _log.exception("单聊图片上传失败 user=%s file=%s", openid, image_path.name)
        raise
    if not isinstance(result, dict) or not result.get("file_info"):
        _log.error("单聊图片上传返回异常 user=%s result=%r", openid, result)
        raise RuntimeError(f"单聊图片上传失败: {result}")
    return result


async def reply_with_image(message, text: str, image_path: Path, *, msg_seq: int = 1) -> None:
    """单条消息同时带文字与图片（群聊 content 必填）。"""
    api = message._api
    path = Path(image_path)
    if not path.exists():
        await message.reply(content=text, msg_seq=msg_seq)
        return

    if isinstance(message, GroupMessage):
        media = await upload_group_image(api, message.group_openid, path)
        route = Route(
            "POST", "/v2/groups/{group_openid}/messages", group_openid=message.group_openid
        )
        await api._http.request(
            route,
            json=_clean_payload(
                content=text,
                msg_type=7,
                media={"file_info": media["file_info"]},
                msg_id=message.id,
                msg_seq=msg_seq,
            ),
        )
        return

    if isinstance(message, C2CMessage):
        openid = message.author.user_openid
        media = await upload_c2c_image(api, openid, path)
        route = Route("POST", "/v2/users/{openid}/messages", openid=openid)
        await api._http.request(
            route,
            json=_clean_payload(
                content=text,
                msg_type=7,
                media={"file_info": media["file_info"]},
                msg_id=message.id,
                msg_seq=msg_seq,
            ),
        )
        return

    await message.reply(content=text, file_image=str(path), msg_seq=msg_seq)
