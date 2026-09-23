# game-auto-test

游戏协议自动化测试框架。基于 **HTTP 登录 + WebSocket + Protobuf**，封装游戏客户端通信层，覆盖核心业务模块的 pytest 用例。

## 架构

```
game-auto-test/
├── config/              # 配置层：环境、账号、超时、配表加载
├── client/              # 通信层：HTTP登录、WebSocket连接、鉴权、心跳、通用收发
├── api/                 # 业务层：每个游戏模块一个文件，填protobuf字段
├── proto/               # 协议层：.proto定义 + 自动生成的_pb2.py + 封包拆包工具
├── tests/               # 用例层：pytest用例 + 断言
├── reports/             # 失败现场/运行日志（gitignore）
└── docs/                # 问题分析文档
```

**通信模型**：
1. HTTP 登录拿 token 和 WebSocket 地址
2. WebSocket 连接，服务器先推 S2C_CONNECTED
3. 发 C2S_AUTH 鉴权换登录态
4. 后台心跳线程保活
5. 业务请求：`send_msg("C2S_xxx", protobuf)` → `recv_until(expect_id=...)` → 用对应 S2C 类解析

**二进制协议**：每个消息包 = `[4字节大端消息ID] + [Protobuf数据]`，消息ID由消息名哈希算出（算法复刻自服务端 Go 源码）。

## 环境要求

- Python 3.10+
- 依赖见 `requirements.txt`
- 可访问游戏测试服（默认 192.168.0.90:8888）

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
# 跑全部用例
pytest tests/ -s

# 跑单个模块
pytest tests/.py -s

# 只收集不执行（验证导入）
pytest --collect-only -q
```

## 用例清单

| 模块 | 用例 | 断言点 |
|---|---|---|
| 登录 | test_login | 登录成功、ws连接建立 |
| 背包 | test_query_backpack | 背包非空 |
| 商店 | test_query_shop / test_buy_gift / test_buy_and_check_backpack | code=0、买前买后背包变化 |
| 邮件 | test_query_mail / test_get_attachments / test_delete_mail | 删除后邮件不在列表 |
| 角色 | test_query_role_info | 角色信息返回 |
| 药草栽培 | test_query_steward_list / test_train_steward | 列表非空、code=0、经验增加 |
| 活动 | test_query_activity / test_query_holiday_lucky_bag / test_activity_time_check | 配表vs服务器时间对拍 |

## 配置

环境/账号/超时在 `config/settings.py`，换环境只改这一个文件。

## 已知问题

- `test_train_steward`：药草培养协议服务端不回包（60s超时无响应），疑点在服务端 handler 内部异常，详见 `docs/`。
