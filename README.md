# game-auto-test

游戏协议自动化测试框架。基于 **HTTP 登录 + WebSocket + Protobuf** 自研通信层，覆盖登录/背包/角色/邮件/商店/活动/任务等核心模块的 pytest 自动化用例，支持 CI 冒烟测试。

## 核心亮点

| 亮点 | 说明 |
|---|---|
| **自研协议通信层** | 复刻服务端 Go 源码的消息ID哈希算法，实现 `[4字节大端ID + Protobuf]` 二进制封包拆包 |
| **精准消息等待** | `recv_until` 跳过心跳/同步推送/S2C_ERROR，精确匹配期望响应ID，双保险防死循环（max_retry + total_timeout） |
| **四步模板封装** | BaseAPI 统一"构造→发送→收响应→解码"，业务API只填 Protobuf 字段，消除重复代码 |
| **fixture 登录复用** | session 级 fixture 一次登录，全部用例共享连接，冒烟测试从 8s 优化到 1.5s |
| **冒烟测试集合** | 一次登录串联 7 个核心模块，`pytest -m smoke` 一键跑，可直接接入 CI/CD |
| **硬断言覆盖** | 每个用例均有字段级断言（ID合法性、非空、时间校验、删除验证、购买前后对比） |

## 架构

```
game-auto-test/
├── config/              # 配置层：环境/账号/超时/配表加载
├── client/              # 通信层：HTTP登录、WebSocket连接、鉴权、心跳、通用收发
├── api/                 # 业务层：每个游戏模块一个API类，继承BaseAPI
├── proto/               # 协议层：Protobuf生成代码 + 封包拆包工具 + 消息ID对照表
├── tests/               # 用例层：pytest用例 + conftest fixture + 冒烟集合
├── utils/               # 工具层：配表加载器测试、时间控制器
├── reports/             # 运行日志（gitignore）
└── docs/                # 文档
```

**调用链**：`tests/` → `api/` → `client/` → 游戏服务器

## 通信模型

1. **HTTP 登录**：向登录服务器要 token + WebSocket 地址
2. **WS 连接**：连上游戏服务器，先消费服务器主动推的 `S2C_CONNECTED`
3. **鉴权**：发 `C2S_AUTH` 携带凭证，换登录态
4. **心跳保活**：后台守护线程定时发心跳，1秒粒度可及时退出
5. **业务请求**：`send_msg("C2S_xxx", protobuf)` → `recv_until(expect_id=...)` → 对应 `S2C_xxx` 类解析

**二进制协议**：每个消息包 = `[4字节大端消息ID] + [Protobuf序列化数据]`，消息ID由消息名哈希算出（算法复刻自服务端 Go 源码）。

## 环境要求

- Python 3.10+
- 依赖见 `requirements.txt`
- 可访问游戏测试服（地址/账号在 `config/settings.py` 配置）

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 跑全部用例
pytest

# 只跑冒烟用例（CI推荐）
pytest -m smoke

# 跑冒烟集合（一次登录串7个模块）
pytest tests/test_smoke.py -v

# 跑单个模块
pytest tests/test_bag.py -v

# 只收集不执行（验证导入）
pytest --collect-only -q
```

## 用例清单

### 冒烟用例（`pytest -m smoke`）

| 模块 | 用例 | 断言点 |
|---|---|---|
| 登录 | `test_login` | cuid非空、ws连接建立 |
| 背包 | `test_query_backpack` | 背包非空、道具数量合法 |
| 角色 | `test_query_role_info` | ID>0、名字非空、等级/VIP合法 |
| 邮件 | `test_query_mail` | 邮件ID>0、标题非空、创建时间合法 |
| 商店 | `test_query_shop` | 商品列表非空 |
| 活动 | `test_query_activity` | 活动ID>0、开始时间<结束时间 |
| 任务 | `test_query_task` | 任务类型匹配、任务ID>0、进度>=0 |
| 冒烟集合 | `test_smoke_all` | 一次登录串联以上7个模块 |

### 操作类用例（单独跑，不进冒烟）

| 模块 | 用例 | 断言点 |
|---|---|---|
| 商店 | `test_buy_gift` | 购买返回 code=0 |
| 商店 | `test_buy_and_check_backpack` | 购买前后背包对比，道具到账 |
| 邮件 | `test_get_attachments` | 领取后 is_item_got=True |
| 邮件 | `test_delete_mail` | 删除后邮件不在剩余列表 |

## 配置

环境/账号/超时/消息ID常量集中在 `config/settings.py`，换环境只改这一个文件。

| 配置项 | 说明 |
|---|---|
| `LOGIN_URL` | HTTP 登录地址 |
| `ACCOUNT_GENERAL` | 通用测试账号 |
| `DEFAULT_SERVER_ID` | 默认服务器ID |
| `WS_TIMEOUT` | WebSocket 单帧超时（秒） |
| `HEARTBEAT_INTERVAL` | 心跳间隔（秒） |
| `RECV_MAX_RETRY` | recv_until 最大接收帧数（防推送风暴） |
| `RECV_TOTAL_TIMEOUT` | recv_until 总等待上限（秒） |

## 技术栈

- **语言**：Python 3.10+
- **测试框架**：pytest
- **通信**：requests（HTTP）+ websocket-client（WebSocket）
- **序列化**：Protobuf（grpc_tools 生成）
- **CI/CD**：支持 GitHub Actions（`pytest -m smoke`）
