"""商城业务 API：查询商店、购买商品/礼包。"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))

# noinspection PyUnresolvedReferences
from proto.msg_user_shop_pb2 import (
    C2S_SHOP_SYS, S2C_SHOP_SYS,
    C2S_SHOP_SYS_BUY, S2C_SHOP_SYS_BUY
)

from api.base_api import BaseAPI


class ShopAPI(BaseAPI):
    """
    商城业务API：查询商店、购买商品
    持有 GameClient 实例，用它做底层通信
    """

    def query_shop(self, shop_type, cfg_id):
        """
        查询商店商品列表

        shop_type: 商店类型（比如502=礼包商店）
        cfg_id: 活动配表id，默认0
        返回: S2C_SHOP_SYS 对象（里面有 infos 商品列表）
        """
        # 构造查询消息
        query = C2S_SHOP_SYS()
        query.shop_type = shop_type
        query.cfg_id = cfg_id

        # 发送 + 精确等 S2C_SHOP_SYS 响应 + 解码。
        # 比原来"跳过心跳后拿第一条业务消息"更稳：
        # 收到 S2C_SYNC_* 推送会被自动跳过，服务器回 S2C_ERROR 会打印错误码。
        resp = self.request("C2S_SHOP_SYS", query, S2C_SHOP_SYS, "查询商店没收到响应")
        return resp

    def buy_shop_item(self, shop_id, conf_id, buy_count, cfg_id, source):
        """
        购买商店商品

        shop_id: 商店ID（比如502）
        conf_id: 商品配表id（比如50208）
        buy_count: 购买数量，默认1
        cfg_id: 活动配表id，默认0
        source: 购买来源，玩家手动填0
        返回: (S2C_SHOP_SYS_BUY 对象, 是否成功)
        """
        # 构造购买消息
        buy = C2S_SHOP_SYS_BUY()
        buy.shop_id = shop_id
        buy.conf_id = conf_id
        buy.buy_count = buy_count
        buy.cfgId = cfg_id
        buy.source = source

        # 发送 + 精确等 S2C_SHOP_SYS_BUY 响应 + 解码
        resp = self.request("C2S_SHOP_SYS_BUY", buy, S2C_SHOP_SYS_BUY, "购买没收到响应")

        # 判断成功失败
        success = (resp.code == 0)
        print(f"购买结果: code = {resp.code}, {'成功' if success else '失败'}")
        return resp, success

    def buy_gift(self, shop_id, conf_id, buy_count, cfg_id, source):
        """
        购买礼包
        """
        return self.buy_shop_item(shop_id, conf_id, buy_count, cfg_id, source)
