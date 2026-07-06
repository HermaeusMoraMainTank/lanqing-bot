# -*- coding: utf-8 -*-
from bot.config import load_config
from bot.plugin.base import BasePlugin, MessageContext
from bot.plugin.result import PluginReply
from bot.utils.hash_util import current_day_str, daily_hash_value


def calculate_jrrp(user_key: str) -> int:
    digest_input = user_key
    return daily_hash_value(digest_input, current_day_str()) % 101


def format_jrrp(display_name: str, luck_value: int) -> str:
    prefix = f"{display_name} 的今日人品是：{luck_value}。"
    if luck_value == 0:
        return prefix + "怎，怎么会这样……"
    if 0 < luck_value <= 20:
        return prefix + "推荐闷头睡大觉。"
    if 20 < luck_value <= 40:
        return prefix + "也许今天适合摆烂。"
    if 40 < luck_value <= 60 and luck_value != 42:
        return prefix + "又是平凡的一天。"
    if 60 < luck_value <= 80 and luck_value != 77:
        return prefix + "太阳当空照，花儿对你笑。"
    if 80 < luck_value < 100:
        return prefix + f"出门可能捡到{luck_value}块钱。"
    if luck_value == 42:
        return prefix + "感觉可以参透宇宙的真理。"
    if luck_value == 77:
        return prefix + "要不要去抽一发卡试试呢……"
    if luck_value == 100:
        return prefix + "买彩票可能会中大奖哦！"
    return prefix + "又是平凡的一天。"


class JrrpPlugin(BasePlugin):
    name = "jrrp"
    version = "1.1.0"
    description = "今日人品（NcatBot 同款）"
    triggers = ["jrrp", "今日人品"]

    def match(self, text: str) -> bool:
        cmd = text.strip()
        return cmd.lower() == "jrrp" or cmd == "今日人品"

    def on_message(self, ctx: MessageContext) -> PluginReply:
        config = load_config()
        vip_openids = set(config.get("jrrp_vip_openids", []))
        if ctx.user_key in vip_openids:
            return f"{ctx.display_name} 的今日人品是：101。"
        value = calculate_jrrp(ctx.user_key)
        return format_jrrp(ctx.display_name, value)
