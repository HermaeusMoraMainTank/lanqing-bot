# -*- coding: utf-8 -*-
"""蓝晴-bot 启动入口。"""
from bot.client import LanqingBot
from bot.config import build_intents, load_config
from bot.utils.botpy_patch import patch_group_message_author


def main() -> None:
    patch_group_message_author()
    config = load_config()
    intents = build_intents(config)
    client = LanqingBot(intents=intents)
    client.run(appid=config["appid"], secret=config["secret"])


if __name__ == "__main__":
    main()
