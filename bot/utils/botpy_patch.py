# -*- coding: utf-8 -*-
"""补全 botpy 未解析的群消息 author 字段。"""
from botpy.message import GroupMessage


def patch_group_message_author() -> None:
    """官方群消息 author 含 member_role，botpy 默认只读 member_openid。"""

    class _GroupAuthor:
        __slots__ = ("member_openid", "member_role", "bot")

        def __init__(self, data: dict):
            self.member_openid = data.get("member_openid")
            self.member_role = data.get("member_role")
            self.bot = data.get("bot")

        def __repr__(self) -> str:
            return str(
                {
                    "member_openid": self.member_openid,
                    "member_role": self.member_role,
                    "bot": self.bot,
                }
            )

    GroupMessage._User = _GroupAuthor
