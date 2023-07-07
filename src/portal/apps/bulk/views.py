from django.shortcuts import render

# インポート
import csv
import io
import uuid
import random
import string
import os
from django.views.generic import FormView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import CSVUploadForm, UserDeleteForm
from accounts.models import User, Company, Service,Notification,Read
from contracts.models import Contract, Plan, PaymentMethod, Estimates

# 削除
import fileinput

# バリデーション
from django.db import transaction
from django.db import IntegrityError
from django.http import JsonResponse

# CommonView
from django.views.generic.base import ContextMixin

# エクスポート
from django.http import HttpResponse

# デコレータ
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

# 多言語化
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

# 設定ファイル読み込み
from django.conf import settings

from django.db.models import Q
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta
import pytz

# 全てで実行させるView
class CommonView(ContextMixin):

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user
        not_paymented = Contract.objects.filter(company=current_user.company, payment__is_paymented=False)
        context["not_paymented"] = not_paymented
        url_name = self.request.resolver_match.url_name
        app_name = self.request.resolver_match.app_name
        #infomation用
        today = datetime.now(timezone.utc)
        all_informations = Notification.objects.filter(start_date__lte = today)
        notice_informations = Notification.objects.filter(Q(target_user_id = None)|Q(target_user_id = current_user),Q(category = 'メッセージ')|Q(category = 'お知らせ'),start_date__lte = today).distinct().values()
        maintenance_informations = Notification.objects.filter(Q(target_user_id = None)|Q(target_user_id = current_user),start_date__lte = today, category__contains = 'メンテナンス').distinct().values()
        read = Read.objects.filter(read_user=current_user).count()
        read_info = Read.objects.filter(read_user=current_user).values_list('notification_id', flat=True)
        
        if read > 0:
            info_all = Notification.objects.filter(Q(target_user_id = None)|Q(target_user_id = current_user),start_date__lte = today).distinct().count()
            no_read = info_all - read
        else:
            no_read = Notification.objects.filter(Q(target_user_id = None)|Q(target_user_id = current_user),start_date__lte = today).distinct().count()
        
        if no_read > 99 :
            context["no_read"] = "99+"

        else:
            context["no_read"] = no_read
        
        context["read_info"] = read_info
        context["all_informations"] = all_informations
        context["maintenance_informations"] = maintenance_informations
        context["notice_informations"] = notice_informations

        context["url_name"] = url_name
        context["app_name"] = app_name
        return context

class InvalidColumnsExcepion(Exception):
    """CSVの列が足りなかったり多かったりしたらこのエラー"""
    pass

class InvalidSourceExcepion(Exception):
    """CSVの読みとり中にUnicodeDecordErrorが出たらこのエラー"""
    pass

class InvalidMustColumnsExcepion(Exception):
    """必須カラムが漏れていたらエラー"""
    pass

class InvalidNonExistsExcepion(Exception):
    """ユーザーが存在しないエラー"""
    pass

class LoggedInUserException(Exception):
    """ログイン中のユーザーが削除されようとしたらエラー""" 
    pass

"""
ホーム画面
"""

class HomeTemplateView(LoginRequiredMixin,TemplateView, CommonView):
    template_name = 'bulk/home/home.html'


"""
カラム名と数
1.メールアドレス(必須)※ドメイン不要
2.パスワード(必須)
3.姓（必須）
4.名（必須）
5.ミドルネーム
6.ふりがな(姓)
7.ふりがな(名)
8.ふりがな(ミドルネーム)
9.利用サービス(スペースで区切る)
10.説明
"""

"""
インポート実行
"""
class AjaxPostImport(View, CommonView):
    template_name = 'bulk/ajax_import.html'
    number_of_columns = 10  # 列の数を定義しておく。各行の列がこれかどうかを判断する

    def save_csv(self, random_name):
            #ランダムファイル名を取得
            with open(random_name,'r') as csvfile:
            # ヘッダーを読み飛ばす
                header = next(csvfile)
                reader = csv.reader(csvfile)

                i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為

                try:
                    # iは、現在の行番号。エラーの際に補足情報として使う
                    for i, row in enumerate(reader, 1):
                        # 列数が違う場合
                        if len(row) != self.number_of_columns:
                            raise InvalidColumnsExcepion('{0}行目 項目数エラー。本来の列数: {1}, {0}行目の列数: {2} ファイル名:{3}'.format(i, self.number_of_columns, len(row), csvfile))

                        # 必須カラムのチェック
                        for num in range(0, 3):
                            if not row[num]:
                                raise InvalidMustColumnsExcepion('{0}行目 {1}列目の必須項目がありません。ファイル名:{2}'.format(i, num+1, csvfile))
                        suser = self.request.user

                        user = User.objects.create(email=row[0])
                        user.set_password(row[1])
                        user.last_name = row[2]
                        user.first_name = row[3]
                        user.middle_name = row[4]
                        if row[2] and row[3] and row[4]: 
                            user.display_name = row[2] + ' ' + row[4] + ' ' + row[3]
                        elif row[2] and row[3]:
                            user.display_name = row[2] + ' ' + row[3]
                        user.p_last_name = row[5]
                        user.p_first_name = row[6]
                        user.p_middle_name = row[7]
                        if row[5] and row[6] and row[7]: 
                            user.p_display_name = row[5] + ' ' + row[7] + ' ' + row[6]
                        elif row[5] and row[6]:
                            user.p_display_name = row[5] + ' ' + row[6]
                        company_id = suser.company.id
                        user.company = suser.company
                        # 利用サービスの値をリストに変換
                        services = row[8].split()
                        user.service.set(Service.objects.filter(name__in=services))
                        user.description = row[9]
                        user.save()

                except UnicodeDecodeError:
                    raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csvfile))

                except IntegrityError as e:
                    raise IntegrityError('{0}行目 エラー。{1}が重複しています。 ファイル名:{2}'.format(i, row[0], csvfile))
            #登録終了後仮ファイル消去
            os.remove(random_name)

    def post(self, request):
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(request.POST.get('random_file'))
        #今のところは、この2つのエラーは同様に対処
        except InvalidSourceExcepion as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidColumnsExcepion as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        except IntegrityError as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidMustColumnsExcepion as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        else:
            data = {
                'messages2': _("ユーザーの一括登録が完了しました。")
            }
        return JsonResponse(data)


from django.core.files.storage import FileSystemStorage

"""
インポートのテスト
"""
class TestPostImport(FormView, CommonView, LoginRequiredMixin):
    template_name = 'bulk/import.html'
    form_class = CSVUploadForm
    number_of_columns = 10  # 列の数を定義しておく。各行の列がこれかどうかを判断する

    def save_csv(self, form):
            # アップロードされたファイル名を取得
            csv_file_name = str(form.cleaned_data['file'])
            # csv.readerに渡すため、TextIOWrapperでテキストモードなファイルに変換
            csvfile = io.TextIOWrapper(form.cleaned_data['file'],encoding='utf-8_sig')

            reader = csv.reader(csvfile)
            # ヘッダーを読み飛ばす
            header = next(reader)

            #filedata = str('')

            self.error_list = []
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(reader, 1):
                    # 列数が違う場合
                    if len(row) != self.number_of_columns:
                        # raise InvalidColumnsExcepion(_('列数を正してください。指定の列数：{1} 現在の列数：{2}').format(i, self.number_of_columns, len(row), csv_file_name))
                        raise InvalidColumnsExcepion('{0}行目 項目数エラー。本来の列数: {1}, {0}行目の列数: {2} ファイル名:{3}'.format(i, self.number_of_columns, len(row), csv_file_name))
                    
                    # 必須カラムのチェック
                    for num in range(0, 4):
                        if not row[num]:
                            raise InvalidMustColumnsExcepion(_('{0}行目{1}列目の必須項目が入力されていません。入力しなおしてください。').format(i, num+1, csv_file_name))

                    # 重複チェック
                    is_exist = User.objects.filter(email=row[0]).exists()
                    user = User.objects.filter(email=row[0]).first()

                    if is_exist:
                        self.error_list.append(str(i) + '行目：' + user.email)

                #ランダムな文字列でファイル名を作る
                random_name = ''.join(random.choice(string.ascii_lowercase) for i in range(15)) #15文字ほどの文字列
                fs = FileSystemStorage() #デフォルトのストレージ
                fs.location = './' #ファイルの一時保管場所。現在はpotal配下に
                fs.save(random_name, csvfile) #ランダムな名前のcsvfileとして保存
                self.random_name = random_name
                random_file_dir = os.path.join(fs.location,random_name)
                random_file_name = random_file_dir + '.csv'

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csv_file_name))

    def form_valid(self, form):
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(form)
        # 今のところは、この2つのエラーは同様に対処。
        except InvalidSourceExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidColumnsExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except IntegrityError as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidMustColumnsExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except Exception as e:
           
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        else:
            if len(self.error_list) > 0:
                data = {
                    'messages': _("エラー：すでに登録済みのユーザーとメールアドレスが重複しています。"),
                    'error_list': self.error_list,
                    'judge': _("ERROR")
                }
                #エラー時仮ファイル消去
                os.remove(self.random_name)

            else:
                data = {
                    'messages': _("データ照合完了：登録ボタンを押してください。"),
                    'file_name': self.random_name,
                    'judge': _("SUCCESS")
                }

            return JsonResponse(data)

"""
途中でキャンセル時仮ファイル削除
"""
#登録ファイル削除
def file_delete(request):
    random_file = request.POST.get('random_file')

    try:
        os.remove(random_file)
    except OSError as err:
        pass
    data = {
        "messages3": _('一括登録を中止しました。')
    }

    return JsonResponse(data)
#変更ファイル削除
def efile_delete(request):
    random_file = request.POST.get('random_file')
    try:
        os.remove(random_file)
    except OSError as err:
        pass
    data = {
        "messages3": _('一括変更を中止しました。')
    }

    return JsonResponse(data)

"""
エクスポート
"""
def post_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    # HttpResponseオブジェクトはファイルっぽいオブジェクトなので、csv.writerにそのまま渡せます。
    # BOM
    sio = io.StringIO()
    writer = csv.writer(sio)
    response.write(sio.getvalue().encode('utf_8_sig'))
    writer = csv.writer(response)
    user = request.user

    # ヘッダーの設定

    if translation.get_language() == 'ja':
        writer.writerow(settings.EXPORT_HEADER_JP)

        # CSV行の生成
        for user in User.objects.select_related().filter(company_id__exact=user.company_id,is_rogical_deleted=False).exclude(email__iexact=user.email):
            writer.writerow([user.email, user.last_name, user.first_name, user.middle_name, user.p_last_name, user.p_first_name, user.p_middle_name,  ' '.join([x.name for x in user.service.all()]), user.description])

    else:

        writer.writerow(settings.EXPORT_HEADER_EN)

        # CSV行の生成
        for user in User.objects.select_related().filter(company_id__exact=user.company_id,is_rogical_deleted=False).exclude(email__iexact=user.email):
            writer.writerow([user.email, user.last_name, user.first_name, user.middle_name, user.p_last_name, user.p_first_name, user.p_middle_name,  ' '.join([x.name for x in user.service.all()]), user.description])


    return response

"""
テンプレートダウンロード
"""
def template_download(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template.csv"'
    # HttpResponseオブジェクトはファイルっぽいオブジェクトなので、csv.writerにそのまま渡せます。
    sio = io.StringIO()
    writer = csv.writer(sio)
    response.write(sio.getvalue().encode('utf_8_sig'))
    writer = csv.writer(response)
    # ヘッダーの設定
    writer.writerow(["メールアドレス(必須)","パスワード(必須)","姓(必須)","名(必須)","ミドルネーム","ふりがな(姓)","ふりがな(名)","ふりがな(ミドルネーム)","利用サービス","説明"])
    return response


"""
一括削除
"""
class PostDelete(FormView, CommonView, LoginRequiredMixin):
    template_name = 'bulk/delete.html'
    success_url = reverse_lazy('accounts:home')
    form_class = UserDeleteForm

    def delete_user(self, request):

            # フォームに入力されたIDを取得
            del_email = request.POST.get('id')
            # IDをリストに変換
            email_list = del_email.splitlines()
            print('ログイン中',self.request.user.id)
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(email_list, 1):

                    # 存在確認
                    user = User.objects.filter(email=row,is_rogical_deleted=False)

                    if del_email == self.request.user.id:
                        raise LoggedInUserException('{0}行目 管理ユーザーとしてログイン中です。削除対象から除外してください。')

                    if user.count() == 0:
                        raise InvalidNonExistsExcepion("エラー：存在しないユーザーが含まれています。")
                        self.error_email_list.append(email_list[i - 1])

                    # 削除する
                    delusers = User.objects.filter(email__in = email_list)
                    for deluser in delusers:
                        deluser.is_rogical_deleted = True
                        deluser.save()

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{}行目でデコードに失敗しました。ファイルのエンコーディングや、正しいCSVファイルか確認ください。'.format(i))

    def post(self, request):
        try:
            # 100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.delete_user(request)
        # 今のところは、この2つのエラーは同様に対処します。
        except InvalidSourceExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except LoggedInUserException as e:
            data = {
                'messages': str(e)
            }
        except InvalidNonExistsExcepion as e:
            data = {
                 'messages': str(e)
            }
            return JsonResponse(data, status=500)
        else:
            data = {
                'messages': _("SUCCESS")
            }
            return JsonResponse(data)

"""
一括削除のテスト
"""
class TestPostDelete(FormView, CommonView, LoginRequiredMixin):
    template_name = 'bulk/delete.html'
    success_url = reverse_lazy('accounts:home')
    form_class = UserDeleteForm

    def delete_user(self, request):

            # フォームに入力されたIDを取得
            del_email = request.POST.get('id')
            # IDをリストに変換
            email_list = del_email.splitlines()
            self.error_email_list = []
            print('りすと',email_list)
            print('ゆーざーー',self.request.user.email)

            i = 0  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(email_list):
                    print('削除対象',type(del_email))
                    # print('りすときてる',email_list[i])
                    
                    if email_list[i] == self.request.user.email:
                        print('じぶんが削除対象')

                        self.error_email_list.append(email_list[i - 1])
                        raise LoggedInUserException('ご自身のメールアドレスを削除対象から除外してください。')
                    
                    # 存在確認
                    user = User.objects.filter(email=row,is_rogical_deleted=False)
                    
                    # if del_email == self.request.user.email:
                    #     self.error_email_list.append(email_list[i - 1])
                    #     raise LoggedInUserException('ご自身のメールアドレスを削除対象から除外してください。')
                    
                    if user.count() == 0:
                        self.error_email_list.append(email_list[i - 1])
                        print('エラーeメールについかしら',self.error_email_list)

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{}行目でデータの変換に失敗しました。入力したメールアドレスをご確認ください。'.format(i))

    def post(self, request):
        try:
            # 100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():

                self.delete_user(request)
        except LoggedInUserException as e:
            print('とりあえずこちらをとった',str(e))
            data = {
                'messages': str(e),
            }
            return JsonResponse(data)
        # 今のところは、この2つのエラーは同様に対処します。
        except InvalidSourceExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidNonExistsExcepion as e:
            data = {
                'messages': str(e),
                'error_email_list': self.error_email_list[self.error_id]
            }
            return JsonResponse(data, status=500)
        else:
            if len(self.error_email_list) > 0:
                data = {
                    'messages': _("エラー：存在しないユーザーが含まれています。"),
                    'error_email_list': self.error_email_list,
                    'judge': _("ERROR")
                }
                print('このえらーにすすんでいる＝ーーーーーー')

            else:
                data = {
                    'messages': _("データ照合完了：削除ボタンを押して削除してください。"),
                    'judge': _("SUCCESS")
                }

            return JsonResponse(data)

"""
一括変更
"""
class PostUpdate(View, CommonView, LoginRequiredMixin):
    template_name = 'bulk/ajax_update.html'
    number_of_columns = 9  # 列の数を定義しておく。各行の列がこれかどうかを判断する

    def save_csv(self, random_name):
            # アップロードされたファイル名を取得
            with open(random_name,'r') as csvfile:
            # ヘッダーを読み飛ばす
                header = next(csvfile)
                reader = csv.reader(csvfile)

                i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
                try:
                    # iは、現在の行番号。エラーの際に補足情報として使う
                    for i, row in enumerate(reader, 1):

                        # 存在確認
                        user = User.objects.filter(email=row[0])
                        if user.count() == 0:
                            raise InvalidNonExistsExcepion('{0}行目 ユーザーが存在しません。ファイル名:{1}'.format(i, csvfile))

                        # 列数が違う場合
                        if len(row) != self.number_of_columns:
                            raise InvalidColumnsExcepion('{0}行目 項目数エラー。本来の列数: {1}, {0}行目の列数: {2} ファイル名:{3}'.format(i, self.number_of_columns, len(row), csvfile))

                        # 必須カラムのチェック
                        for num in range(0, 2):
                            if not row[num]:
                                raise InvalidMustColumnsExcepion('{0}行目 {1}列目の必須項目がありません。ファイル名:{2}'.format(i, num+1, csvfile))

                        user = User.objects.get(email=row[0])
                        user.last_name = row[1]
                        user.first_name = row[2]
                        user.middle_name = row[3]
                        if row[1] and row[2] and row[3]: 
                            user.display_name = row[1] + ' ' + row[3] + ' ' + row[2]
                        elif row[1] and row[2]:
                            user.display_name = row[1] + ' ' + row[2]
                        user.p_last_name = row[4]
                        user.p_first_name = row[5]
                        user.p_middle_name = row[6]
                        if row[4] and row[5] and row[6]: 
                            user.p_display_name = row[4] + ' ' + row[6] + ' ' + row[5]
                        elif row[4] and row[5]:
                            user.p_display_name = row[4] + ' ' + row[5]
                        # 利用サービスの値をリストに変換
                        services = row[7].split()
                        user.service.set(Service.objects.filter(name__in=services))
                        user.description = row[8]

                        user.save()

                except UnicodeDecodeError:
                    raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csvfile))

                except IntegrityError:
                    raise IntegrityError('{0}行目 エラー。{1}が重複しています。ファイル名:{2}'.format(i, row[0], csvfile))
            #変更後仮ファイル削除
            os.remove(random_name)

    def post(self, request):
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(request.POST.get('random_file'))
        # 今のところは、この2つのエラーは同様に対処します。
        except InvalidSourceExcepion as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidColumnsExcepion as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        except IntegrityError as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidMustColumnsExcepion as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidNonExistsExcepion as e:
            data = {
                'messages2': str(e)
            }
            return JsonResponse(data, status=500)
        else:
            data = {
                'messages2': _("ユーザーの一括変更が完了しました。")
            }
        return JsonResponse(data)


from django.core.files.storage import FileSystemStorage

"""
一括変更のテスト
"""
class TestPostUpdate(FormView, CommonView, LoginRequiredMixin):
    template_name = 'bulk/update.html'
    form_class = CSVUploadForm
    number_of_columns = 9  # 列の数を定義しておく。各行の列がこれかどうかを判断する

    def save_csv(self, form):
            # アップロードされたファイル名を取得
            csv_file_name = str(form.cleaned_data['file'])
            # csv.readerに渡すため、TextIOWrapperでテキストモードなファイルに変換
            csvfile = io.TextIOWrapper(form.cleaned_data['file'],encoding='utf-8_sig')

            reader = csv.reader(csvfile)
            # ヘッダーを読み飛ばす
            header = next(reader)
            self.error_list = []
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(reader, 1):

                    # 列数が違う場合
                    if len(row) != self.number_of_columns:
                        raise InvalidColumnsExcepion('{0}行目 項目数エラー。本来の列数: {1}, {0}行目の列数: {2} ファイル名:{3}'.format(i, self.number_of_columns, len(row), csv_file_name))

                    # 必須カラムのチェック
                    for num in range(0, 3):
                        if not row[num]:
                            raise InvalidMustColumnsExcepion('{0}行目 {1}列目の必須項目がありません。ファイル名:{2}'.format(i, num+1, csv_file_name))

                    # 存在確認ここをまわす
                    user = User.objects.filter(email=row[0])
                    if user.count() == 0:
                        #raise InvalidNonExistsExcepion('{0}行目 ユーザーが存在しません。ファイル名:{1}'.format(i, csv_file_name))
                        self.error_list.append(str(i) + '行目：' + row[0])


                #ランダムな文字列でファイル名を作る
                random_name = ''.join(random.choice(string.ascii_lowercase) for i in range(15)) #15文字ほどの文字列
                fs = FileSystemStorage() #デフォルトのストレージ
                fs.location = './' #ファイルの一時保管場所。現在はpotal配下に
                fs.save(random_name, csvfile) #ランダムな名前のcsvfileとして保存
                self.random_name = random_name
                random_file_dir = os.path.join(fs.location,random_name)
                random_file_name = random_file_dir + '.csv'

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csv_file_name))

    def form_valid(self, form):
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(form)
        # 今のところは、この2つのエラーは同様に対処。
        except InvalidSourceExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidColumnsExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except IntegrityError as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidMustColumnsExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidNonExistsExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        else:
            if len(self.error_list) > 0:
                data = {
                    'messages': _("エラー：存在しないユーザーが含まれています。"),
                    'error_list': self.error_list,
                    'judge': _("ERROR")
                }
                os.remove(self.random_name)
            else:
                data = {
                    'messages': _("データ照合完了：変更ボタンを押してください。"),
                    'file_name': self.random_name,
                    'judge': _("SUCCESS")
                }
            return JsonResponse(data)