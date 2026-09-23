"""邮件用例：查邮件、领附件、删邮件。

这一层是 pytest 测试用例，组织方式说明：
  - 这里暂时没有用 @pytest.fixture，每个用例都自己走一遍
      client = GameClient() -> client.login(账号, 服) -> 调 API -> client.close()；
  - pytest 只要看到函数名以 test_ 开头就会自动执行；
  - 断言策略：先调 API 拿到数据，再用 assert 判断结果是否符合预期
    （例如删除后确认邮件ID不在剩余列表里）。
真实项目里通常会把"登录+关闭"抽成一个 scope 级 fixture 复用，这里为了
直观每个用例都写全，方便初学者看完整流程。
"""

from config.settings import DEFAULT_SERVER_ID, ACCOUNT_GENERAL
from api.mail_api import MailAPI
from client.game_client import GameClient
import pytest

@pytest.mark.smoke
def test_query_mail(game_client):
    """测试：查询邮件列表"""
    mail_api = MailAPI(game_client)

    resp = mail_api.get_mail_list()

    # 断言1：邮件列表是列表类型（protobuf 的 repeated 字段）
    assert hasattr(resp.mails, '__len__'), "邮件列表格式错误"

    for mail in resp.mails:
        assert mail.mail_id > 0, f"邮件ID不合法: {mail.mail_id}"
        assert mail.mail_title != "", f"邮件 {mail.mail_id} 标题为空"
        assert mail.create_ts > 0, f"邮件 {mail.mail_id} 创建时间不合法"


def test_get_attachments():
    """测试：领取未领附件的邮件"""
    client = GameClient()
    client.login(ACCOUNT_GENERAL, DEFAULT_SERVER_ID)
    mail_api = MailAPI(client)

    resp = mail_api.get_mail_list()

    #找出未领取的
    ungot_mails = []  # 准备一个空列表
    for m in resp.mails:  # 遍历每一封邮件
        if not m.is_item_got:  # 如果这封邮件的附件没领
            ungot_mails.append(m.mail_id)  # 就把邮件ID加到列表里
    print(f"\n未领取的邮件 : {len(ungot_mails)} 封 !")

    if ungot_mails:
        #领取
        mail_api.get_attachments(ungot_mails)
        # 领取后再查一次，验证附件已领
        resp_after = mail_api.get_mail_list()
        for m in resp_after.mails:
            if m.mail_id in ungot_mails:
                assert m.is_item_got, f"邮件 {m.mail_id} 附件领取后状态未更新"
        print("领取成功 !")
    else:
        print("没有未领附件的邮件，跳过领取 !")

    client.close()

def test_delete_mail():
    """测试：删除已领附件的邮件"""
    client = GameClient()
    client.login(ACCOUNT_GENERAL, DEFAULT_SERVER_ID)
    mail_api = MailAPI(client)

    resp = mail_api.get_mail_list()
    print(f"删除前邮件数量: {len(resp.mails)}")

    # 2. 找出附件已领的邮件（只删已领的，防止删了没领的）
    got_mails = []
    for m in resp.mails:
        if m.is_item_got:
            got_mails.append(m.mail_id)
    print(f"附件已领的邮件: {len(got_mails)} 封")

    if got_mails:
        mail_api.delete_mail(got_mails)
        print(f"删除成功 !")

        resp1 = mail_api.get_mail_list()
        remaining_ids = []
        for m in resp1.mails:
            if m.is_item_got:
                remaining_ids.append(m.mail_id)
        print(f"删除后邮件数量: {len(resp1.mails)} 封")

        for mid in got_mails:
            assert mid not in remaining_ids, f"邮件 {mid} 没有被删除"
        print("删除验证成功!")
    else:
        print("没有已领附件的邮件，跳过删除")

    client.close()
