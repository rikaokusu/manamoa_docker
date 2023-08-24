from accounts.models import User
from accounts.models import Company
from datetime import datetime,timezone
from django.contrib import messages
from django.shortcuts import redirect

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def check_session(self, request, instance):

    print("りくえすと２", request)


    # GET時のみ動作
    if request.method == "GET":

        # 変更フラグの存在を確認
        if instance.version:
            id = str(instance.id)

            # 自分自身の場合
            if instance.change_user == str(self.request.user.id):
                messages.error(request, '変更中のセッションが残っています。セッションを破棄して新たに変更しますか？<div type="button" id="okBtn" data-id=' + '"' + id + '"' + ' data-url="update_profile" class="my-btn my-btn-egypt-1 my-btn-s my-btn-w5 ml-1 mr-1">はい</div><div type="button" data-url="update_profile" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">いいえ</div>')
                print("うごいているとおもうけど")
                return redirect('accounts:companyprofile')
                print("うごいているとおもうけど２")

            # 他ユーザの場合
            else:
                user = User.objects.filter(id=instance.change_user).first()

                change_user = str(user.display_name)

                timestamp = instance.version
                now = datetime.now(timezone.utc)

                diff = now - timestamp

                # 30分以上立っている場合
                if diff.seconds >= 1800:

                    messages.error(request, '' + change_user + ' さんが変更中です。セッションを破棄して新たに変更しますか？<div type="button" id="okBtn" data-id=' + '"' + id + '"' + ' data-url="update_profile" class="my-btn my-btn-egypt-1 my-btn-s my-btn-w5 ml-1 mr-1">はい</div><div type="button" data-url="update_profile" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">いいえ</div>')
                    return redirect('accounts:companyprofile')

                # 30分未満の場合
                else:
                    messages.error(request, '' + change_user + ' さんが変更中です。<div type="button" id="okBtn" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">閉じる</div>')
                    return redirect('accounts:companyprofile')


        else:

            print("うごいてない？")
            # 変更フラグをセット
            instance.version = datetime.now()
            # 変更者のIDをセット
            instance.change_user =  self.request.user.id
            # 保存
            instance.save()




def custom_send_mail(self, subject, message, recipient_list, fail_silently=False, ):
    CUSTOM_EMAIL_HOST = self.request.user.company.email_host
    CUSTOM_EMAIL_PORT = self.request.user.company.port
    CUSTOM_EMAIL_HOST_USER = self.request.user.company.host_user # Gmailのアカウント*
    CUSTOM_EMAIL_HOST_PASSWORD = self.request.user.company.host_password # Gmailの2段階認証用のパスワード*
    CUSTOM_EMAIL_USE_TLS = True
    CUSTOM_EMAIL_FROM_ADDRESS = self.request.user.company.from_address


    # MIMEの作成
    msg = MIMEText(message, "plain")
    msg["Subject"] = subject
    msg["To"] = recipient_list
    msg["From"] = CUSTOM_EMAIL_FROM_ADDRESS


    # メール送信処理
    server = ""

    if self.request.user.company.smtp_connection_type == "1": # なし
        server = smtplib.SMTP(CUSTOM_EMAIL_HOST, CUSTOM_EMAIL_PORT)

    elif self.request.user.company.smtp_connection_type == "2": # STARTTLS
        server = smtplib.SMTP(CUSTOM_EMAIL_HOST, CUSTOM_EMAIL_PORT)
        server.starttls()
        server.login(CUSTOM_EMAIL_HOST_USER, CUSTOM_EMAIL_HOST_PASSWORD)
        print("うごいている２？")

    elif self.request.user.company.smtp_connection_type == "3": # SSL/TLS
        server = smtplib.SMTP_SSL(CUSTOM_EMAIL_HOST, CUSTOM_EMAIL_PORT, context=ssl.create_default_context())
        server.login(CUSTOM_EMAIL_HOST_USER, CUSTOM_EMAIL_HOST_PASSWORD)
        print("うごいている３？")


    server.send_message(msg)
    server.quit()


