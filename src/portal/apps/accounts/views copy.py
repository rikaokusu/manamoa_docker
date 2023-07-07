from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic import View, ListView, DetailView, TemplateView, FormView, CreateView, UpdateView, DeleteView
from django.views.generic.base import ContextMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

from accounts.forms import LoginForm, CompanyUpdateForm, MyUserCreationForm, MyUserChangeForm, CustomPasswordChangeForm, MultiAddInfoForm, UserCompanyMultiForm, MyPasswordResetForm, MySetPasswordForm, UserChangeForm, UserSettingsForm, ContactForm, CompanyConfirmForm,CompanyOnlyUpdateForm
from django.urls import reverse_lazy

# アクセスURL生成
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps

# テンプレート情報取得
from django.template.loader import get_template

# settings情報の取得
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.models import User, Company, Messages, Service
from contracts.models import Contract, Plan, PaymentMethod, Estimates

from django.db.models import Q

from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect

from datetime import datetime,timezone

# フロントへメッセージ送信
from django.contrib import messages

from django.shortcuts import redirect
from django.urls import reverse

from django.http import JsonResponse

from django.dispatch import receiver
from django.db.models.signals import post_save

# セッションを利用するためのライブラリ
from lib.my_utils import check_session
#メール送信
from django.core.mail import send_mail

# 逆参照のテーブルをフィルタやソートする
from django.db.models import Prefetch
# パスワード生成
import string, random


from django.contrib.auth import get_user_model


# 全てで実行させるView
class CommonView(ContextMixin):

    # def dispatch(self, request, *args, **kwargs):

    #     # メッセージの情報を返す
    #     message_q = Messages.objects.filter(user=str(self.request.user.id))

    #     for message in message_q:
    #         if message.url == self.request.resolver_match.url_name:
    #             category = message.category
    #             text = message.text
    #             message_id = str(message.id)
    #             # company_id = 1
    #             if category == "error":
    #                 # messages.error(request, '' + text + '<div type="button" id="okBtn" data-id=' + '"' + id + '"' + ' data-url="update_profile" class="my-btn my-btn-egypt-1 my-btn-s my-btn-w5 ml-1 mr-1">はい</div><div type="button" data-url="update_profile" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">いいえ</div>')
    #                 messages.error(request, '<div id="okBtn" data-message_id=' + '"' + message_id + '"' + '>はい</div>')

    #     return super().dispatch(request, *args, **kwargs)


    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user

        email_list = current_user.email.rsplit('@', 1)
        # メールアドレスをユーザ名とドメインに分割
        email_domain = email_list[1]

        url_name = self.request.resolver_match.url_name
        app_name = self.request.resolver_match.app_name

        context["url_name"] = url_name
        context["app_name"] = app_name


        context["current_user"] = current_user
        context["email_domain"] = email_domain

        # サービス管理者の抽出
        # services = Service.objects.filter(number__in=current_user.service_admin)
        # context["services"] = services

        return context


"""
ホーム画面
"""
# @method_decorator(login_required(login_url='/manager/login/'), name = 'dispatch')
# @method_decorator(user_is_staff, name = 'dispatch')
class HomeTemplateView(LoginRequiredMixin, ListView, CommonView):
    model = Service
    template_name = 'accounts/home/home.html'
    context_object_name = 'services'
    login_url = '/login/'

    def get_queryset(self):
        current_user_id = self.request.user.pk
        current_user = self.request.user

        # サービステーブルから該当するサービスで契約テーブルに値があるか数値を取得
        # service = Service.objects.annotate(num_contract=Count('contract', filter=Q(contract__user_id=current_user_id)))
        
        service = Service.objects.all().prefetch_related(Prefetch("contract_set", queryset=Contract.objects.filter(user=current_user)))
        
        return service
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        url_name = self.request.resolver_match.url_name

        context["url_name"] = url_name

        # サービス管理者の抽出
        # services = Service.objects.filter(number__in=current_user.service_admin)
        # context["services"] = services

        return context
"""
ログイン画面
"""
class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_field_name = 'next'

    # ここでget_redirect_url使用不可。
    # ユーザーリダイレクトしてPW設定が使用できなくなる

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        url_name = self.request.resolver_match.url_name

        context["url_name"] = url_name

        # サービス管理者の抽出
        # services = Service.objects.filter(number__in=current_user.service_admin)
        # context["services"] = services

        return context


"""
ログアウト画面
"""
class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'accounts/logout.html'
    # ログアウト後のURLを指定
    next_page = reverse_lazy('accounts:login')

"""
ヘルプページ
"""
class HelpView(LoginRequiredMixin, CommonView, TemplateView):
    template_name = 'accounts/help.html'
    login_url = '/login/'

"""
会社プロファイル
"""
# @method_decorator(login_required, name = 'dispatch')
class CompanyProfile(LoginRequiredMixin, TemplateView, CommonView):
    # model = Company
    template_name = 'accounts/companyprofile.html'
    login_url = '/login/'


"""
会社プロファイル更新
"""
# @method_decorator(login_required(login_url='/manager/login/'), name = 'dispatch')
class CompanyonlyUpdateView(LoginRequiredMixin, UpdateView, CommonView):
    model = Company
    template_name = "accounts/update_companyonly.html"
    form_class = CompanyOnlyUpdateForm
    success_url = reverse_lazy('accounts:companyprofile')
    login_url = '/login/'

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()

        # context["company"] = current_user.company
        context["test"] = "てすと"
        return context

    # def dispatch(self, request, *args, **kwargs):

    #     # 変更対象のオブジェクトを取得
    #     company = Company.objects.filter(id=self.kwargs['pk']).first()

    #     # GET時のみ動作
    #     if request.method == "GET":

    #         # 変更フラグの存在を確認
    #         if company.version:
    #             id = str(company.id)

    #             # 自分自身の場合
    #             if company.change_user == str(self.request.user.id):

    #                 # # メッセージへの保存
    #                 # message = Messages.objects.create(user=str(self.request.user.id))
    #                 # message.url = "companyprofile"
    #                 # message.category = "error"
    #                 # message.text = '変更中のセッションが残っています。セッションを破棄して新たに変更しますか？'
    #                 # message.save()

    #                 messages.error(request, '変更中のセッションが残っています。セッションを破棄して新たに変更しますか？<div type="button" id="okBtn" data-id=' + '"' + id + '"' + ' data-url="update_profile" class="my-btn my-btn-egypt-1 my-btn-s my-btn-w5 ml-1 mr-1">はい</div><div type="button" data-url="update_profile" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">いいえ</div>')
    #                 return redirect('accounts:companyprofile')

    #             # 他ユーザの場合
    #             else:
    #                 user = User.objects.filter(id=company.change_user).first()

                

    #                 change_user = str(user.display_name)

    #                 timestamp = company.version
    #                 now = datetime.now(timezone.utc)

    #                 diff = now - timestamp

    #                 # 30分以上立っている場合
    #                 if diff.seconds >= 1800:

    #                     messages.error(request, '' + change_user + ' さんが変更中です。セッションを破棄して新たに変更しますか？<div type="button" id="okBtn" data-id=' + '"' + id + '"' + ' data-url="update_profile" class="my-btn my-btn-egypt-1 my-btn-s my-btn-w5 ml-1 mr-1">はい</div><div type="button" data-url="update_profile" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">いいえ</div>')
    #                     return redirect('accounts:companyprofile')

    #                 # 30分未満の場合
    #                 else:
    #                     messages.error(request, '' + change_user + ' さんが変更中です。<div type="button" id="okBtn" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">閉じる</div>')
    #                     return redirect('accounts:companyprofile')


    #         else:

    #             # 変更フラグをセット
    #             company.version = datetime.now()
    #             # 変更者のIDをセット
    #             company.change_user = self.request.user.id
    #             # 上書きフラグをセット
    #             company.change_row = 1
    #             # 保存
    #             company.save()



    #     return super().dispatch(request, *args, **kwargs)



    # def post(self, request, *args, **kwargs):

        # # 変更対象のオブジェクトを取得
        # company = Company.objects.filter(id=self.kwargs['pk']).first()
        # print("かんぱにー",company)


        # # セッションが奪われた場合
        # if company.change_row:

        #     # 自分自身の場合
        #     if company.change_user == str(self.request.user.id):


        #         messages.error(request, '他の操作でセッションが失われました。')
        #         return redirect('accounts:companyprofile')

        #     # 他ユーザの場合
        #     else:

        #         user = User.objects.filter(id=company.change_user).first()

        #         change_user = str(user.display_name)

        #         messages.error(request, '' + change_user + 'さんがセッションを取得しました。')
        #         return redirect('accounts:companyprofile')


        # form = self.get_form()
        # if form.is_valid():
        #     return self.form_valid(form)
        # else:
        #     return self.form_invalid(form)



    def form_valid(self, form):

        # 会社の登録
        company = form.save(commit=False)

        # if company.pic_legal_person_posi == '1': #前
        #     if not company.get_pic_legal_personality_display() == "その他":
        #         company.pic_company_name = company.get_pic_legal_personality_display() + company.pic_company_name
        #     else:
        #         company.pic_company_name = company.pic_company_name


        # elif company.pic_legal_person_posi == '2': #後
        #     if not company.get_pic_legal_personality_display() == "その他":
        #         company.pic_company_name = company.pic_company_name + company.get_pic_legal_personality_display()
        #     else:
        #         company.pic_company_name = company.pic_company_name

        # else:
        #     company.pic_company_name = company.pic_company_name

        # if company.invoice_legal_person_posi == '1': #前
        #     if not company.get_invoice_legal_personality_display == "その他":
        #         company.invoice_company_name = company.get_invoice_legal_personality_display() + company.invoice_company_name
        #     else:
        #         company.invoice_company_name = company.invoice_company_name

        # elif company.invoice_legal_person_posi == '2': #後
        #     if not company.get_invoice_legal_personality_display == "その他":
        #         company.invoice_company_name = company.invoice_company_name + company.get_invoice_legal_personality_display()
        #     else:
        #         company.invoice_company_name = company.invoice_company_name


        # else:
        #     company.invoice_company_name = company.invoice_company_name

        company.save()

        return super(CompanyonlyUpdateView, self).form_valid(form)


"""
会社＆請求先プロファイル更新
"""
# @method_decorator(login_required(login_url='/manager/login/'), name = 'dispatch')
class CompanyprofileUpdateView(LoginRequiredMixin, UpdateView, CommonView):
    model = Company
    template_name = "accounts/update_companyprofile.html"
    form_class = CompanyUpdateForm
    success_url = reverse_lazy('accounts:companyprofile')
    login_url = '/login/'

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()

        # context["company"] = current_user.company
        context["test"] = "てすと"
        return context

    # def dispatch(self, request, *args, **kwargs):

    #     # 変更対象のオブジェクトを取得
    #     company = Company.objects.filter(id=self.kwargs['pk']).first()

    #     # GET時のみ動作
    #     if request.method == "GET":

    #         # 変更フラグの存在を確認
    #         if company.version:
    #             id = str(company.id)

    #             # 自分自身の場合
    #             if company.change_user == str(self.request.user.id):

    #                 # # メッセージへの保存
    #                 # message = Messages.objects.create(user=str(self.request.user.id))
    #                 # message.url = "companyprofile"
    #                 # message.category = "error"
    #                 # message.text = '変更中のセッションが残っています。セッションを破棄して新たに変更しますか？'
    #                 # message.save()

    #                 messages.error(request, '変更中のセッションが残っています。セッションを破棄して新たに変更しますか？<div type="button" id="okBtn" data-id=' + '"' + id + '"' + ' data-url="update_profile" class="my-btn my-btn-egypt-1 my-btn-s my-btn-w5 ml-1 mr-1">はい</div><div type="button" data-url="update_profile" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">いいえ</div>')
    #                 return redirect('accounts:companyprofile')

    #             # 他ユーザの場合
    #             else:
    #                 user = User.objects.filter(id=company.change_user).first()

                

    #                 change_user = str(user.display_name)

    #                 timestamp = company.version
    #                 now = datetime.now(timezone.utc)

    #                 diff = now - timestamp

    #                 # 30分以上立っている場合
    #                 if diff.seconds >= 1800:

    #                     messages.error(request, '' + change_user + ' さんが変更中です。セッションを破棄して新たに変更しますか？<div type="button" id="okBtn" data-id=' + '"' + id + '"' + ' data-url="update_profile" class="my-btn my-btn-egypt-1 my-btn-s my-btn-w5 ml-1 mr-1">はい</div><div type="button" data-url="update_profile" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">いいえ</div>')
    #                     return redirect('accounts:companyprofile')

    #                 # 30分未満の場合
    #                 else:
    #                     messages.error(request, '' + change_user + ' さんが変更中です。<div type="button" id="okBtn" class="my-btn my-btn-gray-1 my-btn-s my-btn-w5 ml-1 mr-1">閉じる</div>')
    #                     return redirect('accounts:companyprofile')


    #         else:

    #             # 変更フラグをセット
    #             company.version = datetime.now()
    #             # 変更者のIDをセット
    #             company.change_user = self.request.user.id
    #             # 上書きフラグをセット
    #             company.change_row = 1
    #             # 保存
    #             company.save()



    #     return super().dispatch(request, *args, **kwargs)



    # def post(self, request, *args, **kwargs):

        # # 変更対象のオブジェクトを取得
        # company = Company.objects.filter(id=self.kwargs['pk']).first()
        # print("かんぱにー",company)


        # # セッションが奪われた場合
        # if company.change_row:

        #     # 自分自身の場合
        #     if company.change_user == str(self.request.user.id):


        #         messages.error(request, '他の操作でセッションが失われました。')
        #         return redirect('accounts:companyprofile')

        #     # 他ユーザの場合
        #     else:

        #         user = User.objects.filter(id=company.change_user).first()

        #         change_user = str(user.display_name)

        #         messages.error(request, '' + change_user + 'さんがセッションを取得しました。')
        #         return redirect('accounts:companyprofile')


        # form = self.get_form()
        # if form.is_valid():
        #     return self.form_valid(form)
        # else:
        #     return self.form_invalid(form)



    def form_valid(self, form):

        # 会社の登録
        company = form.save(commit=False)

        # if company.pic_legal_person_posi == '1': #前
        #     if not company.get_pic_legal_personality_display() == "その他":
        #         company.pic_company_name = company.get_pic_legal_personality_display() + company.pic_company_name
        #     else:
        #         company.pic_company_name = company.pic_company_name


        # elif company.pic_legal_person_posi == '2': #後
        #     if not company.get_pic_legal_personality_display() == "その他":
        #         company.pic_company_name = company.pic_company_name + company.get_pic_legal_personality_display()
        #     else:
        #         company.pic_company_name = company.pic_company_name

        # else:
        #     company.pic_company_name = company.pic_company_name

        # if company.invoice_legal_person_posi == '1': #前
        #     if not company.get_invoice_legal_personality_display == "その他":
        #         company.invoice_company_name = company.get_invoice_legal_personality_display() + company.invoice_company_name
        #     else:
        #         company.invoice_company_name = company.invoice_company_name

        # elif company.invoice_legal_person_posi == '2': #後
        #     if not company.get_invoice_legal_personality_display == "その他":
        #         company.invoice_company_name = company.invoice_company_name + company.get_invoice_legal_personality_display()
        #     else:
        #         company.invoice_company_name = company.invoice_company_name


        # else:
        #     company.invoice_company_name = company.invoice_company_name


        company.save()



        return super(CompanyprofileUpdateView, self).form_valid(form)



@receiver(post_save, sender=Company)
def query_log(instance, **kwargs):

    # バージョンフラグをNoneとする
    instance.version = None
    # 変更者のIDをNoneとする
    instance.change_user = None
    # 上書きフラグをNoneとする
    instance.change_row = None

"""
ミドルネームON/OFF(Ajax)
"""
class MiddleChoiceAjaxView(View):
    def post(self, request):
        # POSTで送られてきた対象のID(リスト)を取得
        is_checked = request.POST.get('is_checked')
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()

        try:
            if is_checked == "true":
                current_user.company.middle_choice = True
                current_user.company.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "ミドルネームの使用を有効にしました。",
                                    })

            else:
                current_user.company.middle_choice = False
                current_user.company.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "ミドルネームの使用を無効にしました。",
                                    })

        except Exception as e:
            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ng",
                                "message": str(e),
                                })


"""
キャンセル処理
"""
class Cancel(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        # プロファイル更新時のキャンセル
        if self.kwargs['str'] == "update_profile":
            # 変更対象のオブジェクトを取得
            company = Company.objects.filter(id=self.kwargs['pk']).first()
            # バージョンフラグをNoneとする
            company.version = None
            # 変更者のIDをNoneとする
            company.change_user = None
            # 上書きフラグをNoneとする
            company.change_row = None
            # 保存
            company.save()


        return HttpResponseRedirect(reverse('accounts:companyprofile'))


"""
セッションのリセット処理(Ajax用)
"""
class ResetSession(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request):

        # プロファイル更新時のキャンセル
        url = request.POST.get('url')
        id = request.POST.get('id')

        if url == "update_profile":
            try:
                # 変更対象のオブジェクトを取得
                company = Company.objects.filter(id=id).first()
                # バージョンフラグをNoneとする
                company.version = None
                # 変更者のIDをNoneとする
                company.change_user = None
                # 上書きフラグをNoneとする
                company.change_row = None
                # 保存
                company.save()


                # メッセージを生成してJSONで返す
                data = {}
                data['message'] = ""
                return JsonResponse(data)


            except Exception as e:
                # メッセージを生成してJSONで返す
                data = {}
                data['message'] = ''
                return JsonResponse(data)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                                    ユーザー管理関連
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""
管理ユーザー情報画面
管理者情報を表示する画面
"""
class UserInfoView(LoginRequiredMixin,TemplateView,CommonView):
    template_name = 'accounts/user_infomation.html'
    login_url = '/login/'

"""
管理ユーザー情報変更画面
管理者情報を変更する画面
"""
class UserUpdateInfoView(LoginRequiredMixin, UpdateView, CommonView):
    model = User
    template_name = "accounts/update_userinfomation.html"
    form_class = UserChangeForm
    login_url = '/login/'
# フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UserUpdateInfoView, self).get_form_kwargs()
        # kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        user = form.save(commit=False)   

        # 姓と名をディスプレイ名にセットする
        last_name = form.cleaned_data['last_name']
        first_name = form.cleaned_data['first_name']
        middle_name = form.cleaned_data['middle_name']
        if last_name and first_name and middle_name:
            display_name = last_name + ' ' + middle_name + ' ' + first_name
            user.display_name = display_name
        elif last_name and first_name:
            display_name = last_name + ' ' + first_name
            user.display_name = display_name

        # ふりがなの姓と名をディスプレイ名にセットする
        p_last_name = form.cleaned_data['p_last_name']
        p_first_name = form.cleaned_data['p_first_name']
        p_middle_name = form.cleaned_data['p_middle_name']
        if p_last_name and p_first_name and p_middle_name:
            p_display_name = p_last_name + ' ' + p_middle_name + ' ' + p_first_name
            user.p_display_name = p_display_name
        elif p_last_name and p_first_name:
            p_display_name = p_last_name + ' ' + p_first_name
            user.p_display_name = p_display_name

        # 本番登録後、is_staff属性をTrueにする。
        user.is_staff = True

        # Serviceを登録する(UpdateViewで自動的にやってくれない？)
        # servicesはquerysetになっていて、object.set()で保存できる
        #services = form.cleaned_data['service']
        #user.service.set(services)
        user.save()

        return redirect('accounts:user_infomation')


"""
ユーザー一覧画面
管理者がユーザーの一覧を表示する画面
"""
class UserIndexView(LoginRequiredMixin, ListView, CommonView):
    model = User
    template_name = 'accounts/user.html'
    login_url = '/login/'


    # 管理者(ログインユーザー)の会社IDでフィルタリングしたユーザー一覧を返す
    def get_context_data(self, **kwargs):

        user = self.request.user
        context = super().get_context_data(**kwargs)

        # 会社ID+論理削除有無でフィルタリングして取得
        users = User.objects.all().filter(company_id__exact=user.company_id,is_rogical_deleted=False).exclude(email__iexact=user.email).order_by('-created_date')
        context['users'] = users
        return context

"""
ユーザー作成画面
管理者がユーザーを新規作成する際に使う画面
URL認証は実施しない
"""
# @method_decorator(login_required(login_url='/manager/login/'), name = 'dispatch')
class UserCreateView(LoginRequiredMixin, CreateView, CommonView):
    model = User
    template_name = "accounts/user_create.html"
    form_class = MyUserCreationForm
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UserCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    # セッションにフォームデータを保存
    def post(self, request, *args, **kwargs):
        request.session['form_data'] = request.POST
        return super().post(request, *args, **kwargs)

    # ログインユーザのドメインを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        # メールアドレスをユーザ名とドメインに分割
        domain = current_user.email.rsplit('@', 1)[1]

        # メールアドレスをユーザー名とサブドメインとドメインに分割
        domain2 = domain.split('.', 1)[1]
        context["current_user_domain"] = domain
        context["current_user_domain2"] = domain2

        return context


    def form_valid(self, form):

        user = form.save(commit=False)

        # 姓と名をディスプレイ名にセットする
        last_name = form.cleaned_data['last_name']
        first_name = form.cleaned_data['first_name']
        middle_name = form.cleaned_data['middle_name']
        if last_name and first_name and middle_name:
            display_name = last_name + ' ' + middle_name + ' ' + first_name
            user.display_name = display_name
        elif last_name and first_name:
            display_name = last_name + ' ' + first_name
            user.display_name = display_name

        # ふりがなの姓と名をディスプレイ名にセットする
        p_last_name = form.cleaned_data['p_last_name']
        p_first_name = form.cleaned_data['p_first_name']
        p_middle_name = form.cleaned_data['p_middle_name']
        if p_last_name and p_first_name and p_middle_name:
            p_display_name = p_last_name + ' ' + p_middle_name + ' ' + p_first_name
            user.p_display_name = p_display_name
        elif p_last_name and p_first_name:
            p_display_name = p_last_name + ' ' + p_first_name
            user.p_display_name = p_display_name

        # is_active属性をFalseにする。
        user.is_active = False
        user.is_activate = False

        # 管理者(ログインユーザ)の会社IDを登録する
        company_id = self.request.user.company_id
        user.company_id = company_id

        #パスワード生成
        password = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
        print('かりぱす',password)
        user.set_password(password)

        #　ログインユーザーのを取得してメールアドレスを
        current_user = self.request.user
        # メールアドレスをユーザ名とドメインに分割
        domain = current_user.email.rsplit('@', 1)[1]
        # メールアドレスをユーザー名とサブドメインとドメインに分割
        # domain2 = domain.split('.', 1)[1]

        email_user_name = form.cleaned_data['email']

        is_checked = form.cleaned_data['domain_check']

        if is_checked :
            subdomain = form.cleaned_data['subdomain']
            email = email_user_name + '@' + subdomain + '.' + domain
        else:
            email = email_user_name + '@' + domain

        user.email = email

        # 保存
        user.save()

        # 一度保存してUserのIDを生成してからServiceを登録する
        # servicesはquerysetになっていて、object.set()で保存できる
        services = form.cleaned_data['service']
        user.service.set(services)

        # service_adminはquerysetになっていて、object.set()で保存できる
        service_admin = form.cleaned_data['service_admin']
        user.service_admin.set(service_admin)


        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(str(user.pk)),
            'user': user,
            'password': password,
        }

        subject_template = get_template('accounts/mail_template/create/subject.txt')
        subject = subject_template.render(context)

        message_template = get_template('accounts/mail_template/create/message.txt')
        message = message_template.render(context)

        user.email_user(subject, message)

        return redirect('accounts:user_create_done')


"""
ユーザー作成完了画面の表示
"""
class UserCreateDone(TemplateView, CommonView):
    """ユーザー本登録したよ"""
    template_name = 'accounts/user_creation_done.html'



"""
ユーザーがトークンからアクセスした際の処理
仮登録で無効にしたユーザーを有効にする。
トークンの期限は1日
"""
class UserCreateComplete(View):
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoenNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_activate:
                    # 問題なければ本登録とする
                    user.is_active = True
                    user.is_activate = True
                    user.save()
                    return redirect('accounts:user_create_setpassword' , pk=user.pk)

        return HttpResponseBadRequest()


"""
ユーザーが本登録時にパスワードを設定する際の画面
"""
class UserCreateSetpassword(PasswordChangeView):
    model = User
    template_name = "accounts/user_set_password.html"
    form_class = CustomPasswordChangeForm
    success_url = reverse_lazy('accounts:user_create_setpassword_done')

    def form_valid(self, form):

        user = form.save(commit=False)
        password1 = form.cleaned_data['password1']
        password2 = form.cleaned_data['password2']

        user.save()

        return super(UserCreateSetpassword, self).form_valid(form)


"""
ユーザーによるパスワード変更完了の表示
"""
class UserCreateSetpasswordDone(TemplateView):
    template_name = 'accounts/user_set_password_done.html'


"""
ユーザー編集画面
管理者がユーザーを編集する際に使う画面
"""
# @method_decorator(login_required(login_url='/manager/login/'), name = 'dispatch')
# @method_decorator(user_is_entry_author, name = 'dispatch')
class UserUpdateView(LoginRequiredMixin, UpdateView, CommonView):
    model = User
    template_name = "accounts/user_update.html"
    form_class = MyUserChangeForm
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UserUpdateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


    def form_valid(self, form):

        user = form.save(commit=False)
        # 姓と名をディスプレイ名にセットする
        last_name = form.cleaned_data['last_name']
        first_name = form.cleaned_data['first_name']
        middle_name = form.cleaned_data['middle_name']
        if last_name and first_name and middle_name:
            display_name = last_name + ' ' + middle_name + ' ' + first_name
            user.display_name = display_name
        elif last_name and first_name:
            display_name = last_name + ' ' + first_name
            user.display_name = display_name

        # ふりがなの姓と名をディスプレイ名にセットする
        p_last_name = form.cleaned_data['p_last_name']
        p_first_name = form.cleaned_data['p_first_name']
        p_middle_name = form.cleaned_data['p_middle_name']
        if p_last_name and p_first_name and p_middle_name:
            p_display_name = p_last_name + ' ' + p_middle_name + ' ' + p_first_name
            user.p_display_name = p_display_name
        elif p_last_name and p_first_name:
            p_display_name = p_last_name + ' ' + p_first_name
            user.p_display_name = p_display_name

        # Serviceを登録する(UpdateViewで自動的にやってくれない？)
        # servicesはquerysetになっていて、object.set()で保存できる
        #services = form.cleaned_data['service']
        #user.service.set(services)

        # service_adminはquerysetになっていて、object.set()で保存できる
        #service_admin = form.cleaned_data['service_admin']
        #user.service_admin.set(service_admin)

        # 保存
        user.save()
        return redirect('accounts:user')

"""
管理者がユーザーのパスワードを変更する画面
"""
class UserChangePassword(LoginRequiredMixin, PasswordChangeView, CommonView):
    model = User
    template_name = "accounts/user_change_password_for_admin.html"
    form_class = CustomPasswordChangeForm
    login_url = '/login/'

    def form_valid(self, form):
        change_user = self.kwargs['pk']
        user = User.objects.get(pk=change_user)

        user.set_password(form.cleaned_data['password1'])

        user.save()

        return redirect('accounts:user_chenge_password_done')



"""
管理者によるパスワード変更完了の表示
"""
class UserChangePasswordDone(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'accounts/user_change_password_done_for_admin.html'
    login_url = '/login/'


"""
ユーザー無効(Ajax用)
"""
class UserDeactive(LoginRequiredMixin, View, CommonView):
    # @staff_member_required
    model = User
    login_url = '/login/'
    def post(self,request):
        checks =request.POST.getlist('checks[]')
        user = User.objects.get(pk__in = checks)
        user.is_active = False

        user.save()

        is_deactive = "true"

        # messages.success(request, "The user is deleted")

        data = {
            'is_exist': is_deactive
        }
        if data['is_exist']:
            data['error_message'] = 'アカウントの無効化が成功しました'
        # print('Emailバリデーション',User.objects.filter(email__iexact=email).exists())
        return JsonResponse(data)
        # return redirect('manager:user')
        # return render(request, 'front.html')


"""
ユーザー有効(Ajax用)
"""
class UserActive(LoginRequiredMixin, View, CommonView):
    # @staff_member_required
    model = User
    login_url = '/login/'
    def post(self,request):
        checks = request.POST.getlist('checks[]')
        # u = User.objects.get(pk = checks[0])
        user = User.objects.get(pk__in = checks)
        user.is_active = True

        user.save()

        is_active = "true"

        # messages.success(request, "The user is deleted")

        data = {
            'is_exist': is_active
        }
        if data['is_exist']:
            data['error_message'] = 'アカウントの有効化が成功しました'
        return JsonResponse(data)
        # return redirect('manager:user')
        # return render(request, 'front.html')


"""
ユーザー削除(Ajax用)
"""
class UserDelete(View):

    def post(self,request):
        checks = request.POST.getlist('checks[]')
        # u = User.objects.get(pk = checks[0])
        users = User.objects.filter(id__in = checks)
        for user in users:
            user.is_rogical_deleted = True
            user.save()
        
        
        #is_deleted = u.delete()
        # messages.success(request, "The user is deleted")
         
        data = {
        'is_exist': "true"
        }
    
        if data['is_exist']:
            data['error_message'] = str(len(checks)) + '名の削除が成功しました'
        return JsonResponse(data)


def load_admin_count(request):
    # cat = request.GET.get('cat')
    user = request.user

    # admin_num = User.objects.filter(is_staff = True ).count()
    admin_num = User.objects.all().filter(company_id__exact=user.company_id, is_staff = True).count()

    return JsonResponse({"status": "ok",
                        "admin_num": admin_num,
                        })


"""
ユーザ向けリンク再発行
"""
class UserLinkReissueView(View, CommonView):

    def get(self, request, *args, **kwargs):
        user_pk = kwargs['pk']

        user = User.objects.get(pk=user_pk)
        #パスワード生成
        password = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])

        user.set_password(password)

        # 保存
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(str(user.pk)),
            'user': user,
            'password': password,
        }

        subject_template = get_template('accounts/mail_template/create/subject.txt')
        subject = subject_template.render(context)
        # subject = "【アカウント作成】パスワードを設定してください。"

        message_template = get_template('accounts/mail_template/create/message.txt')
        message = message_template.render(context)
        

        user.email_user(subject, message)
        messages.success(request, "リンクメールを送信しました")


        return redirect('accounts:user')
#ここまで

# @staff_member_required

# def UserDelete(request):
#     print(vars(request))
#     checks = request.POST.getlist('checks[]')
#     # print("チェックの値は？",checks)
#     # print("チェックの数は？",str(len(checks)))
#     # u = User.objects.get(pk = checks[0])
#     u = User.objects.filter(pk__in = checks)
#     print(u)
#     is_deleted = u.delete()
#     # messages.success(request, "The user is deleted")

#     data = {
#         'is_exist': is_deleted
#     }
#     if data['is_exist']:
#         data['error_message'] = str(len(checks)) + '名の削除が成功しました'
#     # print('Emailバリデーション',User.objects.filter(email__iexact=email).exists())
#     # print('レスポンス', data)
#     return JsonResponse(data)
#     # return redirect('manager:user')
#     # return render(request, 'front.html')


# def load_admin_count(request):
#     # cat = request.GET.get('cat')
#     user = request.user

#     # admin_num = User.objects.filter(is_staff = True ).count()
#     admin_num = User.objects.all().filter(company_id__exact=user.company_id, is_staff = True).count()

#     print('ああああああああいいいい', admin_num)

#     return JsonResponse({"status": "ok",
#                         "admin_num": admin_num,
#                         })
"""
ユーザー表示設定
"""
class UserSettingsView(LoginRequiredMixin, UpdateView, CommonView):
    model = Company
    template_name = "accounts/user_settings.html"
    form_class = UserSettingsForm
    success_url = reverse_lazy('accounts:user')
    login_url = '/login/'

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()

        return context
    
    def form_valid(self, form):
        # 会社の登録
        company = form.save(commit=False)
        company.save()
        messages.success(self.request, "設定を変更しました")
        return redirect('accounts:user')



"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                                管理者登録(初めてのかた)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""
現状設定されているユーザーモデルを取得する
setting.pyのAUTH_USER_MODELで設定されたUserモデルを取得する？
既定値はauth.userだと思われる。
"""
User = get_user_model()

"""
ユーザー仮登録画面
仮登録ではユーザーを無効の状態で登録しておく。
入力値
　1.会社名
　2.部署名
　3.メールアドレス
　4.パスワード
1と2をCompanyモデルへ3と4をUserモデルへ登録
"""
class UserRegistration(CreateView):
    template_name = 'accounts/app_admin_reg/user_registration.html'
    form_class = UserCompanyMultiForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_name = self.request.resolver_match.url_name
        app_name = self.request.resolver_match.app_name

        context["url_name"] = url_name
        context["app_name"] = app_name

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""

        # 会社の登録
        company = form['company'].save(commit=False)

        # if company.pic_legal_person_posi == '1': #前
        #     if not company.get_pic_legal_personality_display() == "その他":
        #         company.pic_company_name = company.get_pic_legal_personality_display() + company.pic_company_name
        #     else:
        #         company.pic_company_name = company.pic_company_name


        # elif company.pic_legal_person_posi == '2': #後
        #     company.pic_company_name = company.pic_company_name + company.get_pic_legal_personality_display()

        # else:
        #     company.pic_company_name = company.pic_company_name

        company.save()


        # 仮登録と本登録の切り替えは、is_active属性を使うと簡単です。
        # 退会処理も、is_activeをFalseにするだけにしておくと捗ります。
        user = form['user'].save(commit=False)
        user.is_active = False
        user.is_activate = False
        user.company = company
        
        #パスワード生成
        password = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(8)])
        user.set_password(password)

        user.save()


        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(str(user.pk)),
            'user': user,
        }

        subject_template = get_template('accounts/mail_template/registoration/subject.txt')
        subject = subject_template.render(context)
        # TODO: テキストが読み込めない
        # subject = "test subject"

        message_template = get_template('accounts/mail_template/registoration/message.txt')
        message = message_template.render(context)

        user.email_user(subject, message)
        return redirect('accounts:user_registration_done')

"""
ユーザー仮登録画面の表示
"""
class UserRegistrationDone(TemplateView):
    """ユーザー仮登録したよ"""
    template_name = 'accounts/app_admin_reg/user_registration_done.html'

"""
ユーザー本登録の処理
仮登録で無効にしたユーザーを有効にする。
トークンの期限は1日
"""
class UserRegistrationComplete(View):
    """メール内URLアクセス後のユーザー本登録"""
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24) # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        # context = super().get_context_data(**kwargs)
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoenNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_activate:
                    # 問題なければ本登録とする
                    user.is_active = True
                    user.is_activate = True
                    user.save()
                    # return super().get(request, **kwargs)
                    # auth_user = authenticate(username=user, password=user.password)
                    # if auth_user is not None:
                    #     print("auth_user成功", auth_user)
                    # user.backend = 'users.backends.EmailModelBackend'
                    # auth_login(request, user)
                    return redirect('accounts:user_registration_addinfo' , pk=user.pk)
                    # else:
                    #     print("auth_user失敗", auth_user)
                    #     return HttpResponseBadRequest()
        return HttpResponseBadRequest()


"""
ユーザー本登録後の情報追加画面の表示
"""
class UserRegistrationAddinfo(UpdateView):
    model = User
    template_name = "accounts/app_admin_reg/user_registration_addinfo.html"
    form_class = MultiAddInfoForm
    # success_url = reverse_lazy('manager:home')


    def get_form_kwargs(self):
            kwargs = super(UserRegistrationAddinfo, self).get_form_kwargs()
            kwargs.update(instance={
                'user': self.object,
                'company': self.object.company,
            })
            return kwargs

    def form_valid(self, form):
        company = form['company'].save(commit=False)
        company.save()


        user = form['user'].save(commit=False)
        
        #ユーザーの入力したパスワードに差し替え(multiformのためform[user]を指定！)
        user.set_password(form['user'].cleaned_data['password1'])
        # 姓と名をディスプレイ名にセットする
        last_name = user.last_name
        first_name = user.first_name
        
        display_name = last_name + ' ' + first_name
        user.display_name = display_name

        # ふりがなの姓と名をディスプレイ名にセットする
        p_last_name = user.p_last_name
        p_first_name = user.p_first_name
        
        p_display_name = p_last_name + ' ' + p_first_name
        user.p_display_name = p_display_name

        # 本番登録後、is_staff属性をTrueにする。
        user.is_staff = True

        # Serviceを登録する(UpdateViewで自動的にやってくれない？)
        # servicesはquerysetになっていて、object.set()で保存できる
        # services = form.cleaned_data['service']
        # user.service.set(services)
        user.company = company
        user.save()

        return redirect('accounts:user_registration_addinfo_done')


"""
ユーザー本登録画面の表示
"""
class UserRegistrationAddinfoDone(TemplateView):
    """ユーザー本登録したよ"""
    template_name = 'accounts/app_admin_reg/user_registration_addinfo_done.html'



"""
会社登録有無確認
"""
class CompanyConfirm(FormView):
    template_name = 'accounts/app_admin_reg/company_confirm.html'
    form_class = CompanyConfirmForm

    
    def post(self, request, *args, **kwargs):
        confirm_email = request.POST['confirm_email']#フォームのメールアドレス
        # confirm_domain =  confirm_email.rsplit('@', 2)[1]#ドメイン抽出したもの

        # メール送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'email': confirm_email,
            'token': dumps(str(confirm_email))
        }

        subject_template = get_template('accounts/mail_template/company_confirm/subject.txt')
        subject = subject_template.render(context)

        message_template = get_template('accounts/mail_template/company_confirm/message.txt')
        message = message_template.render(context)
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [confirm_email]
        
        send_mail(subject, message, from_email, recipient_list)
        return redirect('accounts:company_confirm_done')
# class CompanyConfirm(FormView):
#     template_name = 'accounts/app_admin_reg/company_confirm.html'
#     form_class = CompanyConfirmForm

    
#     def post(self, request, *args, **kwargs):
#         # confirm_lastname = request.POST['confirm_lastname']
#         # confirm_firstname = request.POST['confirm_firstname']
#         # confirm_deptname = request.POST['confirm_deptname']
#         confirm_email = request.POST['confirm_email']#フォームのメールアドレス
#         confirm_domain =  confirm_email.rsplit('@', 2)[1]#ドメイン抽出したもの
#         print('どめいんのほう',confirm_domain)

#         # user_all = User.objects.filter(is_rogical_deleted=0,email__contains=confirm_domain).first()#同一ドメインのユーザー抽出
#         user_all = User.objects.filter(is_rogical_deleted=0,email__contains=confirm_domain).first()#同一ドメインのユーザー抽出

#         if user_all:
#             companys = Company.objects.filter(pic_company_name=user_all.company.pic_company_name)#ユーザーから会社名とる
#         # user_list = []
#         # for user in user_all:
#         #     user_list.append(user.company.pic_company_name)
#             print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaauser_list",companys)
#         #user_all2 = User.objects.all().order_by('company_id').distinct().values_list('company_id')
#         #print('2のほううう',user_all2[0].email)
#         #print('会社ユーザークエリ―取得',user_all)
       
#         # for user_com in user_all:
#         #     print('かいしゃあいでぃ',user_com.company_id)
#         #     email_domain = user_com.email.rsplit('@', 2)[1]
#         #     print('ふぉめいんんｎ',email_domain)
#         #     if email_domain != user_list:
#         #         user_list.append(user_com[i])
#         #     print('りすとみｔる',user_list)
        
#         print('こんふいむのほう',confirm_domain)
        
       
#         #会社有無
#         if not user_all: #会社x
#             #confirm_message = 'お問い合わせ頂いた会社は登録が確認できませんでした。'
#             confirm_result = 4
        
#         else: #会社有
#                 if companys.count() > 1:      
#                     #会社・部署Ok
#                     #confirm_message = 'お問い合わせ頂いたドメインで複数の組織が登録されています。'
#                     confirm_result =2
#                 else: #会社ok
#                     #confirm_message = 'お問い合わせ頂いた会社はすでに登録されています。'
#                     confirm_result = 1  
                
#         # if len(confirm_deptname) == 0:
#         #     if User.objects.filter(email__contains=confirm_domain).exists() and Company.objects.filter(pic_dept_name="").exists():
#         #         #会社ok
#         #         confirm_message = 'お問い合わせ頂いた会社はすでに登録されています。'
#         #         confirm_result = 1
#         #     else:
#         #         #会社x
#         #         confirm_message = 'お問い合わせ頂いた会社は登録が確認できませんでした。'
#         #         confirm_result = 4      
#         # else:
#         #     if User.objects.filter(email__contains=confirm_domain).exists() and Company.objects.filter(pic_dept_name=confirm_deptname).exists():      
#         #         #会社・部署Ok
#         #         confirm_message = 'お問い合わせ頂いた会社ならびに部署はすでに登録されています。'
#         #         confirm_result =2
#         #     elif User.objects.filter(email__contains=confirm_domain).exists() and len(confirm_deptname) > 0:
#         #         confirm_message = 'お問い合わせ頂いた部署は登録が確認できませんでした。'
#         #         confirm_result =3
#         #     else:
#         #         #会社x
#         #         confirm_message = 'お問い合わせ頂いた会社は登録が確認できませんでした。'
#         #         confirm_result = 4


#         # メール送付
#         current_site = get_current_site(self.request)
#         domain = current_site.domain
#         context = {
#             'protocol': 'https' if self.request.is_secure() else 'http',
#             'domain': domain,
#             # 'last_name': confirm_lastname,
#             # 'first_name': confirm_firstname,
#             'email': confirm_email,
#             #'message': confirm_message,
#             'result': confirm_result,
#             'token': dumps(str(companys)),

#         }

#         subject_template = get_template('accounts/mail_template/company_confirm/subject.txt')
#         subject = subject_template.render(context)

#         message_template = get_template('accounts/mail_template/company_confirm/message.txt')
#         message = message_template.render(context)
#         from_email = [settings.EMAIL_HOST_USER]
#         recipient_list = [confirm_email]
        
#         send_mail(subject, message, from_email, recipient_list)
#         return redirect('accounts:company_confirm_done')

class CompanyConfirmDone(TemplateView):
    template_name = 'accounts/app_admin_reg/company_confirm_done.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "登録状況照会ページへのリンクをご入力いただいたメールアドレスに送信しました。"
        return context

class ConfirmResult(TemplateView):
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*15*0)  # デフォルトでは15分以内
    template_name = 'accounts/app_admin_reg/confirm_result.html'

    def get_context_data(self, **kwargs):
        token = kwargs.get('token')
        confirm_mail = loads(token)
        confirm_domain = confirm_mail.rsplit('@', 2)[1]#ドメイン抽出したもの
        user_first = User.objects.filter(is_rogical_deleted=0,email__contains=confirm_domain).first()#同一ドメインのユーザー抽出
        user_get = User.objects.get(is_rogical_deleted=0,email=confirm_mail)
        if user_first:
            # companys = Company.objects.filter(pic_company_name=user_first.company.pic_company_name)#ユーザーから会社名とる
            companys = Company.objects.filter(pic_company_name=user_first.company.pic_company_name)#ユーザーから会社名とる

        #result=1会社あり、部署なし,登録あり
        #result=2会社あり、部署なし,登録なし
        #result=3会社あり、部署あり,登録あり （現状result=1とする。）
        #result=4会社あり、部署あり,登録なし
        #result=5会社なし

        #会社有無
        if not user_first: #会社x
            #confirm_message = 'お問い合わせ頂いた会社は登録が確認できませんでした。'
            confirm_result = 5

        else: #会社有
                if companys.count() > 1:
                    if user_get:
                        #confirm_message = '複数の組織が登録されています。'
                        confirm_result =3
                    else:
                        #confirm_message = '複数の組織が登録されています。ユーザー登録をリクエストしますか'
                        confirm_result =4
                else: #会社ok
                    if user_get:
                        #confirm_message = '会社ならびにユーザーはすでに登録されています。'
                        confirm_result = 1
                    else:
                        #confirm_message = '会社はすでに登録されています。ユーザー登録をリクエストしますか'
                        confirm_result = 2

        context = super().get_context_data(**kwargs)
        context = {
            'email': confirm_mail,
            'companys': companys,
            'result': confirm_result,
            'user_get': user_get
        }

        return context

"""
ユーザー登録リクエスト
"""
class ConfirmRequestView(View):
    template_name = 'accounts/app_admin_reg/confirm_request_done.html'
    
    def post(self, request, *args, **kwargs):
        co_id = request.POST.get('company_id')
        email = request.POST.get('email')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        print('リクエストいちらん',request.POST)
        print("かいしゃあいでぃーーは＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊", co_id)
        print("メールは＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊", email)
        print("姓は＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊", last_name)
        print("名は＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊＊", first_name)

        manager = User.objects.filter(company_id = co_id,is_staff = 1).first()
        manager_mail = manager.email

        # メール送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'email':email,
            'last_name':last_name,
            'first_name':first_name,
            'manager':manager,
            'manager_mail':manager_mail,
        }

        subject_template = get_template('accounts/mail_template/confirm_request/subject.txt')
        subject = subject_template.render(context)

        message_template = get_template('accounts/mail_template/confirm_request/message.txt')
        message = message_template.render(context)
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [manager_mail]
        
        send_mail(subject, message, from_email, recipient_list)
        return redirect('accounts:confirm_request_done')

class ConfirmRequestDone(TemplateView):
    template_name = 'accounts/app_admin_reg/confirm_request_done.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "管理ユーザーへ登録リクエストを送信しました。"
        return context

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                                パスワードを忘れた方
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

"""
ユーザーがパスワード忘れた際のパスワードリセット
"""
class PasswordReset(PasswordResetView):
    subject_template_name = 'accounts/mail_template/password_reset/subject.txt'
    email_template_name = 'accounts/mail_template/password_reset/message.txt'
    template_name = 'accounts/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')

"""
ユーザーがパスワード忘れた際のパスワードリセット完了
"""
class PasswordResetDone(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

"""
パスワードリセット時の新パスワード入力
"""
class PasswordResetConfirm(PasswordResetConfirmView):
    form_class = MySetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')
    template_name = 'accounts/password_reset_confirm.html'

"""
パスワードリセット時の新パスワード入力完了ページ
"""
class PasswordResetComplete(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                               問い合わせフォーム
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
#お問い合わせ受付
class ContactFormView(LoginRequiredMixin, FormView, CommonView):
    template_name = 'accounts/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('accounts:contact_done')
    login_url = '/login/'

    def form_valid(self, form):
        #　ログインユーザーを取得してユーザーのメールアドレスを使用
        current_user = self.request.user
        c_name = current_user.last_name + ' ' + current_user.first_name
        #c_company = ''
        usercompany = Company.objects.get(id=current_user.company_id)
       
        if usercompany.pic_legal_person_posi == '1':
            c_company = usercompany.get_pic_legal_personality_display() + usercompany.pic_company_name
        elif usercompany.pic_legal_person_posi == '2':
            c_company = usercompany.pic_company_name + usercompany.get_pic_legal_personality_display()
        else:
            c_company = usercompany.pic_company_name

        form.send_email(name=c_name, email=current_user.email, company=c_company)
        
        return super().form_valid(form)

#問い合わせ完了
class ContactDoneView(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'accounts/contact_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "メールが送信されました。お問合せありがとうございます。"
        return context