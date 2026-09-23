"""
角色信息测试
"""
from config.settings import DEFAULT_SERVER_ID, ACCOUNT_GENERAL
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client.game_client import GameClient
from api.role_api import RoleAPI

@pytest.mark.smoke
def test_query_role_info(game_client):
    """测试：查询角色信息"""
    role_api = RoleAPI(game_client)
    resp = role_api.get_role_info()

    assert resp is not None, "角色信息为空"
    assert resp.id > 0, "角色ID不合法"
    assert resp.name != "", "角色名字为空"
    assert resp.lv > 0, "角色等级不合法"
    assert resp.vipLv >= 0, "VIP等级不合法"
