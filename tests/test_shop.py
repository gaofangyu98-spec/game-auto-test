"""商店用例：查商店、买礼包、购买前后对比背包。

断言策略（重点看 test_buy_and_check_backpack）：
  - 这类"花钱买东西"的用例，光看服务器返回 code=0 不够，要验证道具真到账；
  - 做法是：买前查一次背包 -> 购买 -> 买后再查一次背包 -> 用
    BagAPI.compare_backpack 对比两份背包字典，看哪些道具数量增加了；
  - 只要有道具数量上涨就说明到账成功（有些道具走邮件发，这时背包不变，
    用例里也对此留了提示）。
"""
from config.settings import ACCOUNT_GENERAL, DEFAULT_SERVER_ID, SHOP_ID
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))

from client.game_client import GameClient
from api.shop_api import ShopAPI
from api.bag_api import BagAPI

@pytest.mark.smoke
def test_query_shop(game_client):
    """测试：查询礼包商店"""
    shop = ShopAPI(game_client)

    resp = shop.query_shop(shop_type=SHOP_ID,cfg_id=0)

    print(f"\n=====礼包商店（共 {len(resp.infos)} 个商品）=====")
    for i, item in enumerate(resp.infos):
        print(f"  商品{i+1}: conf_id = {item.conf_id}, 剩余 = {item.remain_count}, 已购={item.buy_count}")

    assert len(resp.infos) > 0, "商店没有商品"


def test_buy_gift():
    """测试: 购买礼包"""
    client = GameClient()
    client.login(ACCOUNT_GENERAL, DEFAULT_SERVER_ID)
    shop = ShopAPI(client)

    resp, success = shop.buy_gift(
        shop_id=502,
        conf_id=50208,
        buy_count=1,
        cfg_id=0,
        source=0
    )

    print(f"\n=====购买结果=====")
    print(f"  结果码: {resp.code} (0=成功, 1=失败)")
    print(f"  获得道具数量: {len(resp.items)}")
    for i, item in enumerate(resp.items):
        print(f"    道具{i + 1}: id={item.id}, 数量={item.count}")
    if resp.info:
        print(f"  商品剩余次数: {resp.info.remain_count}")

    assert success, f"购买失败, code = {resp.code}"
    client.close()

def test_buy_and_check_backpack():
    """测试：购买前后对比背包，验证道具到账"""
    client = GameClient()
    client.login(ACCOUNT_GENERAL, DEFAULT_SERVER_ID)
    shop = ShopAPI(client)
    bag = BagAPI(client)

    #查看背包
    before = bag.get_backpack(backpack_id=1)
    print(f"购买前: {len(before)} 种道具 !")

    #购买
    resp, success = shop.buy_gift(
        shop_id=502,
        conf_id=50208,
        buy_count=1,
        cfg_id=0,
        source=0
    )
    assert success, "购买失败 !"

    #购买后查背包
    after = bag.get_backpack(backpack_id=1)
    print(f"购买后: {len(before)} 种道具 !")

    #对比变化
    print(f"\n=======道具变化=======")
    changes = bag.compare_backpack(before, after)

    #打印买到的道具ID
    print(f"\n=====本次购买获得道具=====")
    for item_id, old_count, new_count, diff in changes:
        if diff > 0:
            print(f" 道具ID: {item_id}, 数量: +{diff} (从 {old_count} 变成 {new_count})")

    #断言
    assert len(changes) > 0, "购买后背包没有变化，道具可能通过邮件发放"

    client.close()
