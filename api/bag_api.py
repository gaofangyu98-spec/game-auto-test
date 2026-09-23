"""背包业务 API：查询背包、对比背包变化。"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))

# noinspection PyUnresolvedReferences
from proto.msg_item_pb2 import C2S_BACKPACK, S2C_BACKPACK
from api.base_api import BaseAPI


class BagAPI(BaseAPI):
    """
    背包业务API：查询背包、使用道具
    持有 GameClient 实例，用它做底层通信
    """

    def get_backpack(self, backpack_id):
        """
        查询背包

        backpack_id: 背包ID，默认1
        返回: {道具id: 数量} 字典，比如 {100000003: 1, 100201005: 3}
        """
        # 1. 构造查询消息（repeated 字段用 append）
        query = C2S_BACKPACK()
        query.backpack_id.append(backpack_id)

        # 2. 发送 + 收响应 + 解码（模板自动跳过心跳/同步推送，识别 S2C_ERROR）
        resp = self.request("C2S_BACKPACK", query, S2C_BACKPACK, "查询背包没收到响应")

        # 3. 转成字典，方便对比
        result = {}
        for bp in resp.backpacks:
            for item in bp.items:
                result[item.id] = item.count
        return result

    def compare_backpack(self, before, after):
        """
        对比两个背包的变化
        before: 购买前的背包字典 {道具id: 数量}
        after: 购买后的背包字典 {道具id: 数量}
        返回: [(道具id, 旧数量, 新数量, 变化量), ...] 只返回有变化的道具
        """
        changes = []
        all_ids = set(before.keys() | after.keys())
        for item_id in sorted(all_ids):
            old_count = before.get(item_id, 0)
            new_count = after.get(item_id, 0)
            if old_count != new_count:
                diff = new_count - old_count
                changes.append((item_id, old_count, new_count, diff))
                print(f" 道具 {item_id} : {old_count} -> {new_count} (+{diff})")

        return changes
