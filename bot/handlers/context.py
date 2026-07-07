# -*- coding: utf-8 -*-
import re

from bot.utils.group_track import get_group_tracker
from bot.utils.text import normalize_command
from bot.plugin.base import MessageContext, Scene
from botpy.message import C2CMessage, GroupMessage, Message

_MENTION_RE = re.compile(r"<@!?([^>]+)>")


def from_guild_message(client, message: Message) -> MessageContext:
    text = normalize_command(message.content or "")
    return MessageContext(
        text=text,
        raw_text=message.content or "",
        user_key=message.author.id or "unknown",
        display_name=message.author.username or "你",
        scene="guild",
        client=client,
        message=message,
    )


def _extract_mentions(content: str) -> list[str]:
    return _MENTION_RE.findall(content or "")


def from_group_message(client, message: GroupMessage) -> MessageContext:
    raw = message.content or ""
    text = normalize_command(raw)
    author = message.author
    openid = getattr(author, "member_openid", None) or "unknown"
    role = getattr(author, "member_role", None)
    group_openid = message.group_openid or ""
    mentions = _extract_mentions(raw)
    tracker = get_group_tracker()
    tracker.record(group_openid, openid, member_role=role)
    display = tracker.display_name(group_openid, openid)
    return MessageContext(
        text=text,
        raw_text=raw,
        user_key=openid,
        display_name=display,
        scene="group",
        client=client,
        message=message,
        group_openid=group_openid,
        mentioned_openids=mentions,
    )


def from_c2c_message(client, message: C2CMessage) -> MessageContext:
    text = normalize_command(message.content or "")
    return MessageContext(
        text=text,
        raw_text=message.content or "",
        user_key=message.author.user_openid or "unknown",
        display_name="你",
        scene="c2c",
        client=client,
        message=message,
    )
