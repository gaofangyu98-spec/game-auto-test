"""任务业务 API：查询任务列表（主线/日常/成就）。"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))

# noinspection PyUnresolvedReferences
from proto.msg_task_pb2 import C2S_TASK_LIST, S2C_TASK_LIST
from api.base_api import BaseAPI

# 任务类型
class TaskType:
    MAIN = 1    # 主线任务
    DAILY = 2   # 日常任务
    ACHIEVEMENT = 3  # 成就任务

class TaskAPI(BaseAPI):
    """任务业务API"""

    def get_task_list(self, task_type):
        """
        查询任务列表。
        task_type: TaskType.MAIN / DAILY / ACHIEVEMENT
        返回: (任务列表, 活跃度)
        """
        query = C2S_TASK_LIST()
        query.type = task_type

        resp = self.request("C2S_TASK_LIST", query, S2C_TASK_LIST, "查询任务列表没收到响应")
        return resp.tasks, resp.activity