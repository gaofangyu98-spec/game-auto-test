"""任务用例：查询主线/日常/成就任务列表。"""
from api.task_api import TaskAPI, TaskType
import pytest


@pytest.mark.smoke
def test_query_task_list(game_client):
    """测试：查询主线/日常/成就任务列表"""
    task_api = TaskAPI(game_client)

    # 先查完所有任务，结果存下来
    results = {}
    for task_type, name in [(TaskType.MAIN, "主线"), (TaskType.DAILY, "日常"), (TaskType.ACHIEVEMENT, "成就")]:
        tasks, activity = task_api.get_task_list(task_type)
        results[name] = {"tasks": tasks, "activity": activity}

    # 统一打印
    print("\n" + "-" * 40)
    for name, data in results.items():
        tasks = data["tasks"]
        activity = data["activity"]

        print(f"\n【{name}任务】共 {len(tasks)} 个", end="")
        if name == "日常":
            print(f"，活跃度 {activity}", end="")
        print()

        assert len(tasks) > 0, f"{name}任务列表为空"

        for task in tasks[:3]:
            status = "已完成" if task.is_finish else "进行中"
            print(f"  任务{task.task_id} | 进度={task.progress} | {status}")

    print("\n" + "-" * 40)
