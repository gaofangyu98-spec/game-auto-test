"""
业务 API 基类：封装"构造 -> 发送 -> 收期望响应 -> 解码"的公共四步。

所有业务 API 都是同一个套路，重复写一遍样板代码很啰嗦。
继承本类后，业务方法只需：
  1. new 一个 C2S_xxx() 并填好字段；
  2. 调 self.request("C2S_xxx", 消息对象, S2C_xxx)；
底层发消息、算期望响应ID、等响应、解码全部由基类完成。

【为什么响应名可以由 C2S_ 推导成 S2C_】
  游戏协议有一条铁律：消息成对出现，C2S_xxx（客户端发）必有对应的
  S2C_xxx（服务器回），所以 "C2S_BACKPACK" 的响应一定是
  "S2C_BACKPACK"。靠这个约定，request 里就不用每次手动传响应名。
"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))

# noinspection PyUnresolvedReferences
from proto.proto_utils import hash_msg_name


class BaseAPI:
    """持有 GameClient 实例，提供通用请求方法"""

    def __init__(self, client):
        self.client = client

    def request(self, c2s_name, query, s2c_class, assert_msg="客户端没有收到响应......"):
        """
        发送 C2S 请求并等待对应的 S2C 响应，解码后返回。

        参数说明：
          c2s_name:   请求消息名，如 "C2S_BACKPACK"；
                      响应消息名由它推导（把开头的 C2S_ 换成 S2C_）
          query:      已填好字段的 C2S 消息对象
          s2c_class:  对应响应消息的 protobuf 类（如 S2C_BACKPACK）
          assert_msg: 收不到响应时的断言提示

        内部四步（等价于每个业务方法原来手写的那四步）：
          1. send_msg：封包并发送；
          2. hash_msg_name：算出期望响应 ID；
          3. recv_until：跳过心跳/同步推送/S2C_ERROR，精确等到目标响应；
          4. ParseFromString：把二进制解码成结构化的响应对象。
        """
        self.client.send_msg(c2s_name, query)

        s2c_name = c2s_name.replace("C2S_", "S2C_", 1)
        expect_id = hash_msg_name(s2c_name)
        msg_id, data = self.client.recv_until(expect_id = expect_id)
        print(f"该消息协议 : {s2c_name}, 共 （{len(data)}） 字节")
        assert msg_id is not None, assert_msg

        resp = s2c_class()
        resp.ParseFromString(data)
        return resp
