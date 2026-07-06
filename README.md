# 蓝晴-bot

基于 [QQ 机器人开放平台](https://bot.q.qq.com/wiki/develop/api-v2/) 与官方 Python SDK [botpy](https://github.com/tencent-connect/botpy) 搭建的 QQ 机器人框架。

支持 **频道**、**群聊**、**单聊** 三种场景，可按配置开关。

## 准备工作

1. 前往 [QQ 开放平台](https://q.qq.com/) 注册开发者账号并创建机器人
2. 在「开发设置」获取 **AppID** 与 **AppSecret**（Token 鉴权已废弃，请使用 AppSecret）
3. 在开放平台订阅所需事件（频道 @ 消息、群 @ 消息、C2C 消息等）

## 快速开始

### 1. 安装依赖

```bash
cd 蓝晴-bot
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 2. 配置凭证

```bash
copy config\config.example.yaml config\config.yaml
```

编辑 `config/config.yaml`，填入 AppID、AppSecret，并按需调整 `scenes` 开关。

### 3. 启动机器人

```bash
python main.py
```

启动成功后，控制台会输出 `机器人「xxx」已上线`。

## 项目结构

```
蓝晴-bot/
├── main.py                 # 启动入口
├── bot/
│   ├── client.py           # 主 Client，注册事件回调
│   ├── config.py           # 配置加载与 Intents 构建
│   ├── handlers/           # 各场景消息处理器
│   │   ├── guild.py        # 频道 @ 消息
│   │   ├── group.py        # 群 @ 消息
│   │   └── c2c.py          # 单聊消息
│   └── commands/
│       └── basic.py        # 基础指令（帮助 / ping / 你好）
└── config/
    └── config.example.yaml
```

## 扩展开发

### 添加新指令

在 `bot/commands/basic.py` 的 `COMMANDS` 字典中增加键值对即可：

```python
COMMANDS = {
    "天气": "请发送城市名…",
    # ...
}
```

### 添加新事件

1. 在 `bot/client.py` 的 `LanqingBot` 中实现对应 `on_*` 方法
2. 在 `bot/handlers/` 下新建处理器模块
3. 在 `bot/config.py` 的 `build_intents` 中开启相应 Intents

可参考 [botpy examples](https://github.com/tencent-connect/botpy/tree/master/examples) 中的完整示例。

## 参考文档

- [QQ 机器人官方文档 — 启动接入](https://bot.q.qq.com/wiki/develop/api-v2/#%E8%B4%A6%E5%8F%B7%E6%B3%A8%E5%86%8C)
- [botpy GitHub 仓库](https://github.com/tencent-connect/botpy)

## License

MIT
