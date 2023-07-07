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
from accounts.models import User, Company, Service

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


# 全てで実行させるView
class CommonView(ContextMixin):

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user
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
9.会社名(自動反映)
10.部署名
11.利用サービス(スペースで区切る)
12.説明
"""
# class PostImport(FormView, CommonView):
# class PostImport(TemplateView, CommonView):
    # template_name = 'bulk/import.html'
    # form_class = CSVUploadForm
    # number_of_columns = 10  # 列の数を定義しておく。各行の列がこれかどうかを判断する
    

    
    # def save_csv(self, form):
            
    #         # アップロードされたファイル名を取得
    #         csv_file_name = str(form.cleaned_data['file'])
    #         #csv_file_name = str(form.cleaned_data[glob.glob("./random_name/0/*.csv")])
    #         # csv.readerに渡すため、TextIOWrapperでテキストモードなファイルに変換
    #         #csvfile = io.TextIOWrapper(form.cleaned_data['random_file'])
    #         csvfile = io.TextIOWrapper(form.cleaned_data['file'])
    #         reader = csv.reader(csvfile)
    #         # ヘッダーを読み飛ばす
    #         header = next(reader)
    #         i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
    #         try:
    #             # iは、現在の行番号。エラーの際に補足情報として使う
    #             for i, row in enumerate(reader, 1):
    #                 # 列数が違う場合
    #                 if len(row) != self.number_of_columns:
    #                     raise InvalidColumnsExcepion(_('NUMBER OF ITEM ERROR').format(i, self.number_of_columns, len(row), csv_file_name))
                    

    #                 # 必須カラムのチェック
    #                 for num in range(0, 3):
    #                     if not row[num]:
    #                         raise InvalidMustColumnsExcepion('{0}行目 {1}列目の必須項目がありません。ファイル名:{2}'.format(i, num+1, csv_file_name))
    #                 suser = self.request.user

    #                 user = User.objects.create(email=row[0])
    #                 user.set_password(row[1])
    #                 user.last_name = row[2]
    #                 user.first_name = row[3]
    #                 user.middle_name = row[4]
    #                 if row[2] and row[3] and row[4]: 
    #                     user.display_name = row[2] + ' ' + row[4] + ' ' + row[3]
    #                 elif row[2] and row[3]:
    #                     user.display_name = row[2] + ' ' + row[3]
    #                 user.p_last_name = row[5]
    #                 user.p_first_name = row[6]
    #                 user.p_middle_name = row[7]
    #                 if row[5] and row[6] and row[7]: 
    #                     user.p_display_name = row[5] + ' ' + row[7] + ' ' + row[6]
    #                 elif row[5] and row[6]:
    #                     user.p_display_name = row[5] + ' ' + row[6]
    #                 # company = Company.objects.filter(pic_company_name=row[7]).first()
    #                 # if company:
    #                     # user.company = company
    #                 # else:
    #                     # user.company = None
    #                 # company_id = suser.company.id
    #                 # user.company = company_id(row[7])
    #                 user.company = suser.company
    #                 # 利用サービスの値をリストに変換
    #                 services = row[8].split()
    #                 user.service.set(Service.objects.filter(name__in=services))
    #                 user.description = row[9]
    #                 user.save()

    #         except UnicodeDecodeError:
    #             raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csv_file_name))

    #         except IntegrityError as e:
    #             print("ああああ", e)
    #             raise IntegrityError('{0}行目 エラー。{1}が重複しています。 ファイル名:{2}'.format(i, row[0], csv_file_name))


# #ここからうごかんーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
#     def form_valid(self, form):
#     #def form_valid(self):

#         print('登録はじめるよ')
#         try:
#             # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
#             with transaction.atomic():
#                 self.save_csv(form)
#         # 今のところは、この2つのエラーは同様に対処します。
#         except InvalidSourceExcepion as e:
#             data = {
#                 'messages': str(e)
#             }
#             return JsonResponse(data, status=500)
#         except InvalidColumnsExcepion as e:
#             data = {
#                 'messages': str(e)
#             }
#             return JsonResponse(data, status=500)
#         except IntegrityError as e:
#             data = {
#                 'messages': str(e)
#             }
#             return JsonResponse(data, status=500)
#         except InvalidMustColumnsExcepion as e:
#             data = {
#                 'messages': str(e)
#             }
#             return JsonResponse(data, status=500)
#         else:
#             data = {
#                 'messages': _("SUCCESS")
#             }
#             return JsonResponse(data)

class AjaxPostImport(View, CommonView):
    template_name = 'bulk/ajax_import.html'
    number_of_columns = 10  # 列の数を定義しておく。各行の列がこれかどうかを判断する
    
    def save_csv(self, random_name):
            # アップロードされたファイル名を取得
            with open(random_name,'r') as csvfile:
                #content = fp.read()
                #print(content)

            # ヘッダーを読み飛ばす
                header = next(csvfile)
                reader = csv.reader(csvfile)
                print("とうろくたいしょう",csvfile)
                print("１行目",header)
                
                i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            
                try:
                    # iは、現在の行番号。エラーの際に補足情報として使う
                    for i, row in enumerate(reader, 1):
                        # 列数が違う場合
                        print('出力ちぇっく',len(row))
                        print('ひつようなもの',self.number_of_columns)

                        if len(row) != self.number_of_columns:
                            raise InvalidColumnsExcepion(_('NUMBER OF ITEM ERROR').format(i, self.number_of_columns, len(row), csvfile))
                        

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
                    
                    os.remove(csvfile)

                    #os.remove(random_name)

                except UnicodeDecodeError:
                    raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csvfile))

                except IntegrityError as e:
                    raise IntegrityError('{0}行目 エラー。{1}が重複しています。 ファイル名:{2}'.format(i, row[0], csvfile))
            


#ここからうごかんーーーーーーーーーーーーーーーーーーーーーーーーーーーーー
    def post(self, request):
    #def form_valid(self):

        print('登録はじめるよ',vars(self))
        print('登録はじめるよ',request.POST)
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(request.POST.get('random_file'))
                pass
        # 今のところは、この2つのエラーは同様に対処
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
            data = {
                'messages': _("SUCCESS2")
            }
            return JsonResponse(data)


















from django.core.files.storage import FileSystemStorage

"""
インポートのテスト
"""
# #ランダムな文字列でファイル名を作る
# random_name = ''.join(random.choice(string.ascii_lowercase) for i in range(15)) #15文字ほどの文字列

#テストの時点ですぐ検証しているので保存されていない＝一時保存が必要
class TestPostImport(FormView, CommonView):
    template_name = 'bulk/import.html'
    form_class = CSVUploadForm
    number_of_columns = 10  # 列の数を定義しておく。各行の列がこれかどうかを判断する
    
    
    def save_csv(self, form):
            # アップロードされたファイル名を取得
            csv_file_name = str(form.cleaned_data['file'])
            print("ファイル名",csv_file_name)
            # csv.readerに渡すため、TextIOWrapperでテキストモードなファイルに変換
            csvfile = io.TextIOWrapper(form.cleaned_data['file'])
            print("aaaa",csvfile)
            print("aaaa",type(csvfile))
            reader = csv.reader(csvfile)
            # ヘッダーを読み飛ばす
            header = next(reader)
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(reader, 1):
                    print('出力ちぇっく',len(row))
                    # 列数が違う場合
                    if len(row) != self.number_of_columns:
                        raise InvalidColumnsExcepion(_('列数を正してください').format(i, self.number_of_columns, len(row), csv_file_name))
                

                    # 必須カラムのチェック
                    for num in range(0, 3):
                        if not row[num]:
                            raise InvalidMustColumnsExcepion(_('必須項目が入力されていません').format(i, num+1, csv_file_name))
                          

                    # 重複チェック
                    is_exist = User.objects.filter(email=row[0]).exists()
                    if is_exist:
                        raise IntegrityError('{0}行目 エラー。{1}が重複しています。 ファイル名:{2}'.format(i, row[0], csv_file_name))



                #ランダムな文字列でファイル名を作る
                random_name = ''.join(random.choice(string.ascii_lowercase) for i in range(15)) #15文字ほどの文字列
                fs = FileSystemStorage() #デフォルトのストレージ
                fs.location = './' #ファイルの一時保管場所。現在はpotal配下に
                fs.save(random_name, csvfile) #ランダムな名前のcsvfileとして保存
                print('ランダムな名前作成',random_name)
                self.random_name = random_name
                random_file_dir = os.path.join(fs.location,random_name)
                print('ランダムなファイルのありか',random_file_dir)
                random_file_name = random_file_dir + '.csv'
                print('ランダムなファイルの拡張子',random_file_name)
                
            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csv_file_name))

    def form_valid(self, form):
        # print('ここからJSへ',random_name)
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(form)
        # 今のところは、この2つのエラーは同様に対処します。
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
            data = {
                'messages': _("SUCCESS1"),
                'file_name':self.random_name
            }
            return JsonResponse(data)


"""
エクスポート
"""

def post_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'
    # HttpResponseオブジェクトはファイルっぽいオブジェクトなので、csv.writerにそのまま渡せます。
    writer = csv.writer(response)
    user = request.user
    print("ログインユーザー",type(user))
    print("ログインユーザー2",user)

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
    writer = csv.writer(response)
    # ヘッダーの設定
    writer.writerow(["*1.mailaddress","*2.password","*3.lastname","*4.firstname","5.middlename","6.lastname(kana)","7.firstname(kana)","8.middlename(kana)","9.service","10.memo"])
    # writer.writerow(["メールアドレス(必須)", "パスワード(必須)", "姓(必須)", "名(必須)", "ミドルネーム", "ふりがな(姓)", "ふりがな(名)", "ふりがな(ミドルネーム)", "利用サービス", "説明"])
    return response



"""
一括削除
"""
class PostDelete(FormView, CommonView):
    template_name = 'bulk/delete.html'
    success_url = reverse_lazy('accounts:home')
    form_class = UserDeleteForm

    
    def delete_user(self, request):

            # フォームに入力されたIDを取得
            del_email = request.POST.get('id')

            print("おこここ",del_email)

            # IDをリストに変換
            email_list = del_email.splitlines()
            print("メールリスト",email_list)
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(email_list, 1):

                    # 存在確認
                    user = User.objects.filter(email=row,is_rogical_deleted=False)
                    if user.count() == 0:
                        raise InvalidNonExistsExcepion('{0}行目 ユーザーが存在しません。入力しなおしてください。'.format(i))

                    # 削除する
                    delusers = User.objects.filter(email__in = email_list)
                    for deluser in delusers:
                        print(deluser)
                        deluser.is_rogical_deleted = True
                        deluser.save()
                    # user.delete()

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{}行目でデコードに失敗しました。ファイルのエンコーディングや、正しいCSVファイルか確認ください。'.format(i))

    def post(self, request):
        try:
            # 100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.delete_user(request)
                print("このときは？")
        # 今のところは、この2つのエラーは同様に対処します。
        except InvalidSourceExcepion as e:
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
            data = {
                'messages': _("SUCCESS")
            }
            return JsonResponse(data)



"""
一括削除のテスト
"""
class TestPostDelete(FormView, CommonView):
    template_name = 'bulk/delete.html'
    success_url = reverse_lazy('accounts:home')
    form_class = UserDeleteForm

    def delete_user(self, request):

            # フォームに入力されたIDを取得
            del_email = request.POST.get('id')

            # IDをリストに変換
            email_list = del_email.splitlines()

            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(email_list, 1):

                    # 存在確認
                    user = User.objects.filter(email=row,is_rogical_deleted=False)
                    if user.count() == 0:
                        raise InvalidNonExistsExcepion('{0}行目のユーザーが存在しません。入力しなおしてください。'.format(i))

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
一括変更
"""
class PostUpdate(FormView, CommonView):
    template_name = 'bulk/update.html'
    form_class = CSVUploadForm
    number_of_columns = 9  # 列の数を定義しておく。各行の列がこれかどうかを判断する

    def save_csv(self, form):
            # アップロードされたファイル名を取得
            csv_file_name = str(form.cleaned_data['file'])
            # csv.readerに渡すため、TextIOWrapperでテキストモードなファイルに変換
            csvfile = io.TextIOWrapper(form.cleaned_data['file'])
            reader = csv.reader(csvfile)
            # ヘッダーを読み飛ばす
            header = next(reader)
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(reader, 1):

                    # 存在確認
                    user = User.objects.filter(email=row[0])
                    if user.count() == 0:
                        raise InvalidNonExistsExcepion('{0}行目 ユーザーが存在しません。ファイル名:{1}'.format(i, csv_file_name))

                    # 列数が違う場合
                    if len(row) != self.number_of_columns:
                        raise InvalidColumnsExcepion('{0}行目 項目数エラー。本来の列数: {1}, {0}行目の列数: {2} ファイル名:{3}'.format(i, self.number_of_columns, len(row), csv_file_name))

                    # 必須カラムのチェック
                    for num in range(0, 2):
                        if not row[num]:
                            raise InvalidMustColumnsExcepion('{0}行目 {1}列目の必須項目がありません。ファイル名:{2}'.format(i, num+1, csv_file_name))

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
                    services = row[8].split()
                    user.service.set(Service.objects.filter(name__in=services))
                    user.description = row[9]
                    
                    user.save()

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csv_file_name))

            except IntegrityError:
                raise IntegrityError('{0}行目 エラー。{1}が重複しています。ファイル名:{2}'.format(i, row[0], csv_file_name))

    def form_valid(self, form):
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(form)
        # 今のところは、この2つのエラーは同様に対処します。
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
            data = {
                'messages': _("SUCCESS")
            }
            return JsonResponse(data)



"""
一括変更のテスト
"""
class TestPostUpdate(FormView, CommonView):
    template_name = 'bulk/update.html'
    form_class = CSVUploadForm
    number_of_columns = 9  # 列の数を定義しておく。各行の列がこれかどうかを判断する

    def save_csv(self, form):
            # アップロードされたファイル名を取得
            csv_file_name = str(form.cleaned_data['file'])
            # csv.readerに渡すため、TextIOWrapperでテキストモードなファイルに変換
            csvfile = io.TextIOWrapper(form.cleaned_data['file'])
            reader = csv.reader(csvfile)
            # ヘッダーを読み飛ばす
            header = next(reader)
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(reader, 1):

                    # 存在確認
                    user = User.objects.filter(email=row[0])
                    if user.count() == 0:
                        raise InvalidNonExistsExcepion('{0}行目 ユーザーが存在しません。ファイル名:{1}'.format(i, csv_file_name))

                    # 列数が違う場合
                    if len(row) != self.number_of_columns:
                        raise InvalidColumnsExcepion('{0}行目 項目数エラー。本来の列数: {1}, {0}行目の列数: {2} ファイル名:{3}'.format(i, self.number_of_columns, len(row), csv_file_name))

                    # 必須カラムのチェック
                    for num in range(0, 2):
                        if not row[num]:
                            raise InvalidMustColumnsExcepion('{0}行目 {1}列目の必須項目がありません。ファイル名:{2}'.format(i, num+1, csv_file_name))

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csv_file_name))


    def form_valid(self, form):
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(form)
        # 今のところは、この2つのエラーは同様に対処します。
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
            data = {
                'messages': _("SUCCESS")
                'file_name':self.random_name
            }
            return JsonResponse(data)