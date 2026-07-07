# -*- coding: utf-8 -*-
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply
from bot.utils.group_track import get_group_tracker


class BasicPlugin(BasePlugin):
    name = "basic"
    version = "1.0.0"
    description = "基础指令：帮助、ping、问候"
    triggers = ["帮助", "ping", "你好", "hello"]

    _HELP = (
        "可用指令：\n"
        "· 帮助 — 显示本消息\n"
        "· ping — 测试连通性\n"
        "· 今日人品 / jrrp — 查看今日人品\n"
        "· 占卜 — 抽取塔罗牌\n"
        "· 今日小猪 / 抽小猪 / 小猪图鉴 — 今日小猪\n"
        "· 轮盘赌 / 午时已到 — 俄罗斯轮盘赌\n"
        "· 今日老婆 / 群老婆列表 — 群友老婆\n"
        "· 今日二次元老婆 — 二次元老婆\n"
        "· 菲比搜索 <关键词> — 搜索菲比梗图\n"
        "· 今日运势 / 运势 / 今日doro — 运势\n"
        "· 打卡 / 上班 / 下班 / 群上班列表 — 上下班\n"
        "· 设置昵称 <名字> — 设置本群显示昵称\n"
        "· 你好 / hello — 打招呼\n"
        "\n"
        "群聊请 @机器人 或使用 / 指令面板（会自动 @）"
    )

    _COMMANDS = {
        "帮助": _HELP,
        "ping": "pong！",
        "你好": "你好呀～",
        "hello": "Hello!",
    }

    def match(self, text: str) -> bool:
        cmd = text.strip()
        if cmd.startswith("设置昵称"):
            return True
        return super().match(text)

    def on_message(self, ctx: MessageContext) -> PluginReply:
        cmd = ctx.text.strip()
        if cmd.startswith("设置昵称"):
            nick = cmd[len("设置昵称") :].strip()
            if not nick:
                return "用法：@机器人 设置昵称 你的昵称\n（官方 Bot 不提供群名片，需自行设置）"
            get_group_tracker().set_nickname(ctx.group_openid, ctx.user_key, nick)
            return f"已设置本群昵称为：{nick}"
        key = ctx.text.strip().lower() if ctx.text.strip().isascii() else ctx.text.strip()
        for trigger, reply in self._COMMANDS.items():
            if trigger.isascii():
                if key == trigger.lower():
                    return reply
            elif ctx.text.strip() == trigger:
                return reply
        return None
