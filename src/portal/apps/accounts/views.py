from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic import View, ListView, DetailView, TemplateView, FormView, CreateView, UpdateView, DeleteView
from django.views.generic.base import ContextMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from accounts.forms import LoginForm, CompanyUpdateForm, MyUserCreationForm, MyUserChangeForm, CustomPasswordChangeForm, MultiAddInfoForm, UserCompanyMultiForm, MyPasswordResetForm, MySetPasswordForm, UserChangeForm, UserSettingsForm, ContactForm, CompanyConfirmForm, CompanyOnlyUpdateForm, MyPasswordChangeForm,TransferCompleteForm

# from accounts.forms import LoginForm, CompanyUpdateForm, MyUserCreationForm, MyUserChangeForm, CustomPasswordChangeForm, MultiAddInfoForm, UserCompanyMultiForm, MyPasswordResetForm, MySetPasswordForm, UserChangeForm, UserSettingsForm, ContactForm, CompanyConfirmForm, CompanyOnlyUpdateForm, MyPasswordChangeForm,UploadFileForm,TransferCompleteForm
from django.urls import reverse_lazy

# アクセスURL生成
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps

# テンプレート情報取得
from django.template.loader import get_template

# settings情報の取得
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.models import User, Company, Messages, Service, Notification,Read,File,Stripe
from contracts.models import Contract, Plan, PaymentMethod, Estimates

from django.db.models import Q

from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect

from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta
import pytz


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


# mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin




# 別ページでログイン中の他社ユーザーアクセス制限
class OnlyOurUserMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        user_instance = self.get_object()
        return user_instance.company_id == self.request.user.company_id

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
        today = datetime.now(timezone.utc)
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user
        not_paymented = Contract.objects.filter(company=current_user.company, payment__is_paymented=False)
        context["not_paymented"] = not_paymented
        #インフォメーション
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

        email_list = current_user.email.rsplit('@', 1)
        # メールアドレスをユーザ名とドメインに分割
        email_domain = email_list[1]

        url_name = self.request.resolver_match.url_name
        app_name = self.request.resolver_match.app_name
        if no_read > 99 :
            context["no_read"] = "99+"

        else:
            context["no_read"] = no_read
        
        context["read_info"] = read_info
        context["url_name"] = url_name
        context["app_name"] = app_name
        context["all_informations"] = all_informations
        context["maintenance_informations"] = maintenance_informations
        context["notice_informations"] = notice_informations

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
        service = Service.objects.all().prefetch_related(Prefetch("contract_set", queryset=Contract.objects.filter(company=current_user.company))).order_by('number')
        
        return service

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        url_name = self.request.resolver_match.url_name
        current_user_id = self.request.user.pk
        current_user = self.request.user
        userlist = User.objects.filter(company_id=current_user.company_id,is_rogical_deleted=False).count()
        today = datetime.now(timezone.utc)
        # 有効期限迫った見積りリストを渡す
        estimates = Estimates.objects.filter(user=current_user,temp_check=False,is_use=False)
        limit_est = []
        if estimates:
            for estimate in estimates:
                one_week_ago = estimate.expiration_date - relativedelta(weeks=1)
                if one_week_ago < today:
                    limit_est.append(estimate.num)
        #クレジットカード登録有無
        credit = Stripe.objects.filter(company=current_user.company).first()
        if credit:
            context["credit"] = 'true'

        # 期限迫った契約リストを渡す
        limit_contracts = Contract.objects.filter(company=current_user.company,is_autocheckout=False,status="2")
        limit_cont = []
        limit_cont_date = []
        if limit_contracts:
            for limit_contract in limit_contracts:
                one_month_ago = limit_contract.contract_end_date - relativedelta(months=1)
                if one_month_ago < today:
                    limit_cont.append(limit_contract.service.name)

        if len(limit_est) > 0:
            print('みつもりきげんちかいもの',limit_est)
            context["limit_est"] = limit_est

        if len(limit_cont) > 0:

            context["limit_cont"] = limit_cont
            print('けいやくきげんちかいもの',limit_cont)

        context["url_name"] = url_name
        context["userlist"] = userlist

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
お知らせページ
"""
class InfomationView(LoginRequiredMixin, TemplateView,CommonView):
    template_name = 'accounts/infomation.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        print('インフォメーションがうごいた')
        context = super().get_context_data(**kwargs)
        user = self.request.user
        info = Notification.objects.get(id=self.kwargs['pk'])
        if Read.objects.filter(read_user=user,notification_id=info).exists()==False:
            read = Read.objects.create(read_user=user,notification_id=info)
            read.save()
            
            #追記
            today = datetime.now(timezone.utc)

            read2 = Read.objects.filter(read_user=user).count()
            if read2 > 0:
                info_all = Notification.objects.filter(Q(target_user_id = None)|Q(target_user_id = user),start_date__lte = today).distinct().count()
                no_read = info_all - read2
                if no_read > 99 :
                    context["no_read"] = "99+"
                else:
                    context["no_read"] = no_read
        
        context["user"] = user
        context["info"] = info
        return context



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
        company = Company.objects.filter(pk=current_user.company.id).first()
        context["company"] = company
        return context

    def form_valid(self, form):

        # 会社の登録
        company = form.save(commit=False)

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
        company = Company.objects.filter(pk=current_user.company.id).first()
        context["company"] = company
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
メール通知ON/OFF
"""
class SendMailAjaxView(View):
    def post(self, request):
        user = self.request.user
        mail_choiced = request.POST.get('mail_choiced')
        #存在確認
        if mail_choiced == "1":
            user.is_send_mail = True
            data = {
                'judge':'mail_true',
            }
        else:
            user.is_send_mail = False
            data = {
                'judge':'mail_false'
            }
        user.save()

        return JsonResponse(data,safe=True)

"""
キャンセル処理
"""
class Cancel(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        # プロファイル更新時のキャンセル
        if self.kwargs['str'] == "update_profile":
            print('きゃんせるにすすんだ')
            # 変更対象のオブジェクトを取得
            company = Company.objects.filter(id=self.kwargs['pk']).first()
            user = User.objects.filter(id=self.kwargs['pk']).first()
            if company:
                # バージョンフラグをNoneとする
                company.version = None
                # 変更者のIDをNoneとする
                company.change_user = None
                # 上書きフラグをNoneとする
                company.change_row = None
                # 保存
                company.save()
                
                return HttpResponseRedirect(reverse('accounts:companyprofile'))
            elif user:
                print('ユーザーキャンセル進んだ')
                # 排他処理フラグをFalseに
                user.is_updating = False
                # 保存
                user.save()
                return HttpResponseRedirect(reverse('accounts:user'))
                
            else:
                return HttpResponseRedirect(reverse('accounts:home'))


        


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
イメージ削除(Ajax用)
"""
def delete_image(request):
    print('削除Ajaxにきた')
    gen_image = request.POST.get('gen_image')
    print('げんいめーーーーーーじ',gen_image)
    file = File.objects.filter(file=gen_image).first()
    print('ファイル来てる？？？？？？？？',file)
    user = User.objects.filter(image=file.id).first()
    user.image = None
    user.save()
    is_deleted = file.delete()

    data = {
        'is_exist': is_deleted
    }
    if data['is_exist']:
        data['error_message'] = '現在設定している画像を削除しました'

    return JsonResponse(data)


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
        return kwargs

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).first()
        if current_user.image:
            gen_image = File.objects.filter(pk=current_user.image.id)
            context["gen_image"] = current_user.image
        return context

    def form_valid(self, form):
        old_data = User.objects.filter(pk=self.request.user.id).first()

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
        old_image = ''

        if old_data.image:
            old_image = File.objects.filter(pk=old_data.image.id)
        
        if 'up_file_id' in self.request.session:
            
            user.image = File.objects.filter(id=self.request.session['up_file_id']).first()
            if old_image:
                old_image.delete()

        user.save()
        
        return redirect('accounts:user_infomation')

"""
プロファイル画像変更
"""
import json
class ImageImportView(View):
    def post(self, request, *args, **kwargs):
        upload_file = self.request.FILES.get('file')

        file, created = File.objects.get_or_create(name=upload_file.name,size=upload_file.size,file=upload_file,)

        file.save()
        up_file_id = file.id

        # 保存したファイルをセッションへ保存
        up_file_id_json = json.dumps(up_file_id)
        self.request.session['up_file_id'] = up_file_id_json
        print('イメージのセッション作成！！')
        # 何も返したくない場合、HttpResponseで返す
        return HttpResponse('OK')
   
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
        contracts = Contract.objects.filter(user__company_id=user.company_id)

        context['users'] = users
        context['contracts'] = contracts

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

        user.color_num = random.randrange(26)

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
class UserUpdateView(LoginRequiredMixin, OnlyOurUserMixin, UpdateView, CommonView):
    model = User
    template_name = "accounts/user_update.html"
    form_class = MyUserChangeForm
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not self.request.user.is_staff:
            if self.request.user.company.profile_change == '2':
                return render(request, '403.html', status=403)

        return super().dispatch(request, *args, **kwargs)
    
    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UserUpdateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs
    # ユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_user = User.objects.filter(pk=self.kwargs['pk']).first()
        #排他処理のタイムスタンプを上書きする
        target_user.last_updated = datetime.now(timezone.utc)
        target_user.is_updating = True
        target_user.save()
        
        if target_user.image:
            context["gen_image"] = target_user.image
        return context

    def form_valid(self, form):
        old_data = User.objects.filter(pk=self.kwargs['pk']).first()

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
        old_image = ''

        if old_data.image:
            print('toumaのイメージある')
            old_image = File.objects.filter(pk=old_data.image.id)
        
        if 'up_file_id' in self.request.session:
            print('toumaのせっしょん')

            user.image = File.objects.filter(id=self.request.session['up_file_id']).first()
            if old_image:
                old_image.delete()
        user.is_updating = False
        # 保存
        user.save()

        if self.request.user.is_authenticated and self.request.user.is_active and self.request.user.is_staff:
            return redirect('accounts:user')
        else:
            return redirect('accounts:home')

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
ユーザーが自身のパスワード変更
"""
class PasswordChange(LoginRequiredMixin, PasswordChangeView, CommonView):
    template_name = "accounts/password_change_for_self.html"
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('accounts:password_change_done')
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not self.request.user.is_staff:
            if self.request.user.company.pass_change == '2':
                return render(request, '403.html', status=403)

        return super().dispatch(request, *args, **kwargs)



"""
ユーザー自身のパスワード変更完了
"""
class PasswordChangeDone(LoginRequiredMixin, PasswordChangeDoneView, CommonView):
    template_name = 'accounts/password_change_done_for_self.html'
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
         
        data = {
        'is_exist': "true"
        }
    
        if data['is_exist']:
            data['error_message'] = str(len(checks)) + '名の削除が成功しました'
        return JsonResponse(data)


def load_admin_count(request):
    # cat = request.GET.get('cat')
    user = request.user

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


#     return JsonResponse({"status": "ok",
#                         "admin_num": admin_num,
#                         })
"""
ユーザー情報設定
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
        print('フォームの中身',form)
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

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     url_name = self.request.resolver_match.url_name
    #     app_name = self.request.resolver_match.app_name

    #     context["url_name"] = url_name
    #     context["app_name"] = app_name

    #     return context

    # def post(self, request, *args, **kwargs):
    #     """
    #     Handle POST requests: instantiate a form instance with the passed
    #     POST variables and then check if it's valid.
    #     """
    #     form = self.get_form()
    #     print('ふぉーーーむ・・・・・・',form)
    #     if form.is_valid():
    #         return self.form_valid(form)
    #     else:
    #         return self.form_invalid(form)

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 会社の登録
        company = form['company'].save(commit=False)

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

        user.color_num = random.randrange(26)

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

"""
会社登録有無確認送信後
"""
class CompanyConfirmDone(TemplateView):
    template_name = 'accounts/app_admin_reg/company_confirm_done.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "登録状況照会ページへのリンクをご入力いただいたメールアドレスに送信しました。"
        return context


"""
ユーザー登録リクエスト
"""
class ConfirmRequestView(FormView):
    template_name = 'accounts/app_admin_reg/confirm_request.html'

    def get_context_data(self, **kwargs):

        token = self.kwargs.get('token')
        confirm_mail = loads(token)
        confirm_domain = confirm_mail.rsplit('@', 2)[1]#ドメイン抽出したもの
        user_first = User.objects.filter(is_rogical_deleted=0,email__contains=confirm_domain).first()#同一ドメインのユーザー抽出
        if user_first:
            companys = Company.objects.filter(pic_company_name=user_first.company.pic_company_name)#ユーザーから会社名とる
            #result=1会社○、部署×,登録○
            #result=2会社○、部署×,登録×
            #result=3会社○、部署○,登録○ 
            #result=4会社○、部署○,登録×
            #result=5会社×

        #会社有無check!-----------------

        #会社NIL
        if not user_first: 
            confirm_result = 5

            context = {
            'email': confirm_mail,
            'result': confirm_result,
            }

        #会社有
        else: 
            user_get = User.objects.filter(is_rogical_deleted=0,email=confirm_mail)
            if user_get:
                if companys.count() > 1:
                    confirm_result =3
                else:
                    confirm_result = 1

                context = {
                    'email': confirm_mail,
                    'companys': companys,
                    'result': confirm_result,
                    'user_get': user_get
                }
            else:
                if companys.count() > 1:
                    confirm_result =4
                else:
                    confirm_result = 2

                context = {
                    'email': confirm_mail,
                    'companys': companys,
                    'result': confirm_result,
                }

        return context

    
    def post(self, request, *args, **kwargs):
        co_id = request.POST.get('company_id')
        email = request.POST.get('email')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        msg = request.POST.get('message')

        manager = User.objects.get(company_id = co_id,is_staff = 1) #仮の送信先
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
            'msg':msg
        }

        subject_template = get_template('accounts/mail_template/confirm_request/subject.txt')
        subject = subject_template.render(context)

        message_template = get_template('accounts/mail_template/confirm_request/message.txt')
        message = message_template.render(context)
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [manager_mail]
        
        send_mail(subject, message, from_email, recipient_list)
        return redirect('accounts:confirm_request_done')

"""
ユーザー登録リクエスト送信後
"""
class ConfirmRequestDone(TemplateView):
    template_name = 'accounts/app_admin_reg/confirm_request_done.html'

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

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                               振込完了フォーム
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class TransferCompleteView(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'accounts/transfer_complete.html'
    def post(self,request):
        user = self.request.user
        company = Company.objects.get(pk=user.company_id)
        name = user.last_name + user.first_name

        #会社名作成
        if company.pic_corp_class == "1":
            if company.pic_legal_personality == '99' or company.pic_legal_personality == '':
                company_name = company.pic_company_name
            else:
                if company.pic_dept_name:
                    if company.pic_legal_person_posi == '1':
                        company_name = '{} {} {}'.format(company.get_pic_legal_personality_display(), company.pic_company_name, company.pic_dept_name)
                    else:
                        company_name = '{} {} {}'.format(company.pic_company_name, company.get_pic_legal_personality_display(), company.pic_dept_name)
                else:
                    if company.pic_legal_person_posi == '1':
                        company_name = '{} {}'.format(company.get_pic_legal_personality_display(), company.pic_company_name)
                    else:
                        company_name = '{} {}'.format(company.pic_company_name, company.get_pic_legal_personality_display())

        t_bank = self.request.POST.get('t_bank')
        t_date = self.request.POST.get('t_date')

            
        subject = '【CloudLabポータル】振込完了通知'
        message = 'メールアドレス：　{email}\n' \
                '会社名：　{company_name}\n' \
                '名前：　{name}\n' \
                '振込先：　{t_bank}\n' \
                '振込日：　{t_date}\n'.format(email=user.email,
                                    company_name=company_name,
                                    name=name,
                                    t_bank=t_bank,
                                    t_date=t_date)

        from_email = settings.EMAIL_HOST_USER
        recipient_list = [
            "koharu.y.1120@gmail.com",
            "koharu.yano@yui.okinawa"
        ] #受信者リスト
        try:
            send_mail(subject, message, from_email, recipient_list)
            
        except BadHeaderError:
            return HttpResponse("無効なヘッダが検出されました。")
        else:
            data = {
                'message': "送信が完了しました",
                }
        return JsonResponse(data)
