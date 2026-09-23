"""
全局配置：URL、服务器、超时、心跳、测试账号、协议ID等常量。
改环境只需要改这个文件，不用到处找。

这些常量被 game_client.py / api / tests 直接 import 用：
  - LOGIN_URL 等：HTTP 登录用；
  - WS_TIMEOUT / HEARTBEAT_INTERVAL：连接与心跳用；
  - HEARTBEAT_RESPONSE_ID：收消息时用来跳过心跳响应；
  - ACCOUNT_* / DEFAULT_SERVER_ID：测试用例登录用；
  - ACTIVITY_HOLIDAY_SQL：配表对拍用例读配表用；
  - S2C_CONNECTED_ID / S2C_ERROR_ID：连接确认与服务器错误识别用。
"""
from proto.proto_hashmap import SHOP_ID

# ===== HTTP 登录配置 =====
LOGIN_URL = "http://192.168.0.90:8888/api/login"
LOGIN_PLATFORM = "local"
LOGIN_UTM_MEDIUM = ""

# ===== WebSocket 配置 =====
WS_TIMEOUT = 10  # 收消息单帧超时时间（秒）

# ===== 心跳配置 =====
HEARTBEAT_INTERVAL = 10  # 心跳间隔（秒）
HEARTBEAT_RESPONSE_ID = 687543686  # 心跳响应的消息ID（用来跳过心跳）

# ===== 收消息配置 =====
RECV_MAX_RETRY = 10  # recv_until 最多接收的真实消息帧数（防推送风暴死循环）
RECV_TOTAL_TIMEOUT = 60  # recv_until 总等待上限（秒），防止服务器静默时无限干等

# ===== 测试账号与服务器 =====
DEFAULT_SERVER_ID = "14"  # 默认服务器ID
DEFAULT_BACKPACK_ID = 1   # 默认背包ID

# 不同用例需要不同状态的账号（等级/资源不同），按用途命名，换环境时只改这里
ACCOUNT_GENERAL = "auto"      # 通用账号：登录/商店/活动

# ===== 协议固定消息ID（对应 proto/proto_hashmap.py） =====
S2C_CONNECTED_ID = 1208559756  # 连接确认消息
S2C_ERROR_ID = 1289121170      # 服务器通用错误响应（S2C_ERROR，含 code/pid）

# 商店id
SHOP_ID = 7
# noinspection PyUnresolvedReferences
