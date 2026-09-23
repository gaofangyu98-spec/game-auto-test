"""
游戏协议工具：消息ID哈希、封包、拆包。
从服务器 wsptc.go 源码复刻，算法必须和服务器完全一致，否则对方解析不了。

整条消息的二进制长这样（封包后）：
    [4 字节大端消息ID] + [Protobuf 序列化出来的字节]
    └─ pack_message 负责拼起来 ─┘   └─ 业务层填好 protobuf 后给出 ─┘
反过来 unpack_message 就是先切前4字节拿ID，剩下的原样交出去。
"""
import struct


def hash_msg_name(name: str) -> int:
    """
    计算消息名的哈希值（对应服务器 wsptc.Hash）。

    这是整个项目最"死板"的一个函数：
    服务器用这套算法把消息名变成整数ID，客户端必须算得一模一样，
    ID 错一位服务器就不认这条消息。所以这里的每一步都是从
    服务器 Go 源码逐行搬过来的，不能"优化"。

    算法：nHash ^= (nHash << 5) + char + (nHash >> 2)
    初始值 1315423911，最后取低31位。
    逐行拆解：
      1. n_hash = 1315423911          初始种子（服务器写死的）
      2. for c in name.encode()       遍历消息名的每个字节（ASCII 值）
      3. (n_hash << 5)                左移5位 = 乘以32，把历史信息扩散开
      4. (n_hash >> 2)                右移2位 = 除以4，掺入高位信息
      5. 三者相加再异或 n_hash        混合出新的哈希值
      6. & 0xFFFFFFFF                 每步都截断到 32 位（Go 的 uint32 溢出行为）
      7. 最后 & 0x7FFFFFFF            取低31位（服务器最后也这么做）
    """
    n_hash = 1315423911
    for c in name.encode():
        n_hash ^= ((n_hash << 5) + c + (n_hash >> 2)) & 0xFFFFFFFF
        n_hash &= 0xFFFFFFFF
    return n_hash & 0x7FFFFFFF


def pack_message(msg_name: str, protobuf_data: bytes) -> bytes:
    """
    封包：4字节大端消息ID + protobuf消息体，对应服务器 wsptc.Encode。

    struct.pack('>I', ...) 里：
      '>' 表示大端序（高字节在前，服务器用同样的字节序，反了就全乱）；
      'I' 表示 4 字节无符号整数。
    """
    msg_id = hash_msg_name(msg_name)
    header = struct.pack('>I', msg_id)
    return header + protobuf_data


def unpack_message(data: bytes) -> tuple:
    """
    拆包：把收到的字节切成 (消息ID, protobuf数据)，对应服务器 wsptc.Decode。

    前4字节按大端解成整数ID（这就是"消息ID"），
    第5字节起就是 protobuf 原始数据，原样返回，让上层决定用哪个类解析。
    """
    if len(data) < 4:
        # 连 4 字节的消息头都不够，肯定是坏包，返回 (0, b'', False)
        return 0, b'', False
    msg_id = struct.unpack('>I', data[:4])[0]
    return msg_id, data[4:], True
