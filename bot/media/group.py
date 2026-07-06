# -*- coding: utf-8 -*-
import base64
from pathlib import Path
from typing import Any

from botpy import logging
from botpy.http import Route
from botpy.message import C2CMessage, GroupMessage

_log = logging.get_logger()


def _clean_payload(**fields: Any) -> dict:
    return {k: v for k, v in fields.items() if v is not None}


async def upload_group_image(api, group_openid: str, image_path: Path) -> dict:
    file_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    route = Route("POST", "/v2/groups/{group_openid}/files", group_openid=group_openid)
    result = await api._http.request(route, json={"file_type": 1, "file_data": file_data})
    if not isinstance(result, dict) or not result.get("file_info"):
        raise RuntimeError(f"群图片上传失败: {result}")
    return result


async def upload_c2c_image(api, openid: str, image_path: Path) -> dict:
    file_data = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    route = Route("POST", "/v2/users/{openid}/files", openid=openid)
    result = await api._http.request(route, json={"file_type": 1, "file_data": file_data})
    if not isinstance(result, dict) or not result.get("file_info"):
        raise RuntimeError(f"单聊图片上传失败: {result}")
    return result


async def reply_with_image(message, text: str, image_path: Path) -> None:
    """单条消息同时带文字与图片（群聊 content 必填）。"""
    api = message._api
    path = Path(image_path)
    if not path.exists():
        await message.reply(content=text)
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
                msg_seq=1,
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
                msg_seq=1,
            ),
        )
        return

    await message.reply(content=text, file_image=str(path))
