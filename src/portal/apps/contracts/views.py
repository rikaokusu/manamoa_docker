from django.conf import settings
from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic import View, ListView, DetailView, TemplateView, FormView, CreateView, UpdateView, DeleteView

from contracts.forms import EstimateStep1Form,EstimateStep2Form,EstimateStep3Form,OfferStep1Form,OfferStep2Form,UpdateContractNochangeStep1Form,UpdateContractChangeStep1Form,UpdateContractChangeStep2Form,EstimateCopyForm

from accounts.models import User, Company, Service, Messages, Stripe,Notification,Read
from contracts.models import Contract, Plan, PaymentMethod, Estimates, Discount
from payment.models import Payment
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect
from django.template.loader import get_template
#見積PDF化
import pdfkit
import io
import os
from django.template.loader import render_to_string
import urllib.request
import re
# 有効期限の保存
from datetime import datetime, date, timedelta, timezone

from pytz import timezone
from dateutil.relativedelta import relativedelta
import pytz

# バリデーション用
from django.http import JsonResponse

# Mixin
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
# QuerySetのセッションへの保存
from django.core import serializers

from django.db.models import Q
from django.db.models import Prefetch

from json import JSONEncoder
from uuid import UUID

from django.core.exceptions import PermissionDenied


#バーコード生成用
import barcode
from barcode.writer import ImageWriter
import base64
import imgkit

old_default = JSONEncoder.default

def new_default(self, obj):
    if isinstance(obj, UUID):
        return str(obj)
    return old_default(self, obj)

JSONEncoder.default = new_default
# config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\bin\\wkhtmltopdf.exe')
# pdfkit.from_url('http://google.com', 'out.pdf')


# 全てで実行させるView
class CommonView(ContextMixin):
    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user
        not_paymented = Contract.objects.filter(company=current_user.company, payment__is_paymented=False)
        context["not_paymented"] = not_paymented
        email_list = current_user.email.rsplit('@', 1)
        # メールアドレスをユーザ名とドメインに分割
        email_domain = email_list[1]

        url_name = self.request.resolver_match.url_name
        app_name = self.request.resolver_match.app_name
        context["url_name"] = url_name
        context["app_name"] = app_name

        context["current_user"] = current_user
        context["email_domain"] = email_domain

        #infomation用
        today = datetime.now()

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

        return context



"""
試用登録
"""
# @method_decorator(login_required, name = 'dispatch')
class TrialContractRegAjaxView(View):
    def post(self, request):
        # model = Contract
        service_id = request.POST.get('service')
        print('試用サービスIDはーーー',service_id)
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        # 保存する対象のUserオブジェクトをPKを使って取得
        user = User.objects.get(pk = request.user.pk)
        print('ユーザーオブジェクトは？', user)

        # 保存する対象のServiceオブジェクトをPKを使って取得
        # service = Service.objects.get(pk__iexact = service_id)
        service = Service.objects.get(pk = service_id)
        print('サービス名は＿＿＿？？', service.id)

        # サービスに関連するプランを取得
        plan = Plan.objects.filter(service=service, is_option=False, is_trial=True).first()
        print('プランは？', plan)

        # サービスに関連するオプションを取得
        option = Plan.objects.filter(service=service, is_option=True, is_trial=True).first()
        print('オプションは？', option)

        # 文字列を日付型へ変換
        # start_date = datetime.datetime.strptime(start_date_str, '%Y/%m/%d')
        start_date = datetime.strptime(start_date_str, '%Y/%m/%d')

        # 変換した日付の時刻を除去
        start_date = start_date.date()

        # 文字列を日付型へ変換
        # end_date = datetime.datetime.strptime(end_date_str, '%Y/%m/%d')
        end_date = datetime.strptime(end_date_str, '%Y/%m/%d')
        # 変換した日付の時刻を除去
        end_date = end_date.date()

        # TODO: 既存存在確認を追加
        contract, created = Contract.objects.get_or_create(user=user, service=service, status="1", contract_start_date=start_date, contract_end_date=end_date, company=user.company)
        contract.plan = plan
        if option:
            contract.option = option
        contract.save()

        if created:
            # obj.save()
            data = {
                'is_created': created,
                'messages':'登録しました'
            }
        else:
            data = {
                'is_created': "false",
                'messages':'登録に失敗しました'
            }

        return JsonResponse(data)



"""
契約一覧画面
この画面から契約と見積の一覧が見える。
"""
class ContractIndexView(LoginRequiredMixin, ListView, CommonView):
    model = Contract
    template_name = 'contracts/contract.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        print('コンテキストデータ・・・・・・・・・・・・')
        context = super().get_context_data(**kwargs)
        current_user_id = self.request.user.pk
        context["contracts"] = Contract.objects.filter(user=current_user_id).prefetch_related('estimate', 'payment').order_by('status')
        context["status_3"] = Contract.objects.filter(user=current_user_id,status='3').prefetch_related('estimate', 'payment')
        context["status_4"] = Contract.objects.filter(user=current_user_id,status='4').prefetch_related('estimate', 'payment')


        # contracts = Contract.objects.extra(
        #     tables=["contracts_plan",],
        #     where=['''contracts_contract.plan=contracts_plan.id''']
        # )

        Contract.objects.extra(tables=['plan'],where=['contracts.plan_id=plan.id']).query

        context["contracts"] = Contract.objects.filter(user=self.request.user.pk).order_by('status')

        # 見積テーブルの表示
        # TODO: 契約に紐づく形で更新用見積もり書を作成する
        context["estimates"] = Estimates.objects.filter(user=current_user_id)
        context["estimates_is_update"] = Estimates.objects.filter(user=current_user_id, is_update="True")
        return context

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                                        見積機能
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""
見積一覧画面
この画面から見積の一覧が見える。
"""
class EstimateIndexView(LoginRequiredMixin, ListView, CommonView):
    model = Estimates
    template_name = 'contracts/estimate/estimate.html'
    login_url = '/login/'

    def get_queryset(self):
        current_user_id = self.request.user.pk
        current_user = self.request.user

        # サービステーブルから該当するサービスで契約テーブルに値があるか数値を取得
        # service = Service.objects.annotate(num_contract=Count('contract', filter=Q(contract__user_id=current_user_id)))
        # estimate1 = Estimates.objects.filter(user=current_user_id,is_use=1)

        estimate = Estimates.objects.all().prefetch_related(Prefetch("contract_set", queryset=Contract.objects.filter(user=current_user)))

        return estimate

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user_id = self.request.user.pk

        # 見積テーブルの表示
        # TODO: 契約に紐づく形で更新用見積もり書を作成する
        context["contracts"] = Contract.objects.filter(user=current_user_id,status=2)
        context["estimates_is_use"] = Estimates.objects.filter(user=current_user_id,is_use=1)
        context["estimates"] = Estimates.objects.filter(user=current_user_id,temp_check=False)
        context["estimates_is_update"] = Estimates.objects.filter(user=current_user_id, is_update="True")
        return context

"""
戻るボタンの処理
"""
#★部分は遷移するURLでPKなどを指定している場合に、設定する方法です。
class EstimateReturnView(View):
    def get(self, request, *args, **kwargs):
        print('もどるしょり',self.request.session)
        # 不正な遷移をチェック
        if not 'page_num' in self.request.session:
            raise PermissionDenied
        page_num = self.request.session['page_num']

        if 'estimate_step1_id' in self.request.session:

            est = self.request.session['estimate_step1_id']

            if page_num == 2:
                self.request.session['page_num'] = 1

                return HttpResponseRedirect(reverse('contracts:estimate_step1'))
            elif page_num == 3:
                self.request.session['page_num'] = 2

                return HttpResponseRedirect(reverse('contracts:estimate_step2'))
            elif page_num == 4:
                self.request.session['page_num'] = 3

                return HttpResponseRedirect(reverse('contracts:estimate_step3'))

        if 'estimate_copy1_id' in self.request.session:
            estimate_id = self.request.session['estimate_id']
            return HttpResponseRedirect(reverse('contracts:estimate_copy1', kwargs={'pk': estimate_id}))
        
        if 'contract_update_step1' in self.request.session:
            est = self.request.session['contract_update_step1']
            return HttpResponseRedirect(reverse('contracts:cont_update_nochange_step1', kwargs={'pk': contract_id}))

        if 'contract_update_change1' in self.request.session:
            est = self.request.session['contract_update_change1']

            if page_num == 2:
                self.request.session['page_num'] = 1
                contract_id = self.request.session['contract_id']

                return HttpResponseRedirect(reverse('contracts:cont_update_change_step1_1', kwargs={'pk': contract_id}))
        if 'offer_step1_id' in self.request.session:
            est = Estimates.objects.filter(pk=self.request.session['offer_step1_id']).first()
            if page_num == 2:
                self.request.session['page_num'] = 1
                return HttpResponseRedirect(reverse('contracts:offer_step1', kwargs={'pk': est.service.id}))
            if page_num == 3:
                self.request.session['page_num'] = 2
                return HttpResponseRedirect(reverse('contracts:offer_step2'))

        
        # if page_num == 2:
        #     # ★ページ情報をセッションに保存しておく
        #     self.request.session['page_num'] = 1
        #     return HttpResponseRedirect(reverse('tasks:step2', kwargs={'managetask_id': managetask_id}))


"""
キャンセル処理
"""
class EstimateCancelView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        # セッションに「estimate_step1_id」があれば、取得した行を削除
        if 'estimate_step1_id' in request.session or 'estimate_copy1_id' in request.session:
            if 'estimate_step1_id' in request.session:
                estimate = Estimates.objects.get(pk = request.session['estimate_step1_id'])
                estimate.delete()
            if 'estimate_copy1_id' in request.session:
                estimate = Estimates.objects.get(pk = request.session['estimate_copy1_id'])
                estimate.delete()
            # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
            for key in list(self.request.session.keys()):
                if not key.startswith("_"):
                    del self.request.session[key]

            return HttpResponseRedirect(reverse('contracts:estimate'))
        elif 'offer_step1_id' in request.session:

            estimate = Estimates.objects.get(pk = request.session['offer_step1_id'])
            estimate.delete()

            # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
            for key in list(self.request.session.keys()):
                if not key.startswith("_"):
                    del self.request.session[key]

            return HttpResponseRedirect(reverse('accounts:home'))
        else:

            # セッションに「contract_update_change1」があれば、取得した行を削除
            if 'contract_update_change1' in request.session:
                print('変更なしのキャンセルに進んだ')
                estimate = Estimates.objects.get(pk = request.session['contract_update_change1'])
                estimate.delete()
            if 'contract_update_step1' in request.session:
                estimate = Estimates.objects.get(pk = request.session['contract_update_step1'])
                estimate.delete()
            # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
            for key in list(self.request.session.keys()):
                if not key.startswith("_"):
                    del self.request.session[key]

            return HttpResponseRedirect(reverse('contracts:contract'))

        return HttpResponseRedirect(reverse('contracts:contract'))


"""
Ajax受信用
"""
# class EstimateA(View):

#     def post(self,request):
#         checks = request.POST.getlist('checks[]')
#         # u = User.objects.get(pk = checks[0])
#         users = User.objects.filter(id__in = checks)
#         for user in users:
#             user.is_rogical_deleted = True
#             user.save()

#         #is_deleted = u.delete()
#         # messages.success(request, "The user is deleted")

#         data = {
#         'is_exist': "true"
#         }

#         if data['is_exist']:
#             data['error_message'] = str(len(checks)) + '名の削除が成功しました'
#         return JsonResponse(data)


"""
見積作成(ステップ①)
"""
class EstimateStep1(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/estimate/step1.html'
    form_class = EstimateStep1Form
    login_url = '/login/'


    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(EstimateStep1, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_initial(self):
        initial={}
        if 'estimate_step1_id' in self.request.session:
            est_obj = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).first()
            initial={
                'start_day': est_obj.start_day,
                'service': est_obj.service,
                'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
            }
        else:
            initial={
                'service': Service.objects.filter(pk=self.request.session.get('service', None)).first(),
                'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
            }

            # 返す
        return initial

    def form_valid(self, form):
        if not 'estimate_step1_id' in self.request.session:
            # フォームからDBのオブジェクトを仮生成（未保存）
            estimate_step1 = form.save(commit=False)
        else:
            estimate_step1 = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).first()

        # ユーザーを保存
        estimate_step1.user = self.request.user

        # 本日日付
        today = datetime.now()
        print('今日の日付///////////////////////////',today)
        # 作成日を登録
        estimate_step1.created_date = today

        after_one_month = today + relativedelta(months=1,days=-1,hour=23,minute=59,second=59,microsecond=999999)
        # expired_at = datetime.datetime.combine(after_one_month) - datetime.timedelta(seconds=1)


        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1)
        # estimate_step1.expiration_date = expiration_date.date()
        # estimate_step1.expiration_date = expired_at
        estimate_step1.expiration_date = after_one_month

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = today.strftime('%Y%m%d')
        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        date = str(estimate_step1.created_date)
        date2 = code_regex.sub('', date)
        last_id = date2[8:14]

        if int(last_id) <= 9:
            last_id = str("000") + str(last_id)
        elif int(last_id) <= 99:
            last_id = str("00") + str(last_id)
        elif int(last_id) <= 999:
            last_id = str("0") + str(last_id)
        else:
            last_id = str(last_id)

        estimate_num = day_number + last_id
        estimate_step1.num = estimate_num


        # 契約終了日の設定
        # 契約開始日から終了日を生成(+1年)
        start_date = form.cleaned_data['start_day']

        # start_date = form.cleaned_data['start_day'] + relativedelta(hour=0,minute=0,second=0,microsecond=0)
        print('すたーとでいと',start_date)
        start_day = start_date

        # start_day = form.cleaned_data['start_day']
        end_day =  start_day + relativedelta(years=1,hour=23,minute=59,second=59,microsecond=999999) - relativedelta(days=1)
        estimate_step1.end_day = end_day

        # 保存
        estimate_step1.save()

        # POSTで送信された設定された宛先ユーザーを取得
        service = form.cleaned_data['service']

        # POST送信された情報をセッションへ保存
        self.request.session['service'] = service.id

        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['estimate_step1_id'] = estimate_step1.id

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 2

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('contracts:estimate_step2'))  


"""
割引の適用有無チェック
"""

class DiscountCheckView(View, CommonView, LoginRequiredMixin):
    template_name = 'contracts/step2.html'

    def post(self, request):
        print('チェック開始')
        discount_code = self.request.POST.get('discount_code')
        if 'estimate_step1_id' in self.request.session:
            est_obj = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).first()
        if 'offer_step1_id' in self.request.session:
            est_obj = Estimates.objects.filter(pk = self.request.session['offer_step1_id']).first()

        if est_obj.discount:
            print('クーポン登録すみ')
            code_target = Discount.objects.filter(pk=est_obj.discount.id).first()
            #適用
            data = {
            'judge':"success",
            'message': "クーポンを適用しました",
            'code': code_target.coupon_code,
            'coupon_name':code_target.name,
            'discount_rate': code_target.discount_rate,
            }
        else:
            payment_check = self.request.POST.get('payment_check')
            print('めそっどのなかみ222',type(payment_check))
            
            user = self.request.user
            company = Company.objects.get(pk=user.company_id)
            code_target = Discount.objects.filter(coupon_code=discount_code).first()
            contract_list = Contract.objects.filter(user__company=company)
            today = datetime.now()

            print('対象のコードをさがした')
            if not code_target: #コード見つからない
                data = {
                        'judge':"fail",
                        'message':'入力された割引コードは無効です。nocode'
                    }
            else: #コードは存在
                if contract_list and code_target.id in contract_list: #会社の契約書が存在
                    data = {
                        'judge':"fail",
                        'message':'入力された割引コードはすでに使用済みです。'
                    }
                elif code_target.payment is not payment_check:
                    data = {
                        'judge':"fail",
                        'message':'入力された割引コードは無効です。paymenterror'
                    }
                elif code_target.expiration_date.date() < today.date():
                    data = {
                        'judge':"fail",
                        'message':'入力された割引コードは引換え期限が過ぎています。'
                    }
                elif code_target.limit_all:
                    if code_target.limit_all <= code_target.number_of_use:
                        data = {
                            'judge':"fail",
                            'message':'入力された割引コードは引換え可能回数の上限に達しました。'
                        }
                    else:
                        data = {
                        'judge':"success",
                        'message': "クーポンを適用しました",
                        'code': code_target.coupon_code,
                        'coupon_name':code_target.name,
                        'discount_rate': code_target.discount_rate,
                        }
                else:
                    #適用
                    data = {
                    'judge':"success",
                    'message': "クーポンを適用しました",
                    'code': code_target.coupon_code,
                    'coupon_name':code_target.name,
                    'discount_rate': code_target.discount_rate,
                    }

        return JsonResponse(data)



"""
見積作成(ステップ②)
"""
class EstimateStep2(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/estimate/step2.html'
    form_class = EstimateStep2Form
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not 'page_num' in self.request.session:
            return render(request, '406.html', status=406)

        if not self.request.session['page_num'] == 2:

            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)
    


    # def get_initial(self):
    #     # estimates = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
    #     initial={
    #             'service': Service.objects.filter(pk=self.request.session.get('service', None)).first(),
    #             'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
    #             }

    #     # 返す
    #     return initial

    def get_initial(self):
        initial={}
        est_obj = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).first()
        if est_obj.plan:
            initial={
                'plan': Plan.objects.filter(pk=est_obj.plan.id).first(),
                'service': est_obj.service,
            }
            if est_obj.option1:
                initial['option1'] = Plan.objects.filter(pk=est_obj.option1.id).first()
            if est_obj.option2:
                initial['option2'] = Plan.objects.filter(pk=est_obj.option2.id).first()
            if est_obj.option3:
                initial['option3'] = Plan.objects.filter(pk=est_obj.option3.id).first()
            if est_obj.option4:
                initial['option4'] = Plan.objects.filter(pk=est_obj.option4.id).first()
            if est_obj.option5:
                initial['option5'] = Plan.objects.filter(pk=est_obj.option5.id).first()

        # 返す
        return initial


    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(EstimateStep2, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        kwargs.update({'service_id': self.request.session.get('service', None)})

        return kwargs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.request.session.get('service', None)
        service = Service.objects.get(pk=service_id)
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option1','option2','option3','option4','option5',).first()
        context["service"] = service
        context["estimate"] = estimate
        # サービスに紐づくプランの数
        options_list = []
        options = Plan.objects.filter(service=service, is_option=True, is_trial=False,).distinct().values_list('category')
        for op  in options:
            for number in op:
                options_list.append(number)

        context["options_list"] = options_list

        return context

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        print("selfselfselfselfself",self)
        print("requestrequest",request)
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):

        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        estimate_step2 = Estimates.objects.get(pk = self.request.session['estimate_step1_id'])

        # POSTで送信された値を取得

        # プランの保存
        estimate_step2.plan = form.cleaned_data['plan']
        # オプションの保存
        estimate_step2.option1 = form.cleaned_data['option1']
        estimate_step2.option2 = form.cleaned_data['option2']
        estimate_step2.option3 = form.cleaned_data['option3']
        estimate_step2.option4 = form.cleaned_data['option4']
        estimate_step2.option5 = form.cleaned_data['option5']

        # 保存
        estimate_step2.save()

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 3


        # 小計を算出
        # ↑で登録したプランを取得
        estimate_calc = Estimates.objects.select_related().get(pk=estimate_step2.id)
        print("estimate_calc",estimate_calc)
        # プランの月額を取得
        print("プラン",estimate_calc.plan)
        plan_unit_price = estimate_calc.plan.unit_price
        # プランの年額を取得
        plan_price = estimate_calc.plan.price


        # オプションの小計を算出
        option_unit_price_list = []
        option_price_list = []


        if estimate_calc.option1:
            option_unit_price_list.append(estimate_calc.option1.unit_price)
            option_price_list.append(estimate_calc.option1.price)
        if estimate_calc.option2:
            option_unit_price_list.append(estimate_calc.option2.unit_price)
            option_price_list.append(estimate_calc.option2.price)
        if estimate_calc.option3:
            option_unit_price_list.append(estimate_calc.option3.unit_price)
            option_price_list.append(estimate_calc.option3.price)
        if estimate_calc.option4:
            option_unit_price_list.append(estimate_calc.option4.unit_price)
            option_price_list.append(estimate_calc.option4.price)
        if estimate_calc.option5:
            option_unit_price_list.append(estimate_calc.option5.unit_price)
            option_price_list.append(estimate_calc.option5.price)

        # 割引前小計(税抜)
        unit_total = sum(option_price_list) + plan_price
        estimate_calc.unit_total = unit_total
        # 割引前小計(税抜)の月額
        estimate_calc.unit_minor_total = unit_total / 12

        # 保存
        estimate_calc.save()

        # ステップ3へ遷移
        return HttpResponseRedirect(reverse('contracts:estimate_step3'))

"""
見積作成(ステップ③)
"""
class EstimateStep3(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/estimate/step3.html'
    form_class = EstimateStep3Form
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not 'page_num' in self.request.session:
            return render(request, '406.html', status=406)

        if not self.request.session['page_num'] == 3:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)


    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(EstimateStep3, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


    def get_initial(self):
        initial = {}
        if self.request.session['page_num'] == 3:
            est_obj = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).first()
            print('ぺいめんとめそっど',est_obj.method_payment.id)
            initial={
                'method_payment': est_obj.method_payment.id,
                'is_invoice_need': est_obj.is_invoice_need,
                'bill_address':est_obj.bill_address
            }
            if est_obj.discount:
                print('割引はある')
                initial['discount'] = est_obj.discount.coupon_code

        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.request.session.get('service', None)
        service = Service.objects.get(pk=service_id)
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option1', 'option2', 'option3', 'option4', 'option5',).first()

        context["service"] = service
        context["estimate"] = estimate

        return context


    def form_valid(self, form):

        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        estimate_step4 = Estimates.objects.get(pk = self.request.session['estimate_step1_id'])

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']

        is_invoice_need = form.cleaned_data['is_invoice_need']

        bill_address = form.cleaned_data['bill_address']

        coupon_code = form.cleaned_data['discount']
        # 支払い方法の保存
        estimate_step4.method_payment = method_payment

        # 請求オプションの保存
        estimate_step4.is_invoice_need = is_invoice_need

        #請求書の宛先の保存
        estimate_step4.bill_address = bill_address

        if coupon_code:
            discount = Discount.objects.filter(coupon_code=coupon_code).first()
            estimate_step4.discount = discount

        # 小計(税抜)
        if coupon_code and estimate_step4.unit_total >= 30000: #クーポンあり、割引あり
            minor_total = estimate_step4.unit_total - method_payment.payment_discount - discount.discount_rate
        elif estimate_step4.unit_total >= 30000: #クーポンなし、割引あり
            minor_total = estimate_step4.unit_total - method_payment.payment_discount
        elif coupon_code: # クーポンあり、割引なし
            minor_total = estimate_step4.unit_total - discount.discount_rate
        else:# クーポンなし、割引なし
            minor_total = estimate_step4.unit_total

        estimate_step4.minor_total = minor_total

        # 消費税
        tax = minor_total * settings.TAX
        estimate_step4.tax = tax

        # 合計
        total = minor_total + tax
        estimate_step4.total = total

        # 保存
        estimate_step4.save()

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 4

        # ステップ4へ遷移
        return HttpResponseRedirect(reverse('contracts:estimate_step4'))

"""
見積作成(ステップ④)
"""
class EstimateStep4(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'contracts/estimate/step4.html'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not 'page_num' in self.request.session:
            return render(request, '406.html', status=406)

        if not self.request.session['page_num'] == 4:
            # if not self.request.session['page_num'] == 4:

            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 前の作成画面で作成した見積のIDを取得
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option1', 'option2', 'option3', 'option4', 'option5').first()
        # 見積オブジェクトを取得
        context["estimate"] = estimate

        # 日付情報取得
        # today = datetime.now().strftime('%Y年%m月%d日')
        today = datetime.now()

        context["date"] = today

        return context

"""
見積作成(ステップ⑤)
"""
class EstimateStep5(LoginRequiredMixin, View, CommonView):
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not 'page_num' in self.request.session:
            return render(request, '406.html', status=406)

        if not self.request.session['page_num'] == 4:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        # 前の作成画面で作成した見積のIDを取得
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option1', 'option2', 'option3', 'option4', 'option5').first()

        # 作成日を登録
        estimate.created_date = datetime.now()
        #仮作成フラグをFalseに
        estimate.temp_check = False

        estimate.save()

        # 保存したセッションをクリア(Djangoが生成するキー以外)
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]
        print('作成メッセージ直前')

        messages.success(request, "見積書を作成しました。")
        print('作成メッセージさくせい')
        return redirect('contracts:estimate')

        # return HttpResponseRedirect(reverse('contracts:estimate'))

"""
見積もり削除(Ajax用)
"""
def delete_estimate(request):
    print('見積り削除Ajaxにきた')
    checks = request.POST.getlist('checks[]')
    print('ちぇっくず',checks)
    update_estimate = request.POST.get('update_estimate')
    if checks:
        estimates = Estimates.objects.filter(pk__in = checks)

        is_deleted = estimates.delete()

        data = {
            'is_exist': is_deleted
        }
        if data['is_exist']:
            data['error_message'] = str(len(checks)) + '個の見積書を削除しました'

    if update_estimate:
        estimate = Estimates.objects.filter(pk=update_estimate)

        is_deleted = estimate.delete()

        data = {
            'is_exist': is_deleted
        }
        if data['is_exist']:
            data['error_message'] = '更新用見積書を削除しました'
            # messages.success(request, "更新用見積書を削除しました。")

    # return redirect('contracts:contract')

    return JsonResponse(data)


"""
通知書PDFダウンロード
"""
class NoticeToPDF(LoginRequiredMixin, DetailView, CommonView):
    model = Estimates
    # template_name = 'contracts/estimate/estimate_template.html'
    template_name = 'contracts/estimate/subsidy_template1.html'

    context_object_name = 'estimate'
    login_url = '/login/'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estimate = Estimates.objects.filter(pk = self.kwargs['pk']).first()
        b_numbar = estimate.num 

        get_barcode = barcode.get_barcode_class('code39') 
        write_barcode = get_barcode(b_numbar,writer=ImageWriter()) 
        barcode_img = write_barcode.save('barcode', options={"write_text": False})
        context["barcode"] = barcode_img

        # 日付情報取得
        today = datetime.now().strftime('%Y年%m月%d日')
        context["date"] = today

        return context

    def render_to_response(self, context):
        html = get_template(self.template_name).render(self.get_context_data())
        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        estimate = self.get_context_data()['estimate']
        date = str(estimate.created_date)
        date2 = code_regex.sub('', date)
        estimate_date = date2[:16]


        # b_img = self.request.user.photo
        # encoded_str = base64.b64encode(open(b_img,'rb').read())
        # print(type(encoded_str))
        # data_uri = 'data:image/png;base64,'+encoded_str.decode()

        # body="<img src='{}' height='70px'/>".format(data_uri)
        # with open('subsidy_template1.html', 'w') as out:
        #     """for debug purpose"""
        #     for row in html.split('\n'):
        #         out.write(row+'\n')

        options = {
            'page-size': 'A4',
            'margin-top': '0.2in',
            'margin-right': '0.2in',
            'margin-bottom': '0.2in',
            'margin-left': '0.2in',
            'encoding': "UTF-8",
            'no-outline': None,
            'quiet': '',
            'enable-local-file-access' : ''
        }
        # options2={
        #     'format': 'png',
        #     'crop-h': '200',
        #     'crop-w': '375',
        #     'crop-x': '0',
        #     'crop-y': '0',
        #     'disable-smart-width': '',
        #     'zoom':1.0,
        #     'enable-local-file-access': ''
        # }
        # imgkit.from_file(html,'static/accounts/img/barcode2.png',options=options2 )

        response_pdf = pdfkit.from_string(html, False, options=options)
        response = HttpResponse(response_pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{fn}"'.format(fn=urllib.parse.quote('Estimate' + estimate_date + '.pdf'))
        return response

# from django.templatetags.static import static
# """
# 見積PDFダウンロード
# """
class EstimateToPDF(LoginRequiredMixin, DetailView, CommonView):
    model = Estimates
    template_name = 'contracts/estimate/estimate_template.html'
    # template_name = 'contracts/estimate/ginowan2023/ginowan_furikomi.html'

    context_object_name = 'estimate'
    login_url = '/login/'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estimate = Estimates.objects.filter(pk = self.kwargs['pk']).first()
        b_numbar = estimate.num 

        static = settings.STATIC_URL
        #画像ファイルをバイナリで開く

        #estimate用
        with open("static\contracts\img\CL_stamp.png", "rb") as f:
        # with open("static/accounts/img/barcode2.png", "rb") as f:
            #ファイルの内容を読込み、Base64にエンコードする
            bImgBase64 = base64.b64encode(f.read())

        #バイナリを文字列に変換する
        strImgBase64 = str(bImgBase64)
        #文字列変換時の先頭の「b'」と末尾の「'」を取り除く
        strImgBase64 = strImgBase64[2: len(strImgBase64) - 1]
        #PNG形式のヘッダを付加する
        imgSample = "data:image/png;base64," + strImgBase64

        context["imgSample"] = imgSample

        #市長印用
        # with open("static/accounts/img/mayor_stamp.bmp", "rb") as f:
        #     #ファイルの内容を読込み、Base64にエンコードする
        #     bImgBase64 = base64.b64encode(f.read())

        # #バイナリを文字列に変換する
        # strImgBase64 = str(bImgBase64)
        # #文字列変換時の先頭の「b'」と末尾の「'」を取り除く
        # strImgBase64 = strImgBase64[2: len(strImgBase64) - 1]
        # #PNG形式のヘッダを付加する
        # imgSample2 = "data:image/png;base64," + strImgBase64

        # context["imgSample2"] = imgSample2

        # #口座番号3桁
        # bank_num = 1234567 #口座番号データ
        # bank_str = str(bank_num)
        # bank_3 = bank_str[-3:]

        # context["bank3"] = bank_3

        # 日付情報取得
        today = datetime.now()

        # today = datetime.now().strftime('%Y年%m月%d日')
        context["date"] = today

        return context

    def render_to_response(self, context):
        html = get_template(self.template_name).render(self.get_context_data())
        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        estimate = self.get_context_data()['estimate']
        date = str(estimate.created_date)
        date2 = code_regex.sub('', date)
        estimate_date = date2[:16]

        #estimate＆宜野湾a4用
        options = {
            'page-size': 'Letter',
            'margin-top': '0.25in',
            'margin-right': '0.25in',
            'margin-bottom': '0.25in',
            'margin-left': '0.25in',
            'encoding': "UTF-8",
            'no-outline': None,
            'quiet': '',
            'enable-local-file-access' : None
        }

        #宜野湾用A3
        # options = {
        #     'page-size': 'A3',
        #     'margin-top': '0.1in',
        #     'margin-right': '0.2in',
        #     'margin-bottom': '0.2in',
        #     'margin-left': '0.2in',
        #     'encoding': "UTF-8",
        #     'no-outline': None,
        #     'quiet': '',
        #     'orientation' : 'Landscape',
        #     'enable-local-file-access' : ''
        # }


        response_pdf = pdfkit.from_string(html, False, options=options)
        response = HttpResponse(response_pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{fn}"'.format(fn=urllib.parse.quote('Estimate' + estimate_date + '.pdf'))
        return response

"""
見積HTML
"""
# class NoticeToHTML(LoginRequiredMixin, DetailView, CommonView):

class EstimateToHTML(LoginRequiredMixin, DetailView, CommonView):
    model = Estimates
    template_name = 'contracts/estimate/estimate_template.html'
    context_object_name = 'estimate'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print('みつもりHTML')
        # 日付情報取得
        today = datetime.now().strftime('%Y年%m月%d日')
        context["date"] = today

        return context


"""
見積書複製1
"""
class EstimateCopy1(LoginRequiredMixin, FormView, CommonView):
    template_name = 'contracts/estimate/estimate_copy1.html'
    model = Estimates
    form_class = EstimateCopyForm
    login_url = '/login/'

    def get_initial(self):
        initial={}
        if 'estimate_copy1_id' in self.request.session:
            est_obj = Estimates.objects.filter(pk = self.request.session['estimate_copy1_id']).first()
            initial={
                'start_day': est_obj.start_day,
            }
            if est_obj.discount:
                print('割引はある')
                initial['discount'] = est_obj.discount.coupon_code

        else:
            pass

            # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super(EstimateCopy1, self).get_context_data(**kwargs)
        estimate = Estimates.objects.filter(pk = self.kwargs['pk']).first()
        service = Service.objects.get(pk=estimate.service_id)
        if estimate.unit_total >= 30000:
            total = estimate.unit_total - estimate.method_payment.payment_discount
        else:
            total = estimate.unit_total

        # 見積オブジェクトを取得
        context["estimate"] = estimate
        context["service"] = service
        context["total"] = total

        return context

    def form_valid(self, form, **kwargs):

        # フォームからDBのオブジェクトを仮生成（未保存）
        if not 'estimate_copy1_id' in self.request.session:
            estimate_copy1 = form.save(commit=False)
        else:
            estimate_copy1 = Estimates.objects.filter(pk = self.request.session['estimate_copy1_id']).first()

        # ユーザーを保存
        estimate_copy1.user = self.request.user

        org_estimate = Estimates.objects.filter(pk = self.kwargs['pk']).first()

        # 本日日付
        today = datetime.now()

        # 作成日を登録
        estimate_copy1.created_date = datetime.now()

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1)
        estimate_copy1.expiration_date = expiration_date.date()

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')
        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        date = str(estimate_copy1.created_date)
        date2 = code_regex.sub('', date)
        last_id = date2[8:14]

        if int(last_id) <= 9:
            last_id = str("000") + str(last_id)
        elif int(last_id) <= 99:
            last_id = str("00") + str(last_id)
        elif int(last_id) <= 999:
            last_id = str("0") + str(last_id)
        else:
            last_id = str(last_id)

        estimate_num = day_number + last_id
        estimate_copy1.num = estimate_num


        # 契約終了日の設定
        # 契約開始日から終了日を生成(+1年)
        start_day = form.cleaned_data['start_day']
        end_day =  start_day + relativedelta(years=1,hour=23,minute=59,second=59,microsecond=999999) - relativedelta(days=1)
        estimate_copy1.end_day = end_day

        estimate_copy1.service = org_estimate.service

        estimate_copy1.method_payment = org_estimate.method_payment

        estimate_copy1.is_invoice_need = org_estimate.is_invoice_need

        estimate_copy1.bill_address = org_estimate.bill_address

        estimate_copy1.plan = org_estimate.plan

        # オプションの小計を算出
        if org_estimate.option1:
            estimate_copy1.option1 = org_estimate.option1
        if org_estimate.option2:
            estimate_copy1.option2 = org_estimate.option2
        if org_estimate.option3:
            estimate_copy1.option3 = org_estimate.option3
        if org_estimate.option4:
            estimate_copy1.option4 = org_estimate.option4
        if org_estimate.option5:
            estimate_copy1.option5 = org_estimate.option5

        estimate_copy1.unit_total = org_estimate.unit_total

        estimate_copy1.unit_minor_total = org_estimate.unit_minor_total

        coupon_code = form.cleaned_data['discount']
        if coupon_code:
            discount = Discount.objects.filter(coupon_code=coupon_code).first()
            estimate_copy1.discount = discount


        # 小計(税抜)
        if coupon_code: #クーポンある場合
            if estimate_copy1.unit_total >= 30000: #30000以上の場合は各支払い割引適用
                minor_total = estimate_copy1.unit_total - estimate_copy1.method_payment.payment_discount - discount.discount_rate
            else:
                minor_total = estimate_copy1.unit_total - discount.discount_rate

        else:
            if estimate_copy1.unit_total >= 30000: #30000以上の場合は各支払い割引適用
                minor_total = estimate_copy1.unit_total - estimate_copy1.method_payment.payment_discount
            else:
                minor_total = estimate_copy1.unit_total

        estimate_copy1.minor_total = minor_total

        # 消費税
        tax  = minor_total * settings.TAX
        estimate_copy1.tax = tax

        # 合計
        total = minor_total + tax
        estimate_copy1.total = total


        # 保存
        estimate_copy1.save()


        self.request.session['estimate_id'] = org_estimate.id
        # POST送信された情報をセッションへ保存
        self.request.session['service'] =  estimate_copy1.service.id
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['estimate_copy1_id'] = estimate_copy1.id

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 1

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('contracts:estimate_copy2'))  

"""
見積書複製2
"""
class EstimateCopy2(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'contracts/estimate/estimate_copy2.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 前の作成画面で作成した見積のIDを取得
        estimate_copy2 = Estimates.objects.filter(pk = self.request.session['estimate_copy1_id']).prefetch_related('option1', 'option2', 'option3', 'option4', 'option5').first()
        # 見積オブジェクトを取得
        context["estimate"] = estimate_copy2

        # 日付情報取得
        today = datetime.now()
        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 2

        return context

"""
複製完了
"""
class EstimateCopyDone(LoginRequiredMixin, View, CommonView):
    login_url = '/login/'
    
    def get(self, request, *args, **kwargs):

        # 前の作成画面で作成した見積のIDを取得
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_copy1_id']).prefetch_related('option1', 'option2', 'option3', 'option4', 'option5').first()

        # 作成日を登録
        estimate.created_date = datetime.now()
        #仮作成フラグをFalseに
        estimate.temp_check = False

        estimate.save()

        # 保存したセッションをクリア(Djangoが生成するキー以外)
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        messages.success(request, "見積書を複製しました。")
        return redirect('contracts:estimate')

"""
申込-サービス説明
"""
class OfferDescription(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'contracts/offer/description.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_pk = kwargs['pk']
        contract = Contract.objects.get(pk=contract_pk)
        context["contract"] = contract
        return context

"""
申込-プラン・オプション選択(ステップ①)
"""
class OfferStep1(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/offer/step1.html'
    form_class = OfferStep1Form
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self,**kwargs):
        kwargs = super(OfferStep1, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        kwargs.update({'service_id': self.kwargs['pk']})

        return kwargs


    def get_initial(self,**kwargs):
        initial={}
        if 'offer_step1_id' in self.request.session:

            est_obj = Estimates.objects.filter(pk = self.request.session['offer_step1_id']).first()
            if est_obj.plan:
                initial={
                    'start_day': est_obj.start_day,
                    'service': est_obj.service,
                    'plan': Plan.objects.filter(pk=est_obj.plan.id).first(),
                }
                if est_obj.option1:
                    initial['option1'] = Plan.objects.filter(pk=est_obj.option1.id).first()
                if est_obj.option2:
                    initial['option2'] = Plan.objects.filter(pk=est_obj.option2.id).first()
                if est_obj.option3:
                    initial['option3'] = Plan.objects.filter(pk=est_obj.option3.id).first()
                if est_obj.option4:
                    initial['option4'] = Plan.objects.filter(pk=est_obj.option4.id).first()
                if est_obj.option5:
                    initial['option5'] = Plan.objects.filter(pk=est_obj.option5.id).first()
            # 返す
            return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.kwargs['pk']
        service = Service.objects.get(pk=service_id)

        context["service"] = service

        today = datetime.now()
        contract = Contract.objects.filter(service=service,status="1").first()
        if contract:
            context["contract"] = contract

        # サービスに紐づくプランの数
        options_list = []
        options = Plan.objects.filter(service=service, is_option=True, is_trial=False,).distinct().values_list('category')
        for op  in options:
            for number in op:
                options_list.append(number)

        context["options_list"] = options_list

        return context

    def post(self, request, *args, **kwargs):

        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    #キャンセルした際はフォームばりっどを消す
    def form_valid(self, form):
        if not 'offer_step1_id' in self.request.session:
            # フォームからDBのオブジェクトを仮生成（未保存）
            offer_step1 = form.save(commit=False)
        else:
            offer_step1 = Estimates.objects.filter(pk = self.request.session['offer_step1_id']).first()
            if not offer_step1.plan == form.cleaned_data['plan']:
                offer_step1.plan = form.cleaned_data['plan']
            if not offer_step1.option1 == form.cleaned_data['option1']:
                offer_step1.option1 = form.cleaned_data['option1']
            if not offer_step1.option2 == form.cleaned_data['option2']:
                offer_step1.option2 = form.cleaned_data['option2']
            if not offer_step1.option3 == form.cleaned_data['option3']:
                offer_step1.option3 = form.cleaned_data['option3']
            if not offer_step1.option4 == form.cleaned_data['option4']:
                offer_step1.option4 = form.cleaned_data['option4']
            if not offer_step1.option5 == form.cleaned_data['option5']:
                offer_step1.option5 = form.cleaned_data['option5']


        # ユーザーを保存
        offer_step1.user = self.request.user

        # サービスを保存
        service_id = self.kwargs['pk']
        offer_step1.service = Service.objects.get(pk=service_id)
        # 本日日付
        today = datetime.now()

        # 作成日を登録
        offer_step1.created_date = today

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1,days=-1,hour=23,minute=59,second=59,microsecond=999999)
        offer_step1.expiration_date = expiration_date

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')

        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        date = str(offer_step1.created_date)
        date2 = code_regex.sub('', date)
        last_id = date2[8:14]

        if int(last_id) <= 9:
            last_id = str("000") + str(last_id)
        elif int(last_id) <= 99:
            last_id = str("00") + str(last_id)
        elif int(last_id) <= 999:
            last_id = str("0") + str(last_id)
        else:
            last_id = str(last_id)

        estimate_num = day_number + last_id
        offer_step1.num = estimate_num

        # 契約終了日の設定
        # 契約開始日から終了日を生成(+1年)
        start_day = form.cleaned_data['start_day']
        end_day =  start_day + relativedelta(years=1,days=-1,hour=23,minute=59,second=59,microsecond=999999)
        offer_step1.end_day = end_day


        # 保存
        offer_step1.save()

        # ↑で登録したフォームを取得
        estimate_calc = Estimates.objects.select_related().get(pk=offer_step1.id)
        # プランの年額を取得
        plan_price = estimate_calc.plan.price

        # オプションの小計を算出
        option_price_list = []
        if estimate_calc.option1:
            option_price_list.append(estimate_calc.option1.price)
        if estimate_calc.option2:
            option_price_list.append(estimate_calc.option2.price)
        if estimate_calc.option3:
            option_price_list.append(estimate_calc.option3.price)
        if estimate_calc.option4:
            option_price_list.append(estimate_calc.option4.price)
        if estimate_calc.option5:
            option_price_list.append(estimate_calc.option5.price)

        #プラン＆オプション合計
        unit_total = sum(option_price_list) + plan_price
        estimate_calc.unit_total = unit_total

        #プラン＆オプション月額
        estimate_calc.unit_minor_total = unit_total / 12

        # 保存
        estimate_calc.save()

        # # POST送信された情報をセッションへ保存
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['offer_step1_id'] = offer_step1.id
        self.request.session['offer_step1_service_name'] = offer_step1.service.name
        self.request.session['offer_step1_start_day'] = str(offer_step1.start_day)

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 2

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('contracts:offer_step2'))

"""
申込-支払い方法の選択(ステップ②)
"""
class OfferStep2(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/offer/step2.html'
    form_class = OfferStep2Form
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not 'page_num' in self.request.session:
            return render(request, '406.html', status=406)

        if not self.request.session['page_num'] == 2:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(OfferStep2, self).get_form_kwargs()
        estimate = Estimates.objects.filter(pk = self.request.session['offer_step1_id']).prefetch_related('option1','option2','option3','option4','option5').first()
        service =  Service.objects.get(name=self.request.session['offer_step1_service_name'])
        start_day =  self.request.session['offer_step1_start_day']

        # 小計をFormに送る
        kwargs.update({'total_price': estimate.minor_total})
        kwargs.update({'user': self.request.user})

        return kwargs


    def get_initial(self):
        initial = {}
        if self.request.session['page_num'] == 2:
            estimates = Estimates.objects.filter(pk = self.request.session['offer_step1_id']).prefetch_related('method_payment',).first()

            initial={'method_payment': estimates.method_payment.id,
                    'is_invoice_need': estimates.is_invoice_need,
                    'bill_address':estimates.bill_address
            }
            if estimates.discount:
                    initial['discount'] = estimates.discount.coupon_code
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print('ステップ２コンテキストの中身',context)
        estimate = Estimates.objects.filter(pk = self.request.session['offer_step1_id']).prefetch_related('option1','option2','option3','option4','option5').first()
        service =  Service.objects.get(pk=estimate.service.id)
        plan =  Plan.objects.get(pk=estimate.plan_id)


        context["service"] = service
        context["estimate"] = estimate
        context["plan"] = plan

        return context


    def form_valid(self, form):

        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        offer_step2 = Estimates.objects.get(pk = self.request.session['offer_step1_id'])

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']
        is_invoice_need = form.cleaned_data['is_invoice_need']
        bill_address = form.cleaned_data['bill_address']
        coupon_code = form.cleaned_data['discount']

        # 支払い方法の保存
        offer_step2.method_payment = method_payment

        # 請求オプションの保存
        offer_step2.is_invoice_need = is_invoice_need

        #請求書の宛先の保存
        offer_step2.bill_address = bill_address

        if coupon_code:
            discount = Discount.objects.filter(coupon_code=coupon_code).first()
            offer_step2.discount = discount

        # 小計(税抜)
        if coupon_code and offer_step2.unit_total >= 30000: #クーポンあり、割引あり
            minor_total = offer_step2.unit_total - method_payment.payment_discount - discount.discount_rate
        elif offer_step2.unit_total >= 30000: #クーポンなし、割引あり
            minor_total = offer_step2.unit_total - method_payment.payment_discount
        elif coupon_code: # クーポンあり、割引なし
            minor_total = offer_step2.unit_total - discount.discount_rate
        else:# クーポンなし、割引なし
            minor_total = offer_step2.unit_total

        offer_step2.minor_total = minor_total
        # 消費税
        tax  = offer_step2.minor_total * settings.TAX
        offer_step2.tax = tax

        # 合計
        total = offer_step2.minor_total + tax
        offer_step2.total = total

        # 保存
        offer_step2.temp_check = False 
        offer_step2.save()

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 3

        # 支払いへ遷移
        if method_payment.id == 1:
            return HttpResponseRedirect(reverse('payment:checkout_from_offer', kwargs={'pk': offer_step2.id}))
        else:
            return HttpResponseRedirect(reverse('payment:checkout_bank_from_offer', kwargs={'pk': offer_step2.id}))


"""
キャンセル処理
"""
# class UpdateCancelView(LoginRequiredMixin, View):
#     login_url = '/login/'

#     def get(self, request, *args, **kwargs):

#         # セッションに「contract_update_step1」があれば、取得した行を削除
#         if 'contract_update_step1' in request.session:
#             estimate = Estimates.objects.get(pk = request.session['contract_update_step1'])
#             estimate.delete()

#         # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
#         for key in list(self.request.session.keys()):
#             if not key.startswith("_"):
#                 del self.request.session[key]

#         return HttpResponseRedirect(reverse('contracts:contract'))

"""
更新用見積り作成-変更なし
"""
class UpdateContractNoChangeStep1(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/update_contract/no_change_step1.html'
    form_class = UpdateContractNochangeStep1Form
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UpdateContractNoChangeStep1, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        # kwargs.update({'contract_id': self.kwargs['pk']})

        return kwargs

    def get_initial(self):
        contract = Contract.objects.filter(pk = self.kwargs['pk']).first()
        initial={}

        if 'contract_update_step1' in self.request.session:
            est_obj = Estimates.objects.filter(pk = self.request.session['contract_update_step1']).first()
    
            initial={'method_payment': est_obj.method_payment,
                    'is_invoice_need': est_obj.is_invoice_need,
                    }
        else:
            initial={'method_payment': contract.payment.method_payment,
                    'is_invoice_need': contract.is_invoice_need,
                    }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.filter(pk = self.kwargs['pk']).first()
        estimate = contract.estimate.all().first()
        new_start_date = contract.contract_start_date + relativedelta(years=1)
        context["contract"] = contract
        context["estimate"] = estimate
        context["new_start_date"] = new_start_date

        return context

    def form_valid(self, form):

        # 契約のオブジェクトを生成
        contract = Contract.objects.get(pk = self.kwargs['pk'])

        old_estimate = contract.estimate.all().first()

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']
        is_invoice_need = form.cleaned_data['is_invoice_need']

        # 支払い方法の保存
        if not 'contract_update_step1' in self.request.session:

            estimate = Estimates.objects.create(user=old_estimate.user, service=old_estimate.service)
        else:
            estimate = Estimates.objects.filter(pk = self.request.session['contract_update_step1']).first()
        estimate.method_payment = method_payment
        #請求書宛名の保存
        estimate.bill_address = old_estimate.bill_address
        # 請求オプションの保存
        estimate.is_invoice_need = is_invoice_need
        # プランの保存
        estimate.plan = old_estimate.plan

        # オプションの保存
        option_price_list = []
        if old_estimate.option1:
            estimate.option1 = old_estimate.option1
            option_price_list.append(estimate.option1.price)
        if old_estimate.option2:
            estimate.option2 = old_estimate.option2
            option_price_list.append(estimate.option2.price)
        if old_estimate.option3:
            estimate.option3 = old_estimate.option3
            option_price_list.append(estimate.option3.price)
        if old_estimate.option4:
            estimate.option4 = old_estimate.option4
            option_price_list.append(estimate.option4.price)
        if old_estimate.option5:
            estimate.option5 = old_estimate.option5
            option_price_list.append(estimate.option5.price)


        today = datetime.now()

        # 作成日を登録
        estimate.created_date = today

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1,days=-1,hour=23,minute=59,second=59,microsecond=999999)
        estimate.expiration_date = expiration_date.date()

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')
        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        date = str(estimate.created_date)
        date2 = code_regex.sub('', date)
        last_id = date2[8:14]

        if int(last_id) <= 9:
            last_id = str("000") + str(last_id)
        elif int(last_id) <= 99:
            last_id = str("00") + str(last_id)
        elif int(last_id) <= 999:
            last_id = str("0") + str(last_id)
        else:
            last_id = str(last_id)

        estimate_num = day_number + last_id
        estimate.num = estimate_num

        # 契約終了日の設定
        # 契約開始日(旧契約期限の翌日)から終了日を生成(+1年)
        start_day = contract.contract_start_date + relativedelta(years=1,hour=0,minute=0,second=0,microsecond=0)

        estimate.start_day = start_day

        end_day =  contract.contract_end_date + relativedelta(years=1)
        estimate.end_day = end_day

        # coupon_code = form.cleaned_data['discount']
        # if coupon_code:
        #     discount = Discount.objects.filter(coupon_code=coupon_code).first()
        #     estimate.discount = discount

        #プランとオプションの合計
        unit_total = sum(option_price_list) + estimate.plan.price
        estimate.unit_total = unit_total

        #プランとオプションの月額
        estimate.unit_minor_total = unit_total / 12

        # 小計(税抜)
        if estimate.unit_total >= 30000: #割引あり
            minor_total = estimate.unit_total - method_payment.payment_discount
        else:# 割引なし
            minor_total = estimate.unit_total
        # if coupon_code and estimate.unit_total >= 30000: #クーポンあり、割引あり
        #     minor_total = estimate.unit_total - method_payment.payment_discount - discount.discount_rate
        # elif estimate.unit_total >= 30000: #クーポンなし、割引あり
        #     minor_total = estimate.unit_total - method_payment.payment_discount
        # elif coupon_code: # クーポンあり、割引なし
        #     minor_total = estimate.unit_total - discount.discount_rate
        # else:# クーポンなし、割引なし
        #     minor_total = estimate.unit_total

        estimate.minor_total = minor_total

        # 消費税
        tax  = minor_total * settings.TAX
        estimate.tax = tax

        # 合計
        total = minor_total + tax
        estimate.total = total


        # 保存
        estimate.save()
        # POST送信された情報をセッションへ保存
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract_update_step1'] = estimate.id
        self.request.session['contract_id'] = contract.id

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 2
        
        return HttpResponseRedirect(reverse('contracts:cont_update_step2'))

        #支払いへ遷移
        # if method_payment.id == 1:
        #     return HttpResponseRedirect(reverse('payment:update_contract_card', kwargs={'pk': estimate.id}))
        # else:
        #     return HttpResponseRedirect(reverse('payment:update_contract_bank', kwargs={'pk': estimate.id}))


"""
更新用見積り作成-変更あり1_1
"""
class UpdateContractChangeStep1(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/update_contract/change_step1_1.html'
    form_class = UpdateContractChangeStep1Form
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UpdateContractChangeStep1, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        contract = Contract.objects.filter(pk=self.kwargs['pk']).first()
        kwargs.update({'service_id': contract.service.id})

        return kwargs


    def get_initial(self):
        initial={}
        if 'contract_update_change1' in self.request.session:
            est_obj = Estimates.objects.filter(pk = self.request.session['contract_update_change1']).first()
            initial={
                'service': est_obj.service,
                'plan': Plan.objects.filter(pk=est_obj.plan.id).first(),
            }
            if est_obj.option1:
                initial['option1'] = Plan.objects.filter(pk=est_obj.option1.id).first()
            if est_obj.option2:
                initial['option2'] = Plan.objects.filter(pk=est_obj.option2.id).first()
            if est_obj.option3:
                initial['option3'] = Plan.objects.filter(pk=est_obj.option3.id).first()
            if est_obj.option4:
                initial['option4'] = Plan.objects.filter(pk=est_obj.option4.id).first()
            if est_obj.option5:
                initial['option5'] = Plan.objects.filter(pk=est_obj.option5.id).first()
        else:
            # estimates = Estimates.objects.filter(pk = self.kwargs['pk']).prefetch_related('option',).first()
            contract = Contract.objects.filter(pk=self.kwargs['pk']).first()
            initial={
                'service': contract.service,
                'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
            }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_id = self.kwargs['pk']
        contract = Contract.objects.get(pk=contract_id)
        service = Service.objects.get(pk=contract.service.id)

        # サービスに紐づくプランの数
        options_list = []
        options = Plan.objects.filter(service=service, is_option=True, is_trial=False,).distinct().values_list('category')
        for op  in options:
            for number in op:
                options_list.append(number)

        context["service"] = service
        context["contract"] = contract
        context["options_list"] = options_list

        return context

    def form_valid(self, form):
        # 前の契約
        contract = Contract.objects.get(pk=self.kwargs['pk'])

        old_estimate = contract.estimate.all().first()
        if not 'contract_update_change1' in self.request.session:
            # フォームからDBのオブジェクトを仮生成（未保存）
            estimate_step1 = form.save(commit=False)
        else:
            estimate_step1 = Estimates.objects.filter(pk = self.request.session['contract_update_change1']).first()
            option1 = form.cleaned_data['option1']
            option2 = form.cleaned_data['option2']
            option3 = form.cleaned_data['option3']
            option4 = form.cleaned_data['option4']
            option5 = form.cleaned_data['option5']
            if option1 or option2 or option3 or option4 or option5:
                if option1:
                    if not option1 == estimate_step1.option1:
                        estimate_step1.option1 = option1
                if option2:
                    if not option2 == estimate_step1.option2:
                        estimate_step1.option2 = option2
                if option3:
                    if not option3 == estimate_step1.option3:
                        estimate_step1.option3 = option3
                if option4:
                    if not option4 == estimate_step1.option4:
                        estimate_step1.option4 = option4
                if option5:
                    if not option5 == estimate_step1.option5:
                        estimate_step1.option5 = option5


        # ユーザーを保存
        estimate_step1.user = self.request.user

        # サービスを保存
        estimate_step1.service = old_estimate.service
        # 本日日付
        today = datetime.now()

        # 作成日を登録
        estimate_step1.created_date = today

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1,days=-1,hour=23,minute=59,second=59,microsecond=999999)
        estimate_step1.expiration_date = expiration_date

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')

        # 通し番号を生成(見積もりIDを後ろに付与)
        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        date = str(estimate_step1.created_date)
        date2 = code_regex.sub('', date)
        last_id = date2[8:14]

        if int(last_id) <= 9:
            last_id = str("000") + str(last_id)
        elif int(last_id) <= 99:
            last_id = str("00") + str(last_id)
        elif int(last_id) <= 999:
            last_id = str("0") + str(last_id)
        else:
            last_id = str(last_id)

        estimate_num = day_number + last_id
        estimate_step1.num = estimate_num

        # 契約終了日の設定
        # 契約開始日から終了日を生成(+1年)
        start_day = contract.contract_start_date + relativedelta(years=1,hour=0,minute=0,second=0,microsecond=0)
        estimate_step1.start_day = start_day

        end_day =  contract.contract_end_date + relativedelta(years=1)
        estimate_step1.end_day = end_day

        #請求書の宛先の保存
        estimate_step1.bill_address = old_estimate.bill_address

        # 保存
        estimate_step1.save()

        # ↑で登録したプランを取得
        estimate_calc = Estimates.objects.select_related().get(pk=estimate_step1.id)
        print('契約書の計算用==================================',estimate_calc)
        # プランの年額を取得
        plan_price = estimate_calc.plan.price

        # オプションの小計を算出
        option_price_list = []
        if estimate_calc.option1:
            option_price_list.append(estimate_calc.option1.price)
        if estimate_calc.option2:
            option_price_list.append(estimate_calc.option2.price)
        if estimate_calc.option3:
            option_price_list.append(estimate_calc.option3.price)
        if estimate_calc.option4:
            option_price_list.append(estimate_calc.option4.price)
        if estimate_calc.option5:
            option_price_list.append(estimate_calc.option5.price)
        #プラン＆オプション合計
        unit_total = sum(option_price_list) + plan_price
        estimate_calc.unit_total = unit_total

        #プラン＆オプション月額
        estimate_calc.unit_minor_total = unit_total / 12

        # 保存
        estimate_calc.save()

        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract_update_change1'] = estimate_step1.id
        self.request.session['contract_id'] = contract.id

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 2

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('contracts:cont_update_change_step1_2'))


"""
更新用見積り作成-変更あり1_2
"""
class UpdateContractChangeStep2(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/update_contract/change_step1_2.html'
    form_class = UpdateContractChangeStep2Form
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UpdateContractChangeStep2, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        estimate = Estimates.objects.filter(pk = self.request.session['contract_update_change1']).first()

        return kwargs


    def get_initial(self):
        initial = {}
        if self.request.session['page_num'] == 2:
            estimates = Estimates.objects.filter(pk = self.request.session['contract_update_change1']).prefetch_related('method_payment',).first()

            initial={'method_payment': estimates.method_payment,
                    'is_invoice_need': estimates.is_invoice_need,
                    }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estimate = Estimates.objects.filter(pk = self.request.session['contract_update_change1']).prefetch_related('option1','option2','option3','option4','option5').first()
        service =  Service.objects.get(pk=estimate.service.id)
        plan =  Plan.objects.get(pk=estimate.plan_id)

        context["service"] = service
        context["estimate"] = estimate
        context["plan"] = plan

        return context

    def form_valid(self, form):
        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        estimate_step2 = Estimates.objects.get(pk = self.request.session['contract_update_change1'])

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']
        is_invoice_need = form.cleaned_data['is_invoice_need']
        # coupon_code = form.cleaned_data['discount']


        # 支払い方法の保存
        estimate_step2.method_payment = method_payment

        # 請求オプションの保存
        estimate_step2.is_invoice_need = is_invoice_need

        # if coupon_code:
        #     discount = Discount.objects.filter(coupon_code=coupon_code).first()
        #     estimate_step2.discount = discount

        # 小計(税抜)
        if estimate_step2.unit_total >= 30000: #割引あり
            minor_total = estimate_step2.unit_total - method_payment.payment_discount
        else:# 割引なし
            minor_total = estimate_step2.unit_total
        # if coupon_code and estimate_step2.unit_total >= 30000: #クーポンあり、割引あり
        #     minor_total = estimate_step2.unit_total - method_payment.payment_discount - discount.discount_rate
        # elif estimate_step2.unit_total >= 30000: #クーポンなし、割引あり
        #     minor_total = estimate_step2.unit_total - method_payment.payment_discount
        # elif coupon_code: # クーポンあり、割引なし
        #     minor_total = estimate_step2.unit_total - discount.discount_rate
        # else:# クーポンなし、割引なし
        #     minor_total = estimate_step2.unit_total

        estimate_step2.minor_total = minor_total

        # 消費税
        tax  = minor_total * settings.TAX
        estimate_step2.tax = tax

        # 合計
        total = minor_total + tax
        estimate_step2.total = total


        # 保存
        estimate_step2.save()

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 3

        return HttpResponseRedirect(reverse('contracts:cont_update_step2'))


        # 支払いへ遷移
        # if method_payment.id == 1:
        #     return HttpResponseRedirect(reverse('payment:update_contract_card', kwargs={'pk': estimate_step2.id}))
        # else:
        #     return HttpResponseRedirect(reverse('payment:update_contract_bank', kwargs={'pk': estimate_step2.id}))

"""
更新用見積り作成2
"""
class UpdateContractStep2(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'contracts/update_contract/step2.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 前の作成画面で作成した見積のIDを取得 
        if 'contract_update_change1' in self.request.session:
            estimate = Estimates.objects.filter(pk = self.request.session['contract_update_change1']).prefetch_related('option1', 'option2', 'option3', 'option4', 'option5').first()
        else:
            estimate = Estimates.objects.filter(pk = self.request.session['contract_update_step1']).prefetch_related('option1', 'option2', 'option3', 'option4', 'option5').first()
        # 見積オブジェクトを取得
        context["estimate"] = estimate

        # 日付情報取得
        today = datetime.now()

        return context

"""
更新用見積り作成完了
"""
class UpdateEstimateDone(LoginRequiredMixin, View, CommonView):
    login_url = '/login/'
    
    def get(self, request, *args, **kwargs):

        # 前の作成画面で作成した見積のIDを取得
        if 'contract_update_change1' in self.request.session:
            estimate = Estimates.objects.filter(pk = self.request.session['contract_update_change1']).first()
        if 'contract_update_step1' in self.request.session:
            estimate = Estimates.objects.filter(pk = self.request.session['contract_update_step1']).first()
        #更新用フラグをTrueに
        estimate.is_update = True
        #仮作成フラグをFalseに
        estimate.temp_check = False

        estimate.save()

        # 保存したセッションをクリア(Djangoが生成するキー以外)
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        messages.success(request, "更新用見積書を作成しました。")
        return redirect('contracts:contract')


"""
見積書存在確認
"""
class EstimateAjaxView(View):
    def post(self, request):
        user = self.request.user
        s_id = request.POST.get('service')
        estimate = Estimates.objects.filter(service_id = s_id,temp_check=False,user__company=user.company,is_use=False)
        estimate_num = Estimates.objects.filter(service_id = s_id).values("num")
        estimate_j = serializers.serialize("json", estimate)

        #存在確認
        if estimate.count() > 0:
            data = {
                'judge':'exist',
                'estimate':estimate_j
            }
        else:
            data = {
                'judge':'nonexist'
            }

        return JsonResponse(data,safe=True)

"""
既存の見積り選択画面
"""
class SelectEstimate(LoginRequiredMixin, ListView, CommonView):
    model = Estimates
    template_name = 'contracts/offer/select_estimate.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user_id = self.request.user
        service_id = self.kwargs['pk']
        service = Service.objects.filter(pk=service_id)

        # 見積テーブルの表示
        context["estimates"] = Estimates.objects.filter(user=current_user_id,service_id=service_id,temp_check=False,is_change=0,is_use=False)
        # print('==========================見積りしょはｋｋん',context["estimates"])
        context["service"] = service
        return context 