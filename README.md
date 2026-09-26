# game-auto-test

游戏协议自动化测试框架。基于 HTTP 登录 + WebSocket 长连接 + Protobuf 二进制协议，封装游戏客户端完整通信层，用 PyTest 组织背包、商店、邮件、角色、活动、排行榜、任务等核心业务模块的回归用例，替代游戏版本测试中重复的手工协议验证工作。已接入 GitHub Actions CI，提交代码自动跑语法检查、生成测试报告并飞书通知。

## 目录

- [核心亮点](#核心亮点)
- [项目背景](#项目背景)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [通信模型与二进制协议](#通信模型与二进制协议)
- [核心设计点](#核心设计点)
- [环境要求](#环境要求)
- [安装与运行](#安装与运行)
- [用例覆盖](#用例覆盖)
- [配置说明](#配置说明)
- [CI/CD](#cicd)
- [游戏协议测试 vs Web 接口测试](#游戏协议测试-vs-web-接口测试)
- [已知问题与定位过程](#已知问题与定位过程)
- [后续规划](#后续规划)

---

## 核心亮点

| 亮点 | 说明 |
|---|---|
| 自研协议通信层 | 复刻服务端 Go 源码的消息 ID 哈希算法，实现 [4 字节大端 ID + Protobuf] 二进制封包拆包 |
| 精准消息等待 | recv_until 自动跳过心跳 / 同步推送 / S2C_ERROR，精确匹配期望响应，双保险防死循环（max_retry + total_timeout） |
| 四步模板封装 | BaseAPI 统一"构造→发送→收响应→解码"，业务 API 只填 Protobuf 字段，消除重复样板代码 |
| 登录态复用 | session 级 fixture 一次登录，全部用例共享同一条 WebSocket 连接，冒烟测试从 8s 优化到 1.5s |
| 冒烟测试集合 | 一次登录串联 7 个核心模块，pytest -m smoke 一键跑，可直接接 CI/CD |
| 配表对拍 | 从 .sql 配表文件抠 0x 十六进制还原 Excel，openpyxl 解析后与服务器返回数据对拍 |
| CI 自动检查 | GitHub Actions 在 push/PR 时跑 py_compile 语法检查 + collect-only 生成 HTML 报告，飞书 webhook 通知结果 |
| 硬断言覆盖 | 每个用例都有字段级断言（ID 合法性、非空、时间校验、删除验证、购买前后对比） |

---

## 项目背景

游戏测试和普通 Web 测试最大的区别在于通信方式：普通 Web 接口是 HTTP + JSON 短连接，发一次请求拿一次响应；而游戏客户端和服务端之间是 WebSocket 长连接 + Protobuf 二进制协议，登录一次后全程复用同一条 TCP 连接，服务端还会主动推送各种同步消息（道具变化、邮件到达、系统通知）。

手工测一个"买东西"的流程，需要在游戏客户端里点点点：打开商店、选商品、点购买、切回背包看道具数量对不对。版本一更新就要全部重来，效率极低。

这个项目的目标是用 Python 脚本直接跟游戏测试服对话：模拟客户端发协议、收响应、做断言，把核心业务的回归用例自动化跑起来，版本更新后一条命令验证核心链路有没有挂。

---

## 技术栈

- Python 3.10+
- WebSocket：websocket-client
- Protobuf：protoc 编译 .proto 生成 _pb2.py
- PyTest：用例组织与断言
- requests：HTTP 登录阶段
- threading：daemon 后台心跳线程
- openpyxl：解析策划配表 Excel
- GitHub Actions：CI 流水线
- 飞书 webhook：CI 结果通知

---

## 项目结构

```
game-auto-test/
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI：语法检查 + 报告生成 + 飞书通知
├── config/                 # 配置层
│   ├── settings.py         # 环境地址、账号、超时、心跳、消息 ID 常量
│   └── loader.py           # 配表加载器：从 .sql 抠 0x 十六进制 → openpyxl 解析 Excel
├── client/
│   └── game_client.py      # 通信层：登录、WS 连接、鉴权、心跳、通用收发
├── api/                    # 业务层：每个游戏模块一个文件
│   ├── base_api.py         # 基类：封装发请求→等响应→解码四步
│   ├── bag_api.py          # 背包
│   ├── shop_api.py         # 商店
│   ├── mail_api.py         # 邮件
│   ├── role_api.py         # 角色
│   ├── activity_api.py     # 活动
│   ├── rank_api.py         # 排行榜（16 种榜单类型枚举）
│   └── task_api.py         # 任务
├── proto/                  # 协议层
│   ├── *.proto             # 消息定义
│   ├── *_pb2.py            # protoc 生成的 Python 类
│   ├── proto_utils.py      # 封包/拆包：4 字节大端 ID + Protobuf 数据
│   └── proto_hashmap.py    # 消息名 → 消息 ID 映射表
├── tests/                  # 用例层
│   ├── conftest.py         # session 级 fixture：一次登录全用例共享
│   ├── test_smoke.py       # 冒烟集合：一次登录串 7 个模块
│   ├── test_login.py
│   ├── test_bag.py
│   ├── test_shop.py
│   ├── test_mail.py
│   ├── test_role.py
│   ├── test_rank.py
│   ├── test_task.py
│   └── test_activity.py
├── reports/                # 失败现场与运行日志（gitignore）
├── docs/                   # 问题分析文档
├── sql/                    # 配表 SQL 文件
├── utils/
│   ├── time_controller.py  # 时间控制器
│   └── test_loader.py       # 配表加载器的自测
├── pytest.ini
└── requirements.txt
```

分层原则：业务用例（tests）只关心"我要查背包，期望返回什么"，不关心底层 WebSocket 怎么连、协议怎么封包、心跳怎么保。所有通信细节都封在 client 和 proto 层。

调用链：tests/ → api/ → client/ → 游戏服务器。

---

## 通信模型与二进制协议

### 完整登录链路

一次业务请求（比如"查背包"）的完整流程：

1. **HTTP 登录**：GET 登录接口，传 access_code（兑换码）+ server_id，服务端返回 JSON，data 分三块：
   - UserInfo：拿到 cuid（渠道用户 ID）、rid（角色 ID）
   - ServerInfo：拿到 Address（WebSocket 连接地址）
   - AuthInfo：拿到 Token、Ts（时间戳）

2. **WebSocket 连接**：连上上一步拿到的 Address。连上后服务端会主动推第一条消息 S2C_CONNECTED（连接确认），客户端必须先收掉这条并校验消息 ID，否则后面收业务响应时会把它当第一条业务消息，解析直接错乱。

3. **Protobuf 鉴权**：构造 C2S_AUTH 消息，填 cuid / rid / ts / token / lang / currency，封包后发出去。服务端回 S2C_AUTH，成功判定标准是 server_ts > 0（服务端给当前时间戳就说明验明正身了）。如果服务端回 S2C_ERROR，解析错误码抛异常（token 过期、账号被踢等）。

4. **心跳保活**：启动 daemon 后台线程，每隔 10 秒发一条 C2S_HEARTBEAT 空消息，告诉服务端"我还活着"，防止服务端因为一段时间没消息主动断开连接。

5. **业务收发**：发 C2S_xxx → 服务端回 S2C_xxx → 用对应 Protobuf 类解析。

### 二进制消息格式

每个消息包 = `[4 字节大端消息 ID] + [Protobuf 序列化后的字节]`

- 前 4 字节是消息 ID，大端序（网络字节序），告诉服务端这是什么消息
- 后面的字节是 Protobuf 业务数据，服务端根据消息 ID 知道用哪个 Protobuf 类去解析

### 消息 ID 哈希算法

服务端是 Go 写的，消息 ID 不是简单的递增数字，而是根据消息名字符串哈希算出来的。`proto_utils.py` 里复刻了服务端的哈希算法（从服务端 Go 源码对照过来），保证客户端算出来的 ID 和服务端完全一致。算错一位，服务端直接不认，连接断掉。

例如 `C2S_AUTH` 这个消息名算出来的 ID 是 `780175315`。

---

## 核心设计点

### recv_until：循环收消息 + 过滤无关推送

这是整个框架最关键的一个方法。

为什么不能"收到一条就算完"：WebSocket 是双向长连接，一条请求发出去后，消息流上会同时混着四种东西：

1. 心跳响应：服务端对心跳的自动回执，跟业务无关
2. 服务端主动推送 S2C_SYNC_*：别的系统变化触发的同步（道具数量变了、邮件来了），不是我们请求的答案
3. S2C_ERROR：服务端通用错误码（资源不足、参数非法）
4. 我们真正要的业务响应

所以必须循环收消息，一条条判断：是无关的就跳过，是目标消息才返回。

自动跳过的集合：启动时动态扫描 proto_hashmap 里所有 S2C_SYNC_* 开头的常量，自动收集成跳过集合，不用手工维护一长串 ID。

两个防死循环的保险丝：

- max_retry：服务端疯狂推无关消息时，最多收 10 帧真实消息就放弃，防止推送风暴把程序拖死
- total_timeout：服务端一直沉默时，最多等 60 秒就放弃，防止无限干等。超时帧不计入 max_retry，因为沉默不是风暴

### BaseAPI 四步封装

所有业务 API 都继承 BaseAPI，request 方法封装了通用四步：

1. send_msg 发请求（封包 + WebSocket 发送）
2. 自动推导响应名：`C2S_xxx → S2C_xxx`（游戏协议铁律：消息成对出现，客户端发什么，服务端就回同名的 S2C_xxx）
3. hash_msg_name 算出期望响应的消息 ID
4. recv_until 等响应，拿到字节后用对应 S2C 类 ParseFromString 解码

业务层只需要：new 一个 C2S_xxx、填字段、调 `self.request(...)`，不用写任何收发代码。新增一个业务接口就是在 `api/` 下加个方法，十几行代码。

### 登录态复用（session 级 fixture）

每个用例如果都自己登录一次，7 个用例要登 7 次，光登录就花 8 秒。

`conftest.py` 里写了一个 session 级 fixture：整个 pytest 会话开始时登录一次，建立 WebSocket 连接，所有用例共享这同一条连接。跑完所有用例后 fixture 销毁，关闭连接、停心跳。

优化后整个冒烟集合从 8 秒压到 1.5 秒。

### 配表加载器（loader.py）

游戏策划的数值配置先做在 Excel 里，导出工具把整个 Excel 文件以 0x 开头的十六进制形式塞进一条 SQL INSERT 语句里。配表文件虽然叫 .sql，里面真正有用的是那串十六进制。

loader.py 做的事：
1. 正则从 .sql 文件里抠出 0x 开头的十六进制字符串
2. bytes.fromhex 转成二进制
3. openpyxl 从 BytesIO 读成 Excel 表格
4. 解析成字典列表给用例用

活动时间校验用例就用这个加载器读配表，把配表里的活动开始/结束时间和服务器返回的活动时间对拍，配表和服务器不一致就是 Bug。

### 心跳线程设计

- 用 daemon 线程：主程序退出时它自动结束，不会卡住进程
- 睡眠拆成 1 秒粒度，而不是一次性 sleep N 秒：close() 时要能及时退出线程，1 秒粒度最多等 1 秒就发现 running=False
- 心跳发送失败（连接断了）就退出循环，不再空发

---

## 环境要求

- Python 3.10+
- 依赖见 `requirements.txt`
- 可访问游戏测试服

---

## 安装与运行

```bash
# 安装依赖
pip install -r requirements.txt

# 跑全部用例
pytest tests/ -s

# 只跑冒烟用例（CI 推荐）
pytest -m smoke

# 跑单个模块
pytest tests/test_shop.py -v

# 只收集不执行（验证导入是否正确）
pytest --collect-only -q
```

---

## 用例覆盖

### 冒烟用例（pytest -m smoke，只查不改，可反复跑）

| 模块 | 用例 | 断言点 |
|---|---|---|
| 登录 | test_login | cuid 非空、WebSocket 连接建立 |
| 背包 | test_query_backpack | 背包非空、道具数量合法 |
| 角色 | test_query_role_info | ID>0、名字非空、等级 / VIP 合法 |
| 邮件 | test_query_mail | 邮件 ID>0、标题非空、创建时间合法 |
| 商店 | test_query_shop | 商品列表非空 |
| 活动 | test_query_activity | 活动 ID>0、开始时间 < 结束时间 |
| 排行榜 | test_query_rank | 榜单列表非空、我的排名合法 |
| 任务 | test_query_task | 任务类型匹配、任务 ID>0、进度 >=0 |
| 冒烟集合 | test_smoke_all | 一次登录串联以上 7 个模块查询 |

### 操作类用例（写操作，单独跑，不进冒烟）

| 模块 | 用例 | 断言点 |
|---|---|---|
| 商店 | test_buy_gift | 购买返回 code=0 |
| 商店 | test_buy_and_check_backpack | 买前买后背包对比，道具到账 |
| 邮件 | test_get_attachments | 领取后 is_item_got=True |
| 邮件 | test_delete_mail | 删除后邮件不在剩余列表 |
| 药草栽培 | test_train_steward | 训练后经验值增加 |
| 活动 | test_activity_time_check | 配表时间 vs 服务器时间对拍 |

---

## 配置说明

环境地址、账号、超时时间、消息 ID 常量集中在 `config/settings.py`，切换测试环境只改这一个文件。

| 配置项 | 说明 |
|---|---|
| LOGIN_URL | HTTP 登录地址 |
| LOGIN_PLATFORM | 登录平台标识 |
| ACCOUNT_GENERAL | 通用测试账号（登录/商店/活动用） |
| DEFAULT_SERVER_ID | 默认服务器 ID |
| DEFAULT_BACKPACK_ID | 默认背包 ID |
| WS_TIMEOUT | WebSocket 单帧超时（秒），默认 10 |
| HEARTBEAT_INTERVAL | 心跳间隔（秒），默认 10 |
| HEARTBEAT_RESPONSE_ID | 心跳响应消息 ID，收消息时跳过 |
| RECV_MAX_RETRY | recv_until 最大接收帧数（防推送风暴），默认 10 |
| RECV_TOTAL_TIMEOUT | recv_until 总等待上限（秒），默认 60 |
| S2C_CONNECTED_ID | 连接确认消息 ID |
| S2C_ERROR_ID | 服务器通用错误消息 ID |
| SHOP_ID | 测试商店 ID |

---

## CI/CD

项目已配置 GitHub Actions（`.github/workflows/ci.yml`），在 push 或 PR 到 main/master 分支时自动执行：

1. 检出代码 + 设置 Python 3.12 环境
2. 安装依赖
3. 语法检查：`python -m py_compile` 编译 api / client / config / tests 下所有 .py 文件
4. 生成测试报告：`pytest --collect-only` 收集用例，导出 HTML 报告
5. 上传报告作为 artifact（无论成功失败都上传）
6. 飞书 webhook 通知：成功发 ✅，失败发 ❌，带分支名和提交人

飞书 webhook 地址存在 GitHub Secrets 的 `FEISHU_WEBHOOK` 里，不硬编码在 yml 里。

---

## 游戏协议测试 vs Web 接口测试

| 维度 | Web 接口测试 | 游戏协议测试 |
|---|---|---|
| 协议 | HTTP + JSON | WebSocket + Protobuf 二进制 |
| 连接 | 短连接，一次请求一次连接 | 长连接，登录一次全程复用 |
| 消息流 | 请求响应一一对应 | 服务端主动推送，需过滤无关消息 |
| 保活 | 不需要 | 必须心跳线程保活 |
| 序列化 | JSON 文本，可读性好 | Protobuf 二进制，需要 .proto 定义 |
| 消息标识 | URL 路径 | 消息名哈希出 4 字节消息 ID |

---

## 已知问题与定位过程

**test_train_steward 用例挂了**：发完 C2S 消息后服务端 60 秒不回包，recv_until 超时返回。

定位过程：
1. 先排除客户端问题：用 Fiddler 抓包，确认请求字节确实发出去了，格式正确
2. 排除鉴权问题：其他协议都能正常收发，鉴权链路没问题
3. 对比抓包数据：把客户端发的消息字段和真实游戏客户端发的逐字段对比
4. 结论：服务端 handler 内部异常（某个字段空指针），没捕获就静默不回包了
5. 整理成问题文档放 docs/，交给服务端同学排查

---

## 后续规划

- [ ] 接入 Allure 可视化测试报告，替代当前 print 日志
- [ ] 用例失败自动重跑（pytest-rerunfailures），偶发网络抖动自动重试
- [ ] 多账号并发支持，满足简单压测需求
- [ ] 用例数据隔离，每个写操作用例独立账号，避免用例之间互相污染状态
- [ ] 协议版本自动同步：proto 文件更新后自动重新生成 _pb2.py
- [ ] CI 里除了 collect-only，接入真实冒烟用例执行（当前只做语法检查和收集）
