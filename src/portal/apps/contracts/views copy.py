from django.conf import settings
from django.shortcuts import render

from django.http import HttpResponse
from django.views.generic import View, ListView, DetailView, TemplateView, FormView, CreateView, UpdateView, DeleteView

from contracts.forms import EstimateStep1Form,EstimateStep2Form,EstimateStep3Form,OfferStep1Form,OfferStep2Form,UpdateContractNochangeStep1Form,UpdateContractChangeStep1Form,UpdateContractChangeStep2Form,EstimateOptionMultiForm

from accounts.models import User, Company, Service, Messages
from contracts.models import Contract, Plan, PaymentMethod, Estimates, Option
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
import locale
locale.setlocale(locale.LC_CTYPE, "Japanese_Japan.932")
# 有効期限の保存
from datetime import datetime
from dateutil.relativedelta import relativedelta
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

        email_list = current_user.email.rsplit('@', 1)
        # メールアドレスをユーザ名とドメインに分割
        email_domain = email_list[1]

        url_name = self.request.resolver_match.url_name
        app_name = self.request.resolver_match.app_name

        context["url_name"] = url_name
        context["app_name"] = app_name

        context["current_user"] = current_user
        context["email_domain"] = email_domain

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
        contract, created = Contract.objects.get_or_create(user=user, service=service, status="1", contract_start_date=start_date, contract_end_date=end_date)
        contract.plan = plan
        if option:
            contract.option = option
        contract.save()
        # contract.option.set(option)

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
        context = super().get_context_data(**kwargs)
        current_user_id = self.request.user.pk
        context["contracts"] = Contract.objects.filter(user=current_user_id).prefetch_related('estimate', 'payment')


        # contracts = Contract.objects.extra(
        #     tables=["contracts_plan",],
        #     where=['''contracts_contract.plan=contracts_plan.id''']
        # )

        # print("内部結合", contracts)
        Contract.objects.extra(tables=['plan'],where=['contracts.plan_id=plan.id']).query

        context["contracts"] = Contract.objects.filter(user=self.request.user.pk)
        # context["contracts"] = contracts


        # 見積テーブルの表示
        # context["contracts"] = Contract.objects.filter(user=current_user_id)
        # TODO: 契約に紐づく形で更新用見積もり書を作成する
        context["estimates"] = Estimates.objects.filter(user=current_user_id)
        context["estimates_is_update"] = Estimates.objects.filter(user=current_user_id, is_update="True")
        return context

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                                        見積機能
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"""
見積一覧画面
この画面から契約と見積の一覧が見える。
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
キャンセル処理
"""
class EstimateCancelView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        # セッションに「estimate_step1_id」があれば、取得した行を削除
        if 'estimate_step1_id' in request.session:
            estimate = Estimates.objects.get(pk = request.session['estimate_step1_id'])
            estimate.delete()

        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return HttpResponseRedirect(reverse('contracts:estimate'))
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
        # kwargs.update({'service_id': self.kwargs['pk']})

        return kwargs


    def get_initial(self):
        initial={'service': Service.objects.filter(pk=self.request.session.get('service', None)).first(),
                # 'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
                # 'option': estimates.option.all(),
                }

        # 返す
        return initial


    def form_valid(self, form):

        # フォームからDBのオブジェクトを仮生成（未保存）
        estimate_step1 = form.save(commit=False)

        # ユーザーを保存
        estimate_step1.user = self.request.user

        # # サービスを保存
        # service_id = self.kwargs['pk']
        # estimate_step1.service = Service.objects.get(pk=service_id)

        # 本日日付
        today = datetime.now()

        # 作成日を登録
        estimate_step1.created_date = datetime.now()

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1)
        estimate_step1.expiration_date = expiration_date.date()

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')
        
        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        date = str(estimate_step1.created_date)
        date2 = code_regex.sub('', date)
        last_id = date2[8:14]

        # 通し番号を生成(見積もりIDを後ろに付与)
        # last_num = Estimates.objects.all().last()
        # if last_num:
        #     last_id = last_num.pk
        # else:
        #     last_id = 1

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
        start_day = form.cleaned_data['start_day']
        end_day =  start_day + relativedelta(years=1) - relativedelta(days=1)
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
        self.request.session['page_num'] = 1

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('contracts:estimate_step2'))  

"""
見積作成(ステップ②)
"""
class EstimateStep2(LoginRequiredMixin, FormView, CommonView):
    #model = Estimates
    template_name = 'contracts/estimate/step2.html'
    #form_class = EstimateStep2Form
    form_class = EstimateOptionMultiForm
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not 'page_num' in self.request.session:
            return render(request, '406.html', status=406)

        if not self.request.session['page_num'] == 1:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        estimates = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        initial={'method_payment': estimates.method_payment,
                'is_invoice_need': estimates.is_invoice_need,
                }

        # 返す
        return initial

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        # kwargs = super(EstimateOptionMultiForm, self).get_form_kwargs()
        
        kwargs = super(EstimateStep2, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        kwargs.update({'service_id': self.request.session.get('service', None)})
        
        return kwargs


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.request.session.get('service', None)
        service = Service.objects.get(pk=service_id)
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        context["service"] = service
        context["estimate"] = estimate


        return context

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        print("selfselfselfselfself",self)
        print("requestrequest",request)
        form = self.get_form()
        print("formformformformformform",form)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):

        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        estimate_step2 = Estimates.objects.get(pk = self.request.session['estimate_step1_id'])

        # POSTで送信された値を取得
        print('aaaaaaaaaaaaaaaaaaaaa＿＿＿＿＿',form.cleaned_data)
        plan_obj = form.cleaned_data['estimate']['plan']
        print('plan_qs------------------------',plan_obj)
        print('plan_qs------------------------',type(plan_obj))

        option_qs = form.cleaned_data['option']['plan']
        option_num = form.cleaned_data['option']['option_quant']
        print('オプション＿＿＿＿＿',option_qs)
        print('オプション数量＿＿＿＿＿',option_num)

        # for plan in plan_qs:
        if option_qs:
            option_obj, created  = Option.objects.get_or_create(option_quant=option_num)
            option_obj.save()
            option_obj.plan.set(option_qs)
            # オプションの保存
            estimate_step2.option.add(option_obj)
            # オプション数量の保存
            # estimate_step2.option_quant = option_num

        # プランの保存
        estimate_step2.plan = plan_obj
        # POSTで送信された値を取得
        # option_qs = form.cleaned_data['option']
        # print('オプション＿＿＿＿＿',option_qs)
        # POSTで送信された値を取得

        # 保存
        estimate_step2.save()

        # POST送信された情報をセッションへ保存
        # self.request.session['plan'] = plan.id

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 2


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
        print("ああああああああああああああああああああ", estimate_calc.option.all())
        for option in estimate_calc.option.all():
            for option in option.plan.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

        # 小計(税抜)
        minor_total = sum(option_price_list) + plan_price
        estimate_calc.minor_total = minor_total

        unit_minor_total = minor_total / 12

        # 消費税
        tax  = minor_total * settings.TAX
        estimate_calc.tax = tax

        # 合計
        total = minor_total + tax
        estimate_calc.total = total

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

        if not self.request.session['page_num'] == 2:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)


    def get_initial(self):
        estimates = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('method_payment',).first()

        initial={'method_payment': estimates.method_payment,
                'is_invoice_need': estimates.is_invoice_need,
                }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.request.session.get('service', None)
        service = Service.objects.get(pk=service_id)
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        
        context["service"] = service
        context["estimate"] = estimate

        return context


    def form_valid(self, form):

        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        estimate_step4 = Estimates.objects.get(pk = self.request.session['estimate_step1_id'])

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']

        is_invoice_need = form.cleaned_data['is_invoice_need']

        # 支払い方法の保存
        estimate_step4.method_payment = method_payment

        # 請求オプションの保存
        estimate_step4.is_invoice_need = is_invoice_need

        # クレジット決済の場合は割引する
        if method_payment.id == 1:

            # プランの月額を取得
            plan_unit_price = estimate_step4.plan.unit_price
            # プランの年額を取得
            plan_price = estimate_step4.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in estimate_step4.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price - 3000
            estimate_step4.minor_total = minor_total

            # 消費税
            tax  = minor_total * settings.TAX
            estimate_step4.tax = tax

            # 合計
            total = minor_total + tax
            estimate_step4.total = total

        else:
            # プランの月額を取得
            plan_unit_price = estimate_step4.plan.unit_price
            # プランの年額を取得
            plan_price = estimate_step4.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in estimate_step4.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price
            estimate_step4.minor_total = minor_total

            # 消費税
            tax  = minor_total * settings.TAX
            estimate_step4.tax = tax

            # 合計
            total = minor_total + tax
            estimate_step4.total = total


        # 保存
        estimate_step4.save()

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 3

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

        if not self.request.session['page_num'] == 3:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 前の作成画面で作成した見積のIDを取得
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        # 見積オブジェクトを取得
        context["estimate"] = estimate

        # 日付情報取得
        today = datetime.now().strftime('%Y年%m月%d日')
        context["date"] = today

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 4

        return context

"""
見積作成(ステップ⑤)
"""
class EstimateStep5(LoginRequiredMixin, View):
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
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()

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
    checks = request.POST.getlist('checks[]')

    estimates = Estimates.objects.filter(pk__in = checks)

    is_deleted = estimates.delete()

    data = {
        'is_exist': is_deleted
    }
    if data['is_exist']:
        data['error_message'] = str(len(checks)) + '個の削除が成功しました'

    return JsonResponse(data)

# """
# 見積PDFダウンロードオリジナル
# """
# class EstimateToPDF(LoginRequiredMixin, DetailView, CommonView):
#     model = Estimates
#     template_name = 'contracts/estimate/estimate_template.html'
#     context_object_name = 'estimate'
#     login_url = '/login/'


#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         # 日付情報取得
#         today = datetime.now().strftime('%Y年%m月%d日')
#         context["date"] = today

#         return context

#     def render_to_response(self, context):
#         html = get_template(self.template_name).render(self.get_context_data())
#         estimate = self.get_context_data()['estimate']
#         print('ここがpdf')

#         options = {
#             'page-size': 'Letter',
#             'margin-top': '0.25in',
#             'margin-right': '0.25in',
#             'margin-bottom': '0.25in',
#             'margin-left': '0.25in',
#             'encoding': "UTF-8",
#             'no-outline': None,
#             'quiet': ''
#         }
#         print('みつもりPDF')
#         response_pdf = pdfkit.from_string(html, False, options=options)
#         response = HttpResponse(response_pdf, content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="{fn}"'.format(fn=urllib.parse.quote('Estimate' + estimate.num + '.pdf'))
#         return response

"""
見積PDFダウンロード
"""
class EstimateToPDF(LoginRequiredMixin, DetailView, CommonView):
    model = Estimates
    template_name = 'contracts/estimate/estimate_template.html'
    context_object_name = 'estimate'
    login_url = '/login/'



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
        options = {
            'page-size': 'Letter',
            'margin-top': '0.25in',
            'margin-right': '0.25in',
            'margin-bottom': '0.25in',
            'margin-left': '0.25in',
            'encoding': "UTF-8",
            'no-outline': None,
            'quiet': '',
            # 'enable-local-file-access' : 'true'
            'enable-local-file-access' : None
        }
        response_pdf = pdfkit.from_string(html, False, options=options)
        response = HttpResponse(response_pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="{fn}"'.format(fn=urllib.parse.quote('Estimate' + estimate_date + '.pdf'))
        return response

"""
見積HTML
"""
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
    def get_form_kwargs(self):
        kwargs = super(OfferStep1, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        kwargs.update({'service_id': self.kwargs['pk']})

        return kwargs


    def get_initial(self):
        # estimates = Estimates.objects.filter(pk = self.kwargs['pk']).prefetch_related('option',).first()
        #contract = Contract.objects.filter(pk=self.kwargs['pk']).first()

        initial={'service': Service.objects.filter(pk=self.request.session.get('service', None)).first(),
                'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
                # 'option': estimates.option.all(),
                }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.kwargs['pk']
        print('get_context/////サービスIDとは・・・・・・・',service_id)
        service = Service.objects.get(pk=service_id)

        #contract_id = self.kwargs['pk']
        #contract = Contract.objects.get(pk=contract_id)

        context["service"] = service
        #context["contract"] = contract

        return context

    # def post(self, request, *args, **kwargs):
    def post(self, request, *args, **kwargs):
    
        form = self.get_form()
        print('フォーム',form)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
    #キャンセルした際はフォームばりっどを消す
    def form_valid(self, form):

        # フォームからDBのオブジェクトを仮生成（未保存）
        estimate_step1 = form.save(commit=False)
        print('estimate_step1_idの中身ーーーーーー',estimate_step1)

        # ユーザーを保存
        estimate_step1.user = self.request.user
        print('ユーザーはいってる？？？',estimate_step1.user)

        # サービスを保存
        service_id = self.kwargs['pk']
        estimate_step1.service = Service.objects.get(pk=service_id)
        print('サービスはいってる？？？',estimate_step1.service)
        # 本日日付
        today = datetime.now()

        # 作成日を登録
        estimate_step1.created_date = datetime.now()

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1)
        estimate_step1.expiration_date = expiration_date.date()

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')

        code_regex = re.compile('[!"+#$%&\'\\\\(),-./:;<=>?@[\\]^_`{|}~“”＆＊・（）、｀＋ ]')
        date = str(estimate_step1.created_date)
        date2 = code_regex.sub('', date)
        last_id = date2[8:14]
        print('last_idとはーーーーーー',last_id)
        # 通し番号を生成(見積もりIDを後ろに付与)
        # last_num = Estimates.objects.all().last()
        # if last_num:
        #     last_id = last_num.pk

        # else:
        #     last_id = 1

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
        start_day = form.cleaned_data['start_day']
        end_day =  start_day + relativedelta(years=1) - relativedelta(days=1)
        estimate_step1.end_day = end_day

        # 保存
        estimate_step1.save()

        # オプションの保存
        option_qs = form.cleaned_data['option']
        estimate_step1.option.set(option_qs)

        # 小計を算出
        # ↑で登録したプランを取得
        estimate_calc = Estimates.objects.select_related().get(pk=estimate_step1.id)
        # プランの月額を取得
        plan_unit_price = estimate_calc.plan.unit_price
        # プランの年額を取得
        plan_price = estimate_calc.plan.price

        # オプションの小計を算出
        option_unit_price_list = []
        option_price_list = []
        for option in estimate_calc.option.all():
            option_unit_price_list.append(option.unit_price)
            option_price_list.append(option.price)

        # 小計(税抜)
        minor_total = sum(option_price_list) + plan_price -3000
        estimate_calc.minor_total = minor_total

        # 消費税
        tax  = minor_total * settings.TAX
        estimate_calc.tax = tax

        # 合計
        total = minor_total + tax
        estimate_calc.total = total

        # 保存
        estimate_calc.save()


        # # POST送信された情報をセッションへ保存
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['estimate_step1_id'] = estimate_step1.id
        #self.request.session['estimate_step1'] = estimate_step1
        self.request.session['estimate_step1_service_name'] = estimate_step1.service.name
        self.request.session['estimate_step1_start_day'] = str(estimate_step1.start_day)

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 1

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('contracts:offer_step2'))

"""
申し込み-プラン・オプション選択(ステップ①) オリジナル
"""
# class OfferStep1(LoginRequiredMixin, FormView, CommonView):
#     model = Estimates
#     template_name = 'contracts/offer/step1.html'
#     form_class = OfferStep1Form
#     login_url = '/login/'


#     # フォームに対してログインユーザーを渡す
#     def get_form_kwargs(self):
#         kwargs = super(OfferStep1, self).get_form_kwargs()
#         kwargs.update({'user': self.request.user})
#         kwargs.update({'service_id': self.kwargs['service_id']})

#         return kwargs


#     def get_initial(self):
#         # estimates = Estimates.objects.filter(pk = self.kwargs['pk']).prefetch_related('option',).first()
#         contract = Contract.objects.filter(pk=self.kwargs['pk']).first()
#         initial={'service': contract.service,
#                 'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
#                 # 'option': estimates.option.all(),
#                 }
#         # 返す
#         return initial

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         service_id = self.kwargs['service_id']
#         service = Service.objects.get(pk=service_id)

#         contract_id = self.kwargs['pk']
#         contract = Contract.objects.get(pk=contract_id)

#         context["service"] = service
#         context["contract"] = contract

#         return context

#     def form_valid(self, form):

#         # フォームからDBのオブジェクトを仮生成（未保存）
#         estimate_step1 = form.save(commit=False)

#         # ユーザーを保存
#         estimate_step1.user = self.request.user

#         # サービスを保存
#         service_id = self.kwargs['service_id']
#         estimate_step1.service = Service.objects.get(pk=service_id)

#         # 本日日付
#         today = datetime.now()

#         # 作成日を登録
#         estimate_step1.created_date = datetime.now()

#         # 有効期限を生成(+1ヶ月)
#         expiration_date = today + relativedelta(months=1)
#         estimate_step1.expiration_date = expiration_date.date()

#         # 見積NO付与
#         # 本日日付の文字列を取得
#         day_number = datetime.now().strftime('%Y%m%d')

#         # 通し番号を生成(見積もりIDを後ろに付与)
#         last_num = Estimates.objects.all().last()
#         if last_num:
#             last_id = last_num.pk
#         else:
#             last_id = 1

#         if int(last_id) <= 9:
#             last_id = str("000") + str(last_id)
#         elif int(last_id) <= 99:
#             last_id = str("00") + str(last_id)
#         elif int(last_id) <= 999:
#             last_id = str("0") + str(last_id)
#         else:
#             last_id = str(last_id)

#         estimate_num = day_number + last_id
#         estimate_step1.num = estimate_num

#         # 契約終了日の設定
#         # 契約開始日から終了日を生成(+1年)
#         start_day = form.cleaned_data['start_day']
#         end_day =  start_day + relativedelta(years=1) - relativedelta(days=1)
#         estimate_step1.end_day = end_day

#         # 保存
#         estimate_step1.save()

#         # オプションの保存
#         option_qs = form.cleaned_data['option']
#         estimate_step1.option.set(option_qs)

#         # 小計を算出
#         # ↑で登録したプランを取得
#         estimate_calc = Estimates.objects.select_related().get(pk=estimate_step1.id)
#         # プランの月額を取得
#         plan_unit_price = estimate_calc.plan.unit_price
#         # プランの年額を取得
#         plan_price = estimate_calc.plan.price

#         # オプションの小計を算出
#         option_unit_price_list = []
#         option_price_list = []
#         for option in estimate_calc.option.all():
#             option_unit_price_list.append(option.unit_price)
#             option_price_list.append(option.price)

#         # 小計(税抜)
#         minor_total = sum(option_price_list) + plan_price
#         estimate_calc.minor_total = minor_total

#         # 消費税
#         tax  = minor_total * settings.TAX
#         estimate_calc.tax = tax

#         # 合計
#         total = minor_total + tax
#         estimate_calc.total = total

#         # 保存
#         estimate_calc.save()


#         # # POST送信された情報をセッションへ保存
#         # self.request.session['plan'] = plan.id

#         # 生成されたDBの対象行のIDをセッションに保存しておく
#         self.request.session['estimate_step1_id'] = estimate_step1.id

#         # ページ情報をセッションに保存しておく
#         self.request.session['page_num'] = 1

#         # ステップ2へ遷移
#         return HttpResponseRedirect(reverse('contracts:offer_step2'))

#おそらく、前のページへ戻るというとこの値が変わっていてエラーになってる説
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

        if not self.request.session['page_num'] == 1:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(OfferStep2, self).get_form_kwargs()
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        service =  Service.objects.get(name=self.request.session['estimate_step1_service_name'])
        start_day =  self.request.session['estimate_step1_start_day']

        # 小計をFormに送る
        kwargs.update({'total_price': estimate.minor_total})

        return kwargs


    def get_initial(self):

        estimates = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('method_payment',).first()

        initial={'method_payment': estimates.method_payment,
                'is_invoice_need': estimates.is_invoice_need,
                }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print('ステップ２コンテキストの中身',context)
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        service =  Service.objects.get(name=self.request.session['estimate_step1_service_name'])
        plan =  Plan.objects.get(pk=estimate.plan_id)


        context["service"] = service
        context["estimate"] = estimate
        context["plan"] = plan

        return context


    def form_valid(self, form):

        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        estimate_step3 = Estimates.objects.get(pk = self.request.session['estimate_step1_id'])

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']
        is_invoice_need = form.cleaned_data['is_invoice_need']
        bill_address = form.cleaned_data['bill_address']
        # 支払い方法の保存
        estimate_step3.method_payment = method_payment

        # 請求オプションの保存
        estimate_step3.is_invoice_need = is_invoice_need

        #請求書の宛先の保存
        estimate_step3.bill_address = bill_address

        # クレジット決済の場合は割引する
        if method_payment.id == 1:

            # プランの月額を取得
            plan_unit_price = estimate_step3.plan.unit_price
            # プランの年額を取得
            plan_price = estimate_step3.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in estimate_step3.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price
            if minor_total >= 10000:
                print('ここきてる＞＞＞',minor_total)
                estimate_step3.minor_total = minor_total - 3000
            else:
                print('えるすにおちた',minor_total)
                estimate_step3.minor_total = minor_total

            # 消費税
            tax  = estimate_step3.minor_total * settings.TAX
            estimate_step3.tax = tax

            # 合計
            total = estimate_step3.minor_total + tax
            estimate_step3.total = total

        else:
            # プランの月額を取得
            plan_unit_price = estimate_step3.plan.unit_price
            # プランの年額を取得
            plan_price = estimate_step3.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in estimate_step3.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price
            estimate_step3.minor_total = minor_total

            # 消費税
            tax  = minor_total * settings.TAX
            estimate_step3.tax = tax

            # 合計
            total = minor_total + tax
            estimate_step3.total = total


        # 保存
        estimate_step3.temp_check = False 
        estimate_step3.save()

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 2

        # 支払いへ遷移
        if method_payment.id == 1:
            return HttpResponseRedirect(reverse('payment:checkout_from_offer', kwargs={'pk': estimate_step3.id}))
        else:
            return HttpResponseRedirect(reverse('payment:checkout_bank_from_offer', kwargs={'pk': estimate_step3.id}))
"""
 申込-支払い方法の選択(ステップ②) オリジナル
"""
# class OfferStep2(LoginRequiredMixin, FormView, CommonView):
#     model = Estimates
#     template_name = 'contracts/offer/step2.html'
#     form_class = OfferStep2Form
#     login_url = '/login/'

#     # フォームに対してログインユーザーを渡す
#     def get_form_kwargs(self):
#         kwargs = super(OfferStep2, self).get_form_kwargs()
#         estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()

#         # 小計をFormに送る
#         kwargs.update({'total_price': estimate.minor_total})

#         return kwargs


#     def get_initial(self):
#         estimates = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('method_payment',).first()

#         initial={'method_payment': estimates.method_payment,
#                 'is_invoice_need': estimates.is_invoice_need,
#                 }
#         # 返す
#         return initial


#     def form_valid(self, form):

#         # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
#         estimate_step3 = Estimates.objects.get(pk = self.request.session['estimate_step1_id'])

#         # POSTで送信された値を取得
#         method_payment = form.cleaned_data['method_payment']
#         is_invoice_need = form.cleaned_data['is_invoice_need']

#         # 支払い方法の保存
#         estimate_step3.method_payment = method_payment

#         # 請求オプションの保存
#         estimate_step3.is_invoice_need = is_invoice_need

#         # クレジット決済の場合は割引する
#         if method_payment.name == "クレジット":

#             # プランの月額を取得
#             plan_unit_price = estimate_step3.plan.unit_price
#             # プランの年額を取得
#             plan_price = estimate_step3.plan.price

#             # オプションの小計を算出
#             option_unit_price_list = []
#             option_price_list = []

#             for option in estimate_step3.option.all():
#                 option_unit_price_list.append(option.unit_price)
#                 option_price_list.append(option.price)

#             # 小計(税抜)
#             minor_total = sum(option_price_list) + plan_price
#             if minor_total >= 10000:
#                 estimate_step3.minor_total = minor_total - 3000
#             else:
#                 estimate_step3.minor_total = minor_total

#             # 消費税
#             tax  = minor_total * settings.TAX
#             estimate_step3.tax = tax

#             # 合計
#             total = minor_total + tax
#             estimate_step3.total = total

#         else:
#             # プランの月額を取得
#             plan_unit_price = estimate_step3.plan.unit_price
#             # プランの年額を取得
#             plan_price = estimate_step3.plan.price

#             # オプションの小計を算出
#             option_unit_price_list = []
#             option_price_list = []

#             for option in estimate_step3.option.all():
#                 option_unit_price_list.append(option.unit_price)
#                 option_price_list.append(option.price)

#             # 小計(税抜)
#             minor_total = sum(option_price_list) + plan_price
#             estimate_step3.minor_total = minor_total

#             # 消費税
#             tax  = minor_total * settings.TAX
#             estimate_step3.tax = tax

#             # 合計
#             total = minor_total + tax
#             estimate_step3.total = total


#         # 保存
#         estimate_step3.save()

#         # 支払いへ遷移
#         if method_payment.name == "クレジット":
#             return HttpResponseRedirect(reverse('payment:checkout_from_offer', kwargs={'pk': estimate_step3.id}))
#         else:
#             return HttpResponseRedirect(reverse('payment:checkout_bank_from_offer', kwargs={'pk': estimate_step3.id}))

"""
キャンセル処理
"""
class OfferCancelView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        # セッションに「estimate_step1_id」があれば、取得した行を削除
        if 'estimate_step1_id' in request.session:
            estimate = Estimates.objects.get(pk = request.session['estimate_step1_id'])
            estimate.delete()

        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return HttpResponseRedirect(reverse('contracts:contract'))

"""
契約更新-変更なし
"""
class UpdateContractNoChangeStep1(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/update_contract/step1.html'
    form_class = UpdateContractNochangeStep1Form
    login_url = '/login/'


    def get_initial(self):
        contract = Contract.objects.filter(pk = self.kwargs['pk']).first()

        initial={'method_payment': contract.payment.method_payment,
                'is_invoice_need': contract.is_invoice_need,
                }
        # 返す
        return initial


    def form_valid(self, form):

        # 契約のオブジェクトを生成
        contract = Contract.objects.get(pk = self.kwargs['pk'])

        old_estimate = contract.estimate.all().first()

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']
        is_invoice_need = form.cleaned_data['is_invoice_need']

        # 支払い方法の保存
        estimate = Estimates.objects.create(user=old_estimate.user, service=old_estimate.service)
        estimate.method_payment=method_payment

        # プランの保存
        estimate.plan = old_estimate.plan

        # オプションの保存
        for option in old_estimate.option.all():
            estimate.option.add(option)

        # 請求オプションの保存
        estimate.is_invoice_need = is_invoice_need


        today = datetime.now()

        # 作成日を登録
        estimate.created_date = datetime.now()

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1)
        estimate.expiration_date = expiration_date.date()

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')

        # 通し番号を生成(見積もりIDを後ろに付与)
        last_num = Estimates.objects.all().last()
        if last_num:
            last_id = last_num.pk
        else:
            last_id = 1

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
        # 契約開始日から終了日を生成(+1年)
        start_day = contract.contract_end_date + relativedelta(days=1)
        estimate.start_day = start_day

        end_day =  start_day + relativedelta(years=1) - relativedelta(days=1)
        estimate.end_day = end_day


        # クレジット決済の場合は割引する
        if method_payment.id == 1:

            # プランの月額を取得
            plan_unit_price = old_estimate.plan.unit_price
            # プランの年額を取得
            plan_price = old_estimate.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in old_estimate.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price
            if minor_total >= 10000:
                estimate.minor_total = minor_total - 3000
            else:
                estimate.minor_total = minor_total

            # 消費税
            tax  = minor_total * settings.TAX
            estimate.tax = tax

            # 合計
            total = minor_total + tax
            estimate.total = total

        else:
            # プランの月額を取得
            plan_unit_price = old_estimate.plan.unit_price
            # プランの年額を取得
            plan_price = old_estimate.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in old_estimate.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price
            estimate.minor_total = minor_total

            # 消費税
            tax  = minor_total * settings.TAX
            estimate.tax = tax

            # 合計
            total = minor_total + tax
            estimate.total = total


        # 保存
        estimate.save()

        # 支払いへ遷移
        if method_payment.id == 1:
            return HttpResponseRedirect(reverse('payment:update_from_offer', kwargs={'pk': estimate.id}))
        else:
            return HttpResponseRedirect(reverse('payment:checkout_bank_from_offer', kwargs={'pk': estimate.id}))


"""
契約更新-変更あり①
"""
class UpdateContractChangeStep1(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/update_contract_change/step1.html'
    form_class = UpdateContractChangeStep1Form
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        print("セルフー", vars(self))
        kwargs = super(UpdateContractChangeStep1, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        kwargs.update({'service_id': self.kwargs['service_id']})

        return kwargs


    def get_initial(self):
        # estimates = Estimates.objects.filter(pk = self.kwargs['pk']).prefetch_related('option',).first()
        contract = Contract.objects.filter(pk=self.kwargs['pk']).first()
        initial={'service': contract.service,
                'plan': Plan.objects.filter(pk=self.request.session.get('plan', None)).first(),
                # 'option': estimates.option.all(),
                }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service_id = self.kwargs['service_id']
        service = Service.objects.get(pk=service_id)

        contract_id = self.kwargs['pk']
        contract = Contract.objects.get(pk=contract_id)

        context["service"] = service
        context["contract"] = contract

        return context

    def form_valid(self, form):

        # フォームからDBのオブジェクトを仮生成（未保存）
        estimate_step1 = form.save(commit=False)

        # ユーザーを保存
        estimate_step1.user = self.request.user

        # サービスを保存
        service_id = self.kwargs['service_id']
        estimate_step1.service = Service.objects.get(pk=service_id)

        # 本日日付
        today = datetime.now()

        # 作成日を登録
        estimate_step1.created_date = datetime.now()

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1)
        estimate_step1.expiration_date = expiration_date.date()

        # 見積NO付与
        # 本日日付の文字列を取得
        day_number = datetime.now().strftime('%Y%m%d')

        # 通し番号を生成(見積もりIDを後ろに付与)
        last_num = Estimates.objects.all().last()
        if last_num:
            last_id = last_num.pk
        else:
            last_id = 1

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
        start_day = form.cleaned_data['start_day']
        end_day =  start_day + relativedelta(years=1) - relativedelta(days=1)
        estimate_step1.end_day = end_day

        # 保存
        estimate_step1.save()

        # オプションの保存
        option_qs = form.cleaned_data['option']
        estimate_step1.option.set(option_qs)

        # 小計を算出
        # ↑で登録したプランを取得
        estimate_calc = Estimates.objects.select_related().get(pk=estimate_step1.id)
        # プランの月額を取得
        plan_unit_price = estimate_calc.plan.unit_price
        # プランの年額を取得
        plan_price = estimate_calc.plan.price

        # オプションの小計を算出
        option_unit_price_list = []
        option_price_list = []
        for option in estimate_calc.option.all():
            option_unit_price_list.append(option.unit_price)
            option_price_list.append(option.price)

        # 小計(税抜)
        minor_total = sum(option_price_list) + plan_price
        estimate_calc.minor_total = minor_total

        # 消費税
        tax  = minor_total * settings.TAX
        estimate_calc.tax = tax

        # 合計
        total = minor_total + tax
        estimate_calc.total = total

        # 保存
        estimate_calc.save()


        # # POST送信された情報をセッションへ保存
        # self.request.session['plan'] = plan.id


        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['estimate_step1_id'] = estimate_step1.id
        self.request.session['estimate_step1_service_name'] = estimate_step1.service.name
        self.request.session['estimate_step1_start_day'] = str(estimate_step1.start_day)

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 1

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('contracts:cont_update_change_step2'))


"""
契約更新-変更あり②
"""
class UpdateContractChangeStep2(LoginRequiredMixin, FormView, CommonView):
    model = Estimates
    template_name = 'contracts/update_contract_change/step2.html'
    form_class = UpdateContractChangeStep2Form
    login_url = '/login/'

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UpdateContractChangeStep2, self).get_form_kwargs()
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        service =  Service.objects.get(name=self.request.session['estimate_step1_service_name'])
        start_day =  self.request.session['estimate_step1_start_day']

        # 小計をFormに送る
        kwargs.update({'total_price': estimate.minor_total})

        return kwargs


    def get_initial(self):
        estimates = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('method_payment',).first()

        initial={'method_payment': estimates.method_payment,
                'is_invoice_need': estimates.is_invoice_need,
                }
        # 返す
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estimate = Estimates.objects.filter(pk = self.request.session['estimate_step1_id']).prefetch_related('option',).first()
        service =  Service.objects.get(name=self.request.session['estimate_step1_service_name'])
        plan =  Plan.objects.get(id=estimate.service_id)

        context["service"] = service
        context["estimate"] = estimate
        context["plan"] = plan

        return context

    def form_valid(self, form):
        # step1で保存した対象行のIDを使ってDBのオブジェクトを生成
        estimate_step3 = Estimates.objects.get(pk = self.request.session['estimate_step1_id'])

        # POSTで送信された値を取得
        method_payment = form.cleaned_data['method_payment']
        is_invoice_need = form.cleaned_data['is_invoice_need']

        # 支払い方法の保存
        estimate_step3.method_payment = method_payment

        # 請求オプションの保存
        estimate_step3.is_invoice_need = is_invoice_need

        # クレジット決済の場合は割引する
        if method_payment.id == 1:

            # プランの月額を取得
            plan_unit_price = estimate_step3.plan.unit_price
            # プランの年額を取得
            plan_price = estimate_step3.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in estimate_step3.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price
            if minor_total >= 10000:
                estimate_step3.minor_total = minor_total - 3000
            else:
                estimate_step3.minor_total = minor_total

            # 消費税
            tax  = minor_total * settings.TAX
            estimate_step3.tax = tax

            # 合計
            total = minor_total + tax
            estimate_step3.total = total

        else:
            # プランの月額を取得
            plan_unit_price = estimate_step3.plan.unit_price
            # プランの年額を取得
            plan_price = estimate_step3.plan.price

            # オプションの小計を算出
            option_unit_price_list = []
            option_price_list = []

            for option in estimate_step3.option.all():
                option_unit_price_list.append(option.unit_price)
                option_price_list.append(option.price)

            # 小計(税抜)
            minor_total = sum(option_price_list) + plan_price
            estimate_step3.minor_total = minor_total

            # 消費税
            tax  = minor_total * settings.TAX
            estimate_step3.tax = tax

            # 合計
            total = minor_total + tax
            estimate_step3.total = total

        # 保存
        estimate_step3.save()

        # ページ情報をセッションに保存しておく
        self.request.session['page_num'] = 1

        # 支払いへ遷移
        if method_payment.id == 1:
            return HttpResponseRedirect(reverse('payment:update_from_offer', kwargs={'pk': estimate_step3.id}))
        else:
            return HttpResponseRedirect(reverse('payment:checkout_bank_from_offer', kwargs={'pk': estimate_step3.id}))

"""
見積書存在確認
"""
class EstimateAjaxView(View):
    def post(self, request):

        s_id = request.POST.get('service')
        estimate = Estimates.objects.filter(service_id = s_id,temp_check=False)
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
        context["estimates"] = Estimates.objects.filter(user=current_user_id,service_id=service_id,temp_check=False)
        context["service"] = service
        return context 