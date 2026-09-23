"""登录用例：HTTP登录+连接+鉴权全流程是否成功。"""
from config.settings import ACCOUNT_GENERAL, DEFAULT_SERVER_ID
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client.game_client import GameClient

@pytest.mark.smoke
def test_login(game_client):
    """测试：登录成功"""
    assert game_client.cuid == ACCOUNT_GENERAL
    assert game_client.ws is not None
