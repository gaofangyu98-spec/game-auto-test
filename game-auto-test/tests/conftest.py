import pytest
from config.settings import ACCOUNT_GENERAL, DEFAULT_SERVER_ID
from client.game_client import GameClient

@pytest.fixture(scope="session")
def game_client():
    """
    全局登录 fixture：整个测试会话只登录一次，所有用例共享。

    scope="session"：整个 pytest 运行期间只创建一次
    yield 之前：登录（setup）
    yield 之后：关闭连接（teardown）
    """
    client = GameClient()
    client.login(ACCOUNT_GENERAL, DEFAULT_SERVER_ID)
    yield client
    client.close()