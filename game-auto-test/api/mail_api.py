"""邮件业务 API：查邮件列表、领取附件、删除邮件。

所有业务方法都走 BaseAPI.request 模板：
  构造 C2S_xxx -> 发送 -> 精确等 S2C_xxx 响应 -> 解码。
底层收发、跳过心跳/同步推送、识别 S2C_ERROR 全由基类和 GameClient 处理。
"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "proto"))

# noinspection PyUnresolvedReferences
from proto.msg_mail_pb2 import (
    C2S_MAIL, S2C_MAIL,
    C2S_MAIL_ATTACHMENTS, S2C_MAIL_ATTACHMENTS,
    C2S_MAIL_DEL, S2C_MAIL_DEL
)

from api.base_api import BaseAPI


class MailAPI(BaseAPI):
    """邮件业务API：查邮件、领附件、删邮件"""

    # ==================== 查询邮件列表 ====================
    def get_mail_list(self):
        """
        查询邮件列表
        返回: S2C_MAIL 对象（里面有 mails 邮件列表）
        """
        query = C2S_MAIL()
        resp = self.request("C2S_MAIL", query, S2C_MAIL, "查询邮件没有收到响应")
        return resp

    # ==================== 领取邮件附件 ====================
    def get_attachments(self, mail_ids):
        """
        领取邮件附件
        mail_ids: 邮件ID列表，比如 [123, 456]
        """
        req = C2S_MAIL_ATTACHMENTS()
        for mid in mail_ids:
            req.ids.append(mid)

        # 响应是空消息（无字段），收到即代表服务器已受理；收不到会断言失败
        self.request("C2S_MAIL_ATTACHMENTS", req, S2C_MAIL_ATTACHMENTS, "领取附件没有收到响应")
        print(f"已领取 {len(mail_ids)} 封邮件的附件")

    # ==================== 删除邮件 ====================
    def delete_mail(self, mail_ids):
        """
        删除邮件
        mail_ids: 邮件ID列表
        """
        req = C2S_MAIL_DEL()
        for mid in mail_ids:
            req.ids.append(mid)

        # 响应是空消息（无字段），收到即代表服务器已受理；收不到会断言失败
        self.request("C2S_MAIL_DEL", req, S2C_MAIL_DEL, "删除邮件没有收到响应")
        print(f"已删除 {len(mail_ids)} 封邮件 !")

    # ==================== 便捷方法：打印邮件列表 ====================

    def print_mail_list(self):
        """打印邮件列表（调试用）"""
        resp = self.get_mail_list()
        print(f"\n=====邮件列表（共 {len(resp.mails)} 封）=====")
        for i, mail in enumerate(resp.mails):
            print(f"\n 邮件 {i+1} :")
            print(f"    mail_id: {mail.mail_id}")
            print(f"    类型: {mail.type}")
            print(f"    标题: {mail.mail_title}")
            print(f"    已读: {mail.is_read}")
            print(f"    附件已领: {mail.is_item_got}")
            print(f"    附件数量: {len(mail.items)}")
            for j, item in enumerate(mail.items):
                print(f"    附件 {j+1}： 道具 id = {item.id}, 数量 = {item.num}")

        return resp.mails
