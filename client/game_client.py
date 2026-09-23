"""
游戏自动化测试底层 WebSocket 客户端。

封装：HTTP 登录拿 token -> 连接 WebSocket -> Protobuf 鉴权 -> 后台心跳 -> 通用收发。
业务层（api/ 目录）只负责填 Protobuf 消息字段，再调用本类的 send_msg/recv_until。

【理解整件事的一条主线】
  一次业务请求（比如"查背包"）在底层是这样流转的：
    1. HTTP 登录：向登录服务器要"账号凭证 + WebSocket 地址"；
    2. WS 连接：连上游戏服务器（此时服务器先推一条 S2C_CONNECTED 确认）；
    3. 鉴权：把凭证塞进 C2S_AUTH 发给服务器，换登录态；
    4. 心跳：后台线程定时发空消息，防止连接被服务器掐断；
    5. 业务：发 C2S_BACKPACK -> 服务器回 S2C_BACKPACK -> 用对应 protobuf 类解析。

【二进制协议（由 proto_utils 负责）】
  每个消息包 = [4字节大端消息ID] + [Protobuf 序列化数据]
  消息ID = hash_msg_name("消息名")，例如 "C2S_AUTH" 算出来是 780175315。
  这套哈希必须和服务器源码一致，算错一位服务器就不认。

【本类收到消息后只交原始字节，不自动反序列化】
  到底用哪个 Protobuf 类解析，由上层 api/*.py 决定：
  拿到 data 后 new 一个对应的 S2C_xxx，再 ParseFromString(data)。
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import threading
import requests
import websocket

from config.settings import (
    LOGIN_URL, LOGIN_PLATFORM, LOGIN_UTM_MEDIUM,
    WS_TIMEOUT, HEARTBEAT_INTERVAL, HEARTBEAT_RESPONSE_ID,
    RECV_MAX_RETRY, RECV_TOTAL_TIMEOUT,
    S2C_CONNECTED_ID, S2C_ERROR_ID
)
from proto.proto_utils import pack_message, unpack_message
# noinspection PyUnresolvedReferences
from proto.msg_login_pb2 import C2S_AUTH, S2C_AUTH, C2S_HEARTBEAT
# noinspection PyUnresolvedReferences
from proto.msg_sync_pb2 import S2C_ERROR, S2C_CONNECTED


def _collect_sync_msg_ids():
    """收集所有 S2C_SYNC_* 推送消息ID，收业务响应时默认跳过。

    为什么需要它：游戏服务器除了回响应，还会"主动推送"各种同步消息
    （道具数量变了、邮件来了……），这些不是我们请求的答案，如果混进
    等待逻辑里会污染结果。这里动态扫 proto_hashmap 里的常量名，
    免去手工维护一长串 ID 的麻烦。
    """
    from proto import proto_hashmap as hm
    return {
        value for name, value in vars(hm).items()
        if name.startswith("S2C_SYNC_") and isinstance(value, int)
    }


# 默认跳过的服务器推送消息ID：同步推送 + 心跳响应 + 连接确认
_SYNC_MSG_IDS = _collect_sync_msg_ids()


class GameClient:
    """
    游戏客户端：只放通用底层方法（登录、连接、收发消息、心跳）

    通信模型：
      1. HTTP 登录拿 token 和 WebSocket 地址；
      2. 连接 WebSocket，先收掉服务器的连接确认消息；
      3. 发送 C2S_AUTH 完成鉴权；
      4. 启动心跳线程保持连接；
      5. 业务层通过 send_msg / recv_until 按“消息名”收发数据。

    二进制协议由 proto_utils 负责：
      每个消息包 = [4字节大端消息ID] + [Protobuf 序列化数据]
      消息ID = hash_msg_name("消息名")，例如 "C2S_AUTH"。

    说明：本类收到消息后只把原始字节交出去，不会自动按 ID 反序列化。
    到底用哪个 Protobuf 类解析，由上层 api/*.py 决定（拿到 data 后
    new 一个对应的 S2C_xxx，再 ParseFromString(data)）。
    """

    def __init__(self):
        # WebSocket 连接对象，未登录前为 None
        self.ws = None
        # cuid: 渠道用户ID；rid: 游戏角色ID，均由 HTTP 登录结果填充
        self.cuid = None
        self.rid = None
        # token/ts: 鉴权令牌和登录时间戳；lang/currency: 客户端语言和货币
        self.token = None
        self.ts = None
        self.lang = None
        self.currency = None
        self.ws_url = None
        # 后台心跳线程，close 时会主动停止
        self.heartbeat_thread = None
        self.running = False

    # ==================== 登录 ====================

    def http_login(self, access_code, server_id):
        """
        HTTP登录，拿 token 和 WebSocket 地址。

        登录服务器返回的 JSON 里，data 分三块，各取所需：
          - UserInfo:  用户信息 -> 拿到 cuid（渠道用户ID）/ rid（角色ID）
          - ServerInfo: 服务器信息 -> 拿到 Address（WebSocket 连接地址）
          - AuthInfo:   鉴权信息 -> 拿到 Token / Ts（后面鉴权要用）

        一句话：这一步是把"账号名 + 服务器ID"换成"连接游戏服务器要用的凭证"。
        """
        print("\n============开始登录============")
        resp = requests.get(LOGIN_URL, params={
            "access_code": access_code,
            "platform": LOGIN_PLATFORM,
            "default_game_server": server_id,
            "utm_medium": LOGIN_UTM_MEDIUM
        })
        assert resp.status_code == 200  # HTTP 层没通直接失败
        data = resp.json()
        assert data["code"] == 0  # 业务层 code=0 才算登录成功

        user_info = data["data"]["UserInfo"]
        server_info = data["data"]["ServerInfo"]
        auth_info = data["data"]["AuthInfo"]

        self.ws_url = server_info["Address"]
        self.token = auth_info["Token"]
        self.ts = auth_info["Ts"]
        self.cuid = user_info["Cuid"]
        self.rid = user_info["Rid"]
        self.lang = user_info["Lang"]
        self.currency = user_info["Currency"]
        print(f"HTTP登录成功: 账号 = {self.cuid}, 角色ID = {self.rid}")

    def connect(self):
        """
        连接WebSocket服务器。

        为什么首条消息一定是 S2C_CONNECTED：
          这是游戏服务器的约定——玩家一连上，服务器先主动推一条"连接确认"。
        为什么必须消费掉它：
          这条消息不是我们请求来的，如果不先收走，它会排在消息流最前面，
          后面收业务响应时会把它当成第一条业务消息，导致解析错乱。
        为什么校验 ID：
          防止服务器行为变化（比如先推别的）时，程序把错误消息当确认吞掉。
        """
        self.ws = websocket.create_connection(self.ws_url, timeout=WS_TIMEOUT)
        print(f"WebSocket连接成功: {self.ws_url}")
        #接收服务器第一条消息
        first_msg = self.ws.recv()
        msg_id, data, ok = unpack_message(first_msg)
        if msg_id != S2C_CONNECTED_ID:
            #别继续往下跑了，直接报错停掉，不是服务器发来的ID
            raise ConnectionError(
                f"连接后首条消息不是 S2C_CONNECTED（期望ID={S2C_CONNECTED_ID}，实际ID={msg_id}）"
            )
        print(f"收到服务器默认第一条连接确认: 消息ID id={msg_id}, 数据长度={len(data)}")

    def auth(self):
        """
        发送 C2S_AUTH 鉴权。

        鉴权 = 拿着 HTTP 登录拿到的凭证（token/cuid/rid/ts...）跟服务器
        "验明正身"，换一个可以正常收发业务消息的登录态。
        判成功的标准：服务器回的 S2C_AUTH 里 server_ts > 0。
        为什么 server_ts > 0 就算成功：服务器只会给"验明正身的玩家"
        下发当前服务器时间戳，给不出来就说明鉴权没通过。
        """
        auth_msg = C2S_AUTH()
        auth_msg.cuid = self.cuid
        auth_msg.rid = self.rid
        auth_msg.ts = self.ts
        auth_msg.token = self.token
        auth_msg.lang = self.lang
        auth_msg.currency = self.currency

        packet = pack_message("C2S_AUTH", auth_msg.SerializeToString())
        self.ws.send(packet, opcode=websocket.ABNF.OPCODE_BINARY)
        print("已发送 C2S_AUTH 鉴权请求......")

        resp = self.ws.recv()
        resp_id, resp_data, ok = unpack_message(resp)
        if resp_id == S2C_ERROR_ID:
            # 服务器回 S2C_ERROR：解析错误码并抛出明确异常，而不是静默断言失败
            # （比如 token 过期、账号被踢下线，服务器会走通用错误通道回话）
            err = S2C_ERROR()
            err.ParseFromString(resp_data)
            raise RuntimeError(f"鉴权失败，服务器返回错误: code = {err.code}")
        s2c = S2C_AUTH()
        s2c.ParseFromString(resp_data)
        print(f"鉴权结果: "
              f"服务器时间 server_ts={s2c.server_ts}, "
              f"是否创建角色 is_created = {s2c.is_created}, "
              f"名字 name = {s2c.name}, "
              f"是否为新手 is_newbie = {s2c.is_newbie}")
        assert s2c.server_ts > 0, "鉴权失败"
        print("已接收 S2C_AUTH() 鉴权成功......")
        return s2c

    def login(self, access_code, server_id):
        """
        一键登录：HTTP登录 + 连接 + 鉴权 + 心跳。

        登录完成后就可以调用业务 API 了。
        """
        self.http_login(access_code, server_id)
        self.connect()
        self.auth()
        self.start_heartbeat()
        print("============登录成功============")

    def close(self):
        """关闭连接：先停心跳线程，再关闭 WebSocket"""
        self.stop_heartbeat()
        if self.ws:
            self.ws.close()
        print("连接已关闭!")

    # ==================== 心跳 ====================

    def send_heartbeat(self):
        """
        发送一次心跳。

        心跳是空消息 C2S_HEARTBEAT，用途只有一个：告诉服务器"我还活着"，
        防止服务器因为一段时间没消息而判定连接空闲、主动断开。
        """
        heartbeat = C2S_HEARTBEAT()
        packet = pack_message("C2S_HEARTBEAT", heartbeat.SerializeToString())
        self.ws.send(packet, opcode=websocket.ABNF.OPCODE_BINARY)
        print("心跳已发送,确认双方沟通......")

    def _heartbeat_loop(self):
        """
        心跳循环（后台线程）。

        细节：为什么不用 time.sleep(HEARTBEAT_INTERVAL) 一口气睡 10 秒，
        而是拆成 1 秒一次的小睡？
        因为 close() 时要能"及时退出"这个线程——如果线程正在睡大觉，
        要等它睡醒才能检查 running=False；拆成 1 秒粒度后，最迟 1 秒内
        就能发现停止信号退出。
        """
        while self.running:
            try:
                self.send_heartbeat()
            except Exception as e:
                print(f"心跳发送失败: {e}")
                break  # 连接大概率断了，再发也没意义，退出循环
            for _ in range(HEARTBEAT_INTERVAL):
                if not self.running:
                    break
                time.sleep(1)

    def start_heartbeat(self):
        """启动后台心跳线程"""
        self.running = True
        # daemon = True：守护线程，主程序退出时它自动结束，不会卡住进程
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        print("心跳线程已启动!")

    def stop_heartbeat(self):
        """停止心跳线程：置 running=False，最多等 3 秒让线程退出"""
        self.running = False
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=3)
        print("心跳线程已停止!")

    # ==================== 通用收发 ====================

    def send_msg(self, msg_name, protobuf_msg):
        """
        通用发消息：protobuf编码 + 封包 + 发送。

        msg_name: 消息名字符串，例如 "C2S_FLIGHT_ATTENDANT_TRAIN"
        protobuf_msg: 已填好字段的 protobuf 消息对象

        封包动作在 pack_message 里：
          算出消息ID（4字节大端）拼在 protobuf 字节前面，组成完整一帧。
        """
        packet = pack_message(msg_name, protobuf_msg.SerializeToString())
        self.ws.send(packet, opcode=websocket.ABNF.OPCODE_BINARY)
        print(f"已发送消息协议: {msg_name}  共 ({len(packet)}) 字节")

    def recv_msg(self, timeout=WS_TIMEOUT, quiet=False):
        """
        通用收消息：接收 + 拆包。

        返回 (消息ID, protobuf二进制数据)；超时或拆包失败返回 (None, b'')。
        quiet=True 时不打印单帧日志（recv_until 内部轮询时用，避免刷屏）。

        为什么每次都要 settimeout：
          websocket 库的超时是"一次性"的，收完一条就失效，
          所以每收一条前都要重新设一遍，否则会永久阻塞。
        """
        self.ws.settimeout(timeout)
        try:
            data = self.ws.recv()
        except websocket.WebSocketTimeoutException:
            if not quiet:
                print(f"接收超时: {timeout}秒")
            return None, b''
        msg_id, protobuf_data, ok = unpack_message(data)
        if not ok:
            print("拆包失败!")
            return None, b''
        if not quiet:
            print(f"收到消息协议: ID = {msg_id}, 数据长度 = {len(protobuf_data)}")
        return msg_id, protobuf_data

    def recv_until(self, skip_ids=None, expect_id=None, max_retry=None, total_timeout=None):
        """
        循环收消息，跳过无关消息直到收到目标消息。

        【为什么要"循环收+跳过"——这是理解本项目最关键的一处】
        WebSocket 是双向长连接，一条"请求"发出去后，消息流上会同时混着：
          1. 心跳响应：服务器对心跳的自动回执，跟业务无关；
          2. 服务器主动推送（S2C_SYNC_* 等）：别的玩家/系统变化触发的同步，
             也不是我们请求的答案；
          3. S2C_ERROR：服务器通用错误（比如资源不足、参数非法）；
          4. 业务响应：我们发请求后服务器返回的目标消息。
        所以不能"收到一条就算完"，而要一条条看：
          是无关消息就跳过，是目标消息才返回。

        【两个防死循环的保险丝】
          - max_retry：服务器疯狂推无关消息时，最多收这么多帧"真实消息"
            就放弃（防止推送风暴把程序拖死）；
          - total_timeout：服务器一直沉默时，最多等这么多秒就放弃
            （防止无限干等）。超时帧不计入 max_retry，因为沉默不是风暴。

        skip_ids: 要跳过的消息ID集合（默认：同步推送 + 心跳 + 连接确认）
        expect_id: 期望收到的消息ID，传了只收这个ID，其他全跳过
        max_retry: 最多收多少帧"真实消息"才放弃，防止推送风暴死循环
        total_timeout: 总等待秒数上限，防止服务器静默时无限干等

        返回 (消息ID, protobuf二进制数据)；收不到返回 (None, b'')。
        """
        if skip_ids is None:
            skip_ids = set(_SYNC_MSG_IDS)
            skip_ids.update([HEARTBEAT_RESPONSE_ID, S2C_CONNECTED_ID])
        if max_retry is None:
            max_retry = RECV_MAX_RETRY
        if total_timeout is None:
            total_timeout = RECV_TOTAL_TIMEOUT

        start = time.time()
        received = 0  # 真实收到的消息帧数（超时帧不计入，静默不算推送风暴）
        while received < max_retry:
            # 超过总等待时长：放弃，防止服务器一直不回话时无限循环
            if time.time() - start > total_timeout:
                break
            msg_id, data = self.recv_msg(quiet=True)
            if msg_id is None:
                # 单帧接收超时：
                #   没传 expect_id 时保持"快速失败"旧行为（第一条业务消息都没等到）；
                #   传了 expect_id 时继续等，但受 total_timeout 总时长约束。
                if expect_id is None:
                    return None, b''
                continue
            received += 1
            if msg_id == S2C_ERROR_ID:
                # 业务失败时服务器回 S2C_ERROR：打印错误码，继续等目标消息
                self._report_server_error(data)
                continue
            if msg_id in skip_ids:
                print(f"跳过无关消息 ID = {msg_id}，继续等...")
                continue
            if expect_id is not None and msg_id != expect_id:
                print(f"收到非期望消息 ID = {msg_id}（期望 {expect_id}），继续等...")
                continue
            # 就是目标消息了，返回给调用方解析
            print(f"收到目标消息: ID = {msg_id} ")
            return msg_id, data

        print(f"等了 {total_timeout} 秒 / 收了 {received} 帧都没收到目标消息")
        return None, b''

    def _report_server_error(self, data):
        """解析并打印服务器 S2C_ERROR 内容（业务失败信号）"""
        try:
            err = S2C_ERROR()
            err.ParseFromString(data)
            print(f"服务器返回错误: code = {err.code}")
        except Exception:
            print(f"服务器返回 S2C_ERROR 但解析失败，原始数据长度 = {len(data)}")
