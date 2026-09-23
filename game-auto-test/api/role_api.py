"""
角色信息API
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
# noinspection PyUnresolvedReferences
from proto.msg_player_role_pb2 import (
    C2S_PLAYER_ROLE_INFO,
    S2C_PLAYER_ROLE_INFO
)

from api.base_api import BaseAPI


class RoleAPI(BaseAPI):
    """角色信息 API：查询当前玩家角色详情。"""

    def get_role_info(self):
        """
        查询当前玩家的角色信息

        返回: S2C_PLAYER_ROLE_INFO 对象
        """
        # 构造（空消息）+ 发送 + 收响应 + 解码
        query = C2S_PLAYER_ROLE_INFO()
        resp = self.request(
            "C2S_PLAYER_ROLE_INFO", query, S2C_PLAYER_ROLE_INFO,
            "查询角色信息没有收到响应"
        )

        # 打印所有字段
        print(f"\n=====角色信息=====")
        print(f"名字: {resp.name}")
        print(f"ID: {resp.id}")
        print(f"等级: {resp.lv}")
        print(f"VIP等级: {resp.vipLv}")
        print(f"师团ID: {resp.guildId}")
        print(f"创角第几天: {resp.days}")
        print(f"货币符号: {resp.currency}")
        print(f"是否默认名字: {resp.isDefaultName}（1=默认，2=自定义）")
        print(f"指挥室默认皮肤: {resp.showMainSkinId}")
        print(f"创角时间: {resp.createdTs}（毫秒时间戳）")
        print(f"当前头像: {resp.iconActived}")


        return resp
