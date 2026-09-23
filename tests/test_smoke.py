"""冒烟测试集合：一次登录，串6个核心模块的查询。

这是 CI 里每次提交必跑的用例，验证核心链路通不通。
只做查询，不做修改（购买/删除/领取），保证可以反复跑。
"""

import pytest
from api.bag_api import BagAPI
from api.role_api import RoleAPI
from api.mail_api import MailAPI
from api.shop_api import ShopAPI
from api.activity_api import ActivityAPI
from config.settings import SHOP_ID


@pytest.mark.smoke
def test_smoke_all(game_client):
    """冒烟测试：登录后依次查询背包/角色/邮件/商店/活动"""

    # 1. 背包查询
    print("\n============ 1. 背包查询 ============")
    bag = BagAPI(game_client)
    backpack = bag.get_backpack(backpack_id=1)
    print(f"背包共 {len(backpack)} 种道具")
    assert len(backpack) > 0, "背包为空"

    # 2. 角色查询
    print("\n============ 2. 角色查询 ============")
    role = RoleAPI(game_client)
    role_info = role.get_role_info()
    print(f"角色: {role_info.name}, 等级: {role_info.lv}, VIP: {role_info.vipLv}")
    assert role_info.id > 0, "角色ID不合法"
    assert role_info.name != "", "角色名字为空"

    # 3. 邮件查询
    print("\n============ 3. 邮件查询 ============")
    mail = MailAPI(game_client)
    mail_list = mail.get_mail_list()
    print(f"邮件共 {len(mail_list.mails)} 封")
    for m in mail_list.mails:
        assert m.mail_id > 0, f"邮件ID不合法: {m.mail_id}"

    # 4. 商店查询
    print("\n============ 4. 商店查询 ============")
    shop = ShopAPI(game_client)
    shop_info = shop.query_shop(shop_type=SHOP_ID, cfg_id=0)
    print(f"商店共 {len(shop_info.infos)} 个商品")
    assert len(shop_info.infos) > 0, "商店没有商品"

    # 5. 活动查询
    print("\n============ 5. 活动查询 ============")
    activity = ActivityAPI(game_client)
    activity_list = activity.get_activity_list()
    # 收集所有活动（动态遍历22个列表字段）
    all_activities = []
    for field_name in dir(activity_list):
        if field_name.endswith('_list') or field_name.endswith('List'):
            field_value = getattr(activity_list, field_name)
            if hasattr(field_value, '__len__') and len(field_value) > 0:
                all_activities.extend(field_value)
    print(f"当前开启的活动共 {len(all_activities)} 个")
    assert len(all_activities) > 0, "没有任何活动开启"

    print("\n============ 冒烟测试全部通过 ============")
