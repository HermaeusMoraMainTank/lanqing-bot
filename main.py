# -*- coding: utf-8 -*-
"""蓝晴-bot 启动入口。"""
import sys

from bot.client import LanqingBot
from bot.config import build_intents, load_config
from bot.utils.botpy_patch import patch_group_message_author
from bot.utils.logger import setup_logging


def main() -> None:
    setup_logging(debug="-d" in sys.argv or "--debug" in sys.argv)
    patch_group_message_author()
    config = load_config()
    intents = build_intents(config)
    client = LanqingBot(intents=intents)
    client.run(appid=config["appid"], secret=config["secret"])


if __name__ == "__main__":
    main()
