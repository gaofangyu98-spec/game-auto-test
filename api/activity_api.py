"""活动业务 API：查活动列表、查节日福袋、购买福袋(充值下单)。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))
# noinspection PyUnresolvedReferences
from proto.msg_ai_activity_pb2 import (
    C2S_AI_ACTIVITY_LIST,
    S2C_AI_ACTIVITY_LIST
)

# noinspection PyUnresolvedReferences
from proto.msg_ai_activity_pb2 import (
    C2S_AI_ACTIVITY_HOLIDAY_LUCKY_BAG_INFO,
    S2C_AI_ACTIVITY_HOLIDAY_LUCKY_BAG_INFO
)

# noinspection PyUnresolvedReferences
from proto.msg_recharge_pb2 import (
    C2S_RECHARGE_CREATE_ORDER,
    S2C_RECHARGE_CREATE_ORDER,
    # S2C_RECHARGE_DELIVE 是购买后的发货推送消息，此处先导入备用，buy 流程暂未接收
    S2C_RECHARGE_DELIVE
)

from api.base_api import BaseAPI

class ActivityAPI(BaseAPI):
    """活动业务API：查活动列表、查活动详情、买礼包"""

    # ==================== 查询活动列表 ====================

    def get_activity_list(self):
        """
        查询所有当前开启的活动列表
        返回: S2C_AI_ACTIVITY_LIST 对象
        """
        query = C2S_AI_ACTIVITY_LIST()
        resp = self.request(
            "C2S_AI_ACTIVITY_LIST", query, S2C_AI_ACTIVITY_LIST,
            "查询活动列表没有收到响应 !"
        )
        return resp

    # ==================== 打印活动列表（调试用） ====================

    def print_activity_list(self):
        """打印所有活动列表，看看有哪些活动开启了"""
        resp = self.get_activity_list()

        print(f"\n============当前开启的活动============")

        # 1. 冲榜
        if resp.ai_activity_rank_list:
            print(f"\n【冲榜】共 {len(resp.ai_activity_rank_list)} 个")
            for i, act in enumerate(resp.ai_activity_rank_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 2. 限时充值
        if resp.ai_activity_limit_recharge_list:
            print(f"\n【限时充值】共 {len(resp.ai_activity_limit_recharge_list)} 个")
            for i, act in enumerate(resp.ai_activity_limit_recharge_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 3. 限时礼包
        if resp.ai_activity_limit_gift_list:
            print(f"\n【限时礼包】共 {len(resp.ai_activity_limit_gift_list)} 个")
            for i, act in enumerate(resp.ai_activity_limit_gift_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 4. 转盘
        if resp.ai_activity_turntable_list:
            print(f"\n【转盘】共 {len(resp.ai_activity_turntable_list)} 个")
            for i, act in enumerate(resp.ai_activity_turntable_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 5. 钻石转盘
        if resp.ai_activity_turntable_dia_list:
            print(f"\n【钻石转盘】共 {len(resp.ai_activity_turntable_dia_list)} 个")
            for i, act in enumerate(resp.ai_activity_turntable_dia_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 6. 战令
        if resp.ai_activity_battlepass_list:
            print(f"\n【战令】共 {len(resp.ai_activity_battlepass_list)} 个")
            for i, act in enumerate(resp.ai_activity_battlepass_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 7. 节日战令
        if resp.ai_activity_battlepass_two_list:
            print(f"\n【节日战令】共 {len(resp.ai_activity_battlepass_two_list)} 个")
            for i, act in enumerate(resp.ai_activity_battlepass_two_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 8. 基金
        if resp.ai_activity_fund_list:
            print(f"\n【基金】共 {len(resp.ai_activity_fund_list)} 个")
            for i, act in enumerate(resp.ai_activity_fund_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 9. 天数通行证
        if resp.ai_activity_daypass_list:
            print(f"\n【天数通行证】共 {len(resp.ai_activity_daypass_list)} 个")
            for i, act in enumerate(resp.ai_activity_daypass_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 10. 七日签到
        if resp.ai_activity_sign7day_list:
            print(f"\n【七日签到】共 {len(resp.ai_activity_sign7day_list)} 个")
            for i, act in enumerate(resp.ai_activity_sign7day_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 11. 充值双倍
        if resp.ai_activity_recharge_double_list:
            print(f"\n【充值双倍】共 {len(resp.ai_activity_recharge_double_list)} 个")
            for i, act in enumerate(resp.ai_activity_recharge_double_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 12. 招财猫
        if resp.ai_activity_lucky_cat_list:
            print(f"\n【招财猫】共 {len(resp.ai_activity_lucky_cat_list)} 个")
            for i, act in enumerate(resp.ai_activity_lucky_cat_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 13. 跨服特惠礼包
        if resp.ai_activity_limit_gift_cross_list:
            print(f"\n【跨服特惠礼包】共 {len(resp.ai_activity_limit_gift_cross_list)} 个")
            for i, act in enumerate(resp.ai_activity_limit_gift_cross_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 14. 跨服冲榜
        if resp.ai_activity_rank_cross_list:
            print(f"\n【跨服冲榜】共 {len(resp.ai_activity_rank_cross_list)} 个")
            for i, act in enumerate(resp.ai_activity_rank_cross_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 15. 蛇形礼包
        if resp.ai_activity_snake_gift_list:
            print(f"\n【蛇形礼包】共 {len(resp.ai_activity_snake_gift_list)} 个")
            for i, act in enumerate(resp.ai_activity_snake_gift_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 16. 幸运棋牌
        if resp.ai_activity_lucky_chess_list:
            print(f"\n【幸运棋牌】共 {len(resp.ai_activity_lucky_chess_list)} 个")
            for i, act in enumerate(resp.ai_activity_lucky_chess_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 17. 幸运福袋
        if resp.ai_activity_lucky_bag_list:
            print(f"\n【幸运福袋】共 {len(resp.ai_activity_lucky_bag_list)} 个")
            for i, act in enumerate(resp.ai_activity_lucky_bag_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 18. 金字塔
        if resp.aiActivityPyramidList:
            print(f"\n【金字塔】共 {len(resp.aiActivityPyramidList)} 个")
            for i, act in enumerate(resp.aiActivityPyramidList):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 19. 节日活动（游园会）
        if resp.aiActivityHolidayList:
            print(f"\n【节日活动（游园会）】共 {len(resp.aiActivityHolidayList)} 个")
            for i, act in enumerate(resp.aiActivityHolidayList):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 20. 小游戏
        if resp.aiActivityMinigameList:
            print(f"\n【小游戏】共 {len(resp.aiActivityMinigameList)} 个")
            for i, act in enumerate(resp.aiActivityMinigameList):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 21. 同乐礼包
        if resp.ai_activity_tongle_gift_list:
            print(f"\n【同乐礼包】共 {len(resp.ai_activity_tongle_gift_list)} 个")
            for i, act in enumerate(resp.ai_activity_tongle_gift_list):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        # 22. 冲榜礼包
        if resp.aiActivityRushGiftList:
            print(f"\n【冲榜礼包】共 {len(resp.aiActivityRushGiftList)} 个")
            for i, act in enumerate(resp.aiActivityRushGiftList):
                print(f"  活动{i + 1}: id={act.id}, 开始={act.start_time}, 结束={act.end_time}")

        return resp
