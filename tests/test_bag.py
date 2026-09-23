"""背包用例：查询背包并校验道具数量。"""
from config.settings import DEFAULT_SERVER_ID, ACCOUNT_GENERAL
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))

from client.game_client import GameClient
from api.bag_api import BagAPI

@pytest.mark.smoke
def test_query_backpack(game_client):
    """测试：查询背包"""
    bag = BagAPI(game_client)

    # 只看这些道具ID
    watch_ids = [ ]

    count = 1

    backpack = bag.get_backpack(count)

    print(f"\n=====背包（共 {len(backpack)} 种道具）=====")
    for item_id, count in backpack.items():
        print(f"  道具 {item_id} : {count} 个")

    print(f"\n=====背包（指定道具，共 {len(watch_ids)} 个）=====")
    for item_id in watch_ids:
        count = backpack.get(item_id, 0)  # 没有就显示0
        print(f"  道具 {item_id} : {count} 个")

    assert len(backpack) > 0, "背包为空......"
