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

## 测试群快速上手（推荐先看这里）

以下流程适用于在 **QQ 沙箱群** 里调试，参考 [官方接入文档](https://bot.q.qq.com/wiki/develop/api-v2/#%E8%B4%A6%E5%8F%B7%E6%B3%A8%E5%86%8C) 与 [botpy 群聊示例](https://github.com/tencent-connect/botpy/blob/master/examples/demo_group_reply_text.py)。

### 第一步：开放平台配置

1. 登录 [QQ 开放平台](https://q.qq.com/) → 进入你的机器人 → **开发设置**
2. 复制 **AppID**、**AppSecret**（Token 已废弃，不要用 Token）
3. 进入 **沙箱配置** → **QQ 群配置**：
   - 选择你的测试群（需为群主/管理员，成员 ≤ 20 人）
   - 建议群名含「测试」便于区分
4. 确认已订阅 **群事件**（`GROUP_AT_MESSAGE_CREATE`，即群内 @ 机器人消息）

> botpy 默认走 **WebSocket** 长连接，本地电脑即可运行，**不需要** 公网服务器或回调地址。

### 第二步：本地配置

```powershell
cd 蓝晴-bot
copy config\config.example.yaml config\config.yaml
```

编辑 `config/config.yaml`，至少填好凭证，群聊测试建议只开 group：

```yaml
appid: "你的AppID"
secret: "你的AppSecret"

scenes:
  guild: false   # 暂不测频道可关
  group: true    # 群聊必开
  c2c: false     # 暂不测单聊可关
```

### 第三步：安装并启动

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

看到 `机器人「xxx」已上线` 即表示 WebSocket 连接成功。

### 第四步：把机器人拉进测试群

在 **手机 QQ** 打开沙箱测试群：

**设置 → 群机器人 → 添加测试机器人**

（或在开放平台扫描群机器人二维码，分享到测试群后添加）

### 第五步：在群里发消息测试

在群内 **@机器人** 并发送指令（必须 @，否则不会触发）：

| 你发送的内容 | 机器人回复 |
|-------------|-----------|
| `@机器人 帮助` | 显示可用指令列表 |
| `@机器人 ping` | `pong！` |
| `@机器人 你好` | `你好呀～` |
| `@机器人 随便说点什么` | 默认欢迎语 |

控制台会打印 `[群聊] xxx: ping` 等日志，便于排查。

### 常见问题

| 现象 | 可能原因 |
|------|---------|
| 启动报错找不到 config.yaml | 未复制配置文件 |
| 上线了但 @ 没反应 | 机器人未加入沙箱群；或未订阅群事件；或未 @ 机器人 |
| 鉴权失败 | AppID / AppSecret 填错 |
| 群列表里找不到机器人 | 沙箱群未配置好，或你不是群主/管理员 |

## 项目结构

```
蓝晴-bot/
├── main.py
├── plugins/                # 功能插件（自动加载）
│   ├── basic/              # 帮助、ping
│   ├── jrrp/               # 今日人品
│   ├── tarot/              # 占卜
│   └── _template/          # 新插件模板
├── bot/
│   ├── client.py           # 主 Client
│   ├── plugin/             # 插件基类与注册器
│   └── handlers/           # 消息分发入口
└── config/
    └── config.example.yaml
```

开发规范见 `.cursor/skills/lanqing-bot-dev/SKILL.md`。

## 扩展开发

### 新增插件

1. 复制 `plugins/_template/` 为新目录
2. 实现 `plugin.py`（继承 `BasePlugin`）
3. 填写 `manifest.yaml` 和 **`platform.yaml`**（官网配置文档）
4. 重启机器人

每个插件的 `platform.yaml` 说明该功能在 QQ 开放平台需要填写的指令、服务和事件。

## 参考文档

- [QQ 机器人官方文档 — 启动接入](https://bot.q.qq.com/wiki/develop/api-v2/#%E8%B4%A6%E5%8F%B7%E6%B3%A8%E5%86%8C)
- [botpy GitHub 仓库](https://github.com/tencent-connect/botpy)

## License

MIT
