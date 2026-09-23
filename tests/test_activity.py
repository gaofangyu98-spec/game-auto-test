"""活动查询用例：登录后打印当前开启的所有活动。"""
from config.settings import ACCOUNT_GENERAL, DEFAULT_SERVER_ID
from api.activity_api import ActivityAPI
from client.game_client import GameClient
import pytest

@pytest.mark.smoke
def test_query_activity(game_client):
    """测试：查询当前开启的活动列表"""
    activity_api = ActivityAPI(game_client)

    # 查询并打印所有活动
    resp = activity_api.get_activity_list()

    # 收集所有活动
    all_activities = []
    for field_name in dir(resp):
        if field_name.endswith('_list') or field_name.endswith('List'):
            field_value = getattr(resp, field_name)
            if hasattr(field_value, '__len__') and len(field_value) > 0:
                all_activities.extend(field_value)

    # 断言
    assert len(all_activities) > 0, "没有任何活动开启"
    for act in all_activities:
        assert act.id > 0, f"活动ID不合法: {act.id}"
        assert act.start_time < act.end_time, f"活动 {act.id} 时间不合法"
