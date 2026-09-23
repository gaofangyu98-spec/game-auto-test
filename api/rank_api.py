"""排行榜业务 API：查询榜单列表、查询单个榜单详情。"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))
# noinspection PyUnresolvedReferences
from proto.msg_rank_pb2 import C2S_RANKING_LIST, S2C_RANKING_LIST, C2S_RANKING_INFO, S2C_RANKING_INFO
from api.base_api import BaseAPI

# 榜单类型ID
# 榜单类型ID（对应 proto 里的 RANK_ID 枚举，只保留"全部"类）
class RankType:
    GOLD_ALL = 1            # 课税榜-全部
    HERO_ALL = 4            # 伙伴榜-全部
    WARSHIP_ALL = 7         # 战舰榜-全部
    GUILD_ALL = 10          # 师团榜-全部
    FLIGHT_ALL = 13         # 乘务员榜-全部
    PVP_ALL = 16            # PVP榜-全部
    BANQUET_ALL = 19        # 宴会榜-全部
    MEDALBOSS_ALL = 22      # 勋章战榜-全部
    GUILD_TRAVEL_WEEK = 25  # 师团运输榜-本周
    GUILD_TRAVEL_LAST_WEEK = 26  # 师团运输榜-上周
    WORLDBOSS_ALL = 27      # 世界BOSS伤害榜-全部
    GVG_SCORE = 30          # GVG积分榜
    GVG_GUILD_SCORE = 31    # GVG师团积分榜
    GVG_SERVER_SCORE = 32   # GVG区服积分榜
    CROSS_PVP_ROLE = 41     # 跨服PVP榜-个人
    CROSS_PVP_SERVER = 42   # 跨服PVP榜-区服
    TEXAS_ALL = 43          # 德州榜-全部
    MOUNTAIN_HERO = 46      # 爬塔榜-英雄
    MOUNTAIN_WARSHIP = 47   # 爬塔榜-战舰
    TEST_WORLD_ALL = 101    # 测试榜-全服

    # 榜单ID → 中文名 映射
    NAME_MAP = {
        GOLD_ALL: "课税榜",
        HERO_ALL: "伙伴榜",
        WARSHIP_ALL: "战舰榜",
        GUILD_ALL: "师团榜",
        FLIGHT_ALL: "乘务员榜",
        PVP_ALL: "PVP榜",
        BANQUET_ALL: "宴会榜",
        MEDALBOSS_ALL: "勋章战榜",
        GUILD_TRAVEL_WEEK: "师团运输榜-本周",
        GUILD_TRAVEL_LAST_WEEK: "师团运输榜-上周",
        WORLDBOSS_ALL: "世界BOSS伤害榜",
        GVG_SCORE: "GVG积分榜",
        GVG_GUILD_SCORE: "GVG师团积分榜",
        GVG_SERVER_SCORE: "GVG区服积分榜",
        CROSS_PVP_ROLE: "跨服PVP榜-个人",
        CROSS_PVP_SERVER: "跨服PVP榜-区服",
        TEXAS_ALL: "德州榜",
        MOUNTAIN_HERO: "爬塔榜-英雄",
        MOUNTAIN_WARSHIP: "爬塔榜-战舰",
        TEST_WORLD_ALL: "测试榜",
    }

    @classmethod
    def get_name(cls, rank_id):
        """根据榜单ID返回中文名，找不到就返回ID数字"""
        return cls.NAME_MAP.get(rank_id, f"未知榜单({rank_id})")



class RankAPI(BaseAPI):
    """排行榜业务API"""

    def get_ranking_list(self, rank_ids):
        """批量查询多个榜单的第一名。rank_ids: 榜单ID列表"""
        query = C2S_RANKING_LIST()
        for rid in rank_ids:
            query.rank_ids.append(rid)

        resp = self.request("C2S_RANKING_LIST", query, S2C_RANKING_LIST, "查询榜单列表没收到响应")
        return resp.infos

    def get_ranking_info(self, rank_type):
        """查询单个榜单完整排行。返回 (排行列表, 我的排名, 我的分数)"""
        query = C2S_RANKING_INFO()
        query.rank_type = rank_type

        resp = self.request("C2S_RANKING_INFO", query, S2C_RANKING_INFO, "查询榜单详情没收到响应")
        return resp.ranking_info, resp.mine_rank, resp.mine_score




