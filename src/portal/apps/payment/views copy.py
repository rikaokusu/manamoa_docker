from django.conf import settings
from django.shortcuts import render,redirect
from django.views.generic import View, TemplateView, DetailView, UpdateView, FormView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin, ModelFormMixin
from accounts.models import User, Company, Messages, Service
from contracts.models import Estimates, Contract, Plan
from .models import Payment
from .forms import ChangeContractForm
from django.urls import reverse_lazy
# import requests
import payjp
import stripe

# 有効期限の保存
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

# ログインのデコレータ
from django.contrib.auth.mixins import LoginRequiredMixin

# 小数点以下切り捨て
import math

# ajax用
from django.http import JsonResponse

# フロントへメッセージ送信
from django.contrib import messages

# リダイレクト
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse

# mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin

# 別ページでログイン中の他社ユーザーアクセス制限
class OnlyOurContractMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        contract_instance = self.get_object()

        return contract_instance.user.company_id == self.request.user.company_id

# 全てで実行させるView
class CommonView(ContextMixin):
    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_user = self.request.user
        context["current_user"] = current_user

        #PAY.JPのパブリックキーをテンプレートへ渡す
        context["pay_public_key"] = settings.PAYJP_PUBLICKEY

        return context



"""
カード情報
"""
class CardInfo(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'payment/card_info.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #PAY.JPのパブリックキーをテンプレートへ渡す
        context["pay_public_key"] = settings.PAYJP_PUBLICKEY

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY

        if self.request.user.payjp_cus_id:

            # 顧客情報の取得
            customer = payjp.Customer.retrieve(self.request.user.payjp_cus_id)

            # カード情報の取得
            card = customer.cards.retrieve(customer.default_card)

            # カード情報から有効期限、ブランド、下4桁を取得
            context["card_exp_month"] = card.exp_month
            context["card_exp_year"] = card.exp_year
            context["card_brand"] = card.brand
            context["card_last4"] = card.last4


        return context



# """
# カードの登録
# """
# class CardCreate(LoginRequiredMixin, View):
#     login_url = '/login/'

#     def post(self, request):
#         """
#         カードの作成(PAYJP側で顧客情報の作成)
#         """
#         # トークンの取得
#         payjp_token = request.POST.get("payjp-token")

#         #顧客の作成
#         payjp.api_key = settings.PAYJP_SECRETKEY
#         customer = payjp.Customer.create(
#             card= payjp_token,
#             email= self.request.user.email
#         )

#         #顧客IDをユーザーに登録
#         user = User.objects.get(pk=self.request.user.pk)
#         user.payjp_cus_id = customer.id
#         user.save()

#         messages.success(request, "クレジットカードを登録しました。")


#         return redirect('payment:card_info')

"""
カードの登録
"""
class CardCreate(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request):
        """
        カードの作成(Stripe側で顧客情報の作成)
        """
        # トークンの取得
        #stripe_token = request.POST.get("stripe-token")

        #顧客の作成
        stripe.api_key = settings.STRIPE_API_KEY
        print('1顧客の作成',stripe.api_key)
        # Customerオブジェクト生成（引数は任意→今回はnameを指定）
        customer = stripe.Customer.create(
        card= stripe_token,
        email=self.request.user.email,
        )
        
        # SetupIntentオブジェクト生成
        setup_intent = stripe.SetupIntent.create(
        customer=customer.id,# 生成したCustomerのIDを指定
        payment_method_types=["card"],# 支払い方法→今回はクレジットカード（"card"）
        )

         # 作成したSetupIntentからclient_secretを取得する→テンプレートへ渡す
        context = {
        "client_secret": setup_intent.client_secret,
        }
        template_name = 'create_card.html'
        return render(request, template_name, context)

        #顧客IDをユーザーに登録
        user = User.objects.get(pk=self.request.user.pk)
        user.stripe_cus_id = customer.id
        user.save()

        messages.success(request, "クレジットカードを登録しました。")


        return redirect('payment:card_info')



"""
カードの更新
"""
class CardUpdate(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request):
        """
        カードの更新（既存を削除して新規登録）
        """
        # トークンの取得
        payjp_token = request.POST.get("payjp-token")

        current_user = self.request.user

        payjp_cus_id = self.request.user.payjp_cus_id

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY

        # 顧客情報の取得
        customer = payjp.Customer.retrieve(payjp_cus_id)

        # 既存カードの取得
        card = customer.cards.retrieve(customer.default_card)

        # カードの削除
        card.delete()

        # 新規カードの登録
        customer.cards.create(
            card=payjp_token,
        )

        messages.success(request, "クレジットカードを更新しました。")


        return redirect('payment:card_info')




"""
支払い(クレジット)
"""
class Checkout(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/checkout.html'
    context_object_name = 'estimate'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.payjp_cus_id:
            messages.error(request, "クレジットカードが未登録です。登録してください。")
            return redirect('payment:card_info')
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, pk):
        print('pkの値ーーーー',pk)
        autocheckout = request.POST.get('autocheckout')
        is_start_now = request.POST.get('is_start_now')

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY

        # PAYJPの顧客IDを取得
        customer_id = self.request.user.payjp_cus_id
        print('ここまではOK11111',customer_id)

        # 見積書に記載されたプランのPAY.JPIDを取得
        # estimate = Estimates.objects.select_related().get(pk=pk)
        estimate = Estimates.objects.select_related().get(pk=pk)

        payjp_plan_id = estimate.plan.payjp_plan_id
        print('ここまではOK22222',customer_id)

        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=request.user)
        print('ここまではOK33333',customer_id)

        # 契約DBへ本契約の有効期限を保存
        contract, created = Contract.objects.get_or_create(user=self.request.user, service=estimate.service)
        print('ここまではOK44444',customer_id)

        try:

            # """
            # payjp側処理
            # """
            
            # 定期課金の作成
            payjp_plan = payjp.Subscription.create(
                plan = payjp_plan_id,
                customer = customer_id
            )
            print('定期課金の作成')

            # 作成したPAYJP定期課金のIDを保存
            payment.payjp_plan = payjp_plan.id
            print('作成したPAYJP定期課金のIDを保存')
            # 自動更新OFFの場合は、その場でキャンセルする
            if autocheckout ==  "False":
                payjp_plan.cancel()

            # 定期課金が作成された
            if payjp_plan.created:

                # 見積書に記載されたディスクサイズオプションのPAY.JPIDを取得
                if estimate.option.all():

                    for option in estimate.option.all():
                        # 定期課金の作成
                        option_plan = payjp.Subscription.create(
                            plan = option.payjp_plan_id,
                            customer = customer_id
                        )
                        payjp_option_id = option_plan.id

                        # 自動更新OFFの場合は、その場でキャンセルする
                        if autocheckout ==  "False":
                            option_plan.cancel()

                        # ManyToManyに登録するためオブジェクトを作成
                        payjp_option, created = PayjpOption.objects.get_or_create(name=option.name, payjp_id=payjp_option_id)

                        # 支払いテーブルと紐付け
                        payment.payjp_option.add(payjp_option)
                        print('支払いテーブルと紐づけ')
                    # 見積りのオプションを契約テーブルに上書き保存
                    contract.option.set(estimate.option.all())

                else:
                    # 契約テーブル上のオプションをリセット
                    contract.option.clear()

                # 支払いフラグをON
                payment.is_paymented = True

                # 支払い日を登録
                payment.created_date = datetime.fromtimestamp(payjp_plan.created)

                # 契約日付
                # すぐに開始の場合は支払い日付をセット
                if is_start_now == None:
                    contract.contract_start_date = estimate.start_day
                    contract.contract_end_date = estimate.end_day
                else:
                    contract.contract_start_date = datetime.fromtimestamp(payjp_plan.current_period_start)
                    contract.contract_end_date = datetime.fromtimestamp(payjp_plan.current_period_end)

                # 支払い日付
                contract.pay_start_date = datetime.fromtimestamp(payjp_plan.current_period_start)
                contract.pay_end_date = datetime.fromtimestamp(payjp_plan.current_period_end)


                # """
                # 後処理
                # """
                # 試用プランの削除
                contract.plan = None

                # 紐づく支払いを契約テーブルに保存
                contract.payment=payment

                # 見積りのプランを契約テーブルに保存
                contract.plan = estimate.plan

                # ステータスの変更
                contract.status = "2" #本番

                # 自動更新フラグをON
                if autocheckout ==  "True":
                    contract.is_autocheckout = True
                else:
                    contract.is_autocheckout = False

                # 見積りIDを保存
                contract.estimate.add(estimate)

                # 請求書オプションを契約テーブルに保存
                contract.is_invoice_need = estimate.is_invoice_need

                # 見積りの小計を契約テーブルに保存
                contract.minor_total = estimate.minor_total

                # 見積りの消費税を契約テーブルに保存
                contract.tax = estimate.tax

                # 見積りの合計を契約テーブルに保存
                contract.total = estimate.total

                # 見積りの支払い方法を支払いテーブルに保存
                payment.method_payment = estimate.method_payment

                # 保存
                contract.save()
                payment.save()


                # 見積り使用フラグをON
                estimate.is_use = True

                estimate.save()

        except payjp.error.CardError as e:
            context = {
                "err_message":"このカードはご利用になれません。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.InvalidRequestError as e:
            context = {
                "err_message":"入力いただいた情報に誤りがあります。今一度ご確認をお願いします。解決できない場合はエラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.AuthenticationError as e:
            context = {
                "err_message":"システムエラーが発生しております。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.APIConnectionError as e:
            context = {
                "err_message":"APIConnectionErroによりエラーが発生しています。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)


        messages.success(request, "お申し込みが完了しました。")


        return redirect('contracts:estimate')



"""
支払い(クレジット) 申し込みからの支払い
"""
class CheckoutFromOffer(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/checkout_from_offer.html'
    context_object_name = 'estimate'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.payjp_cus_id:
            messages.error(request, "クレジットカードが未登録です。登録してください。")
            return redirect('payment:card_info')
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, pk):
        autocheckout = request.POST.get('autocheckout')
        is_start_now = request.POST.get('is_start_now')

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY

        # PAYJPの顧客IDを取得
        customer_id = self.request.user.payjp_cus_id

        # 見積書に記載されたプランのPAY.JPIDを取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        payjp_plan_id = estimate.plan.payjp_plan_id

        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=request.user)

        # 契約DBへ本契約の有効期限を保存
        contract, created = Contract.objects.get_or_create(user=request.user, service=estimate.service)


        try:

            """
            payjp側処理
            """

            # 定期課金の作成
            payjp_plan = payjp.Subscription.create(
                plan = payjp_plan_id,
                customer = customer_id
            )
            # 作成したPAYJP定期課金のIDを保存
            payment.payjp_plan = payjp_plan.id

            # 自動更新OFFの場合は、その場でキャンセルする
            if autocheckout ==  "False":
                payjp_plan.cancel()

            # 定期課金が作成された
            if payjp_plan.created:

                # 見積書に記載されたディスクサイズオプションのPAY.JPIDを取得
                if estimate.option.all():

                    for option in estimate.option.all():
                        # 定期課金の作成
                        option_plan = payjp.Subscription.create(
                            plan = option.payjp_plan_id,
                            customer = customer_id
                        )
                        payjp_option_id = option_plan.id

                        # 自動更新OFFの場合は、その場でキャンセルする
                        if autocheckout ==  "False":
                            option_plan.cancel()

                        # ManyToManyに登録するためオブジェクトを作成
                        payjp_option, created = PayjpOption.objects.get_or_create(name=option.name, payjp_id=payjp_option_id)

                        # 支払いテーブルと紐付け
                        payment.payjp_option.add(payjp_option)

                    # 見積りのオプションを契約テーブルに上書き保存
                    contract.option.set(estimate.option.all())

                else:
                    # 契約テーブル上のオプションをリセット
                    contract.option.clear()

                # 支払いフラグをON
                payment.is_paymented = True

                # 支払い日を登録
                payment.created_date = datetime.fromtimestamp(payjp_plan.created)

                # 契約日付
                # すぐに開始の場合は支払い日付をセット
                if is_start_now == None:
                    contract.contract_start_date = estimate.start_day
                    contract.contract_end_date = estimate.end_day
                else:
                    contract.contract_start_date = datetime.fromtimestamp(payjp_plan.current_period_start)
                    contract.contract_end_date = datetime.fromtimestamp(payjp_plan.current_period_end)

                # 支払い日付
                contract.pay_start_date = datetime.fromtimestamp(payjp_plan.current_period_start)
                contract.pay_end_date = datetime.fromtimestamp(payjp_plan.current_period_end)


                """
                後処理
                """
                # 試用プランの削除
                contract.plan = None

                # 紐づく支払いを契約テーブルに保存
                contract.payment=payment

                # 見積りのプランを契約テーブルに保存
                contract.plan = estimate.plan

                # ステータスの変更
                contract.status = "2" #本番

                # 自動更新フラグをON
                if autocheckout ==  "True":
                    contract.is_autocheckout = True
                else:
                    contract.is_autocheckout = False

                # 見積りIDを保存
                contract.estimate.add(estimate)

                # 請求書オプションを契約テーブルに保存
                contract.is_invoice_need = estimate.is_invoice_need

                # 見積りの小計を契約テーブルに保存
                contract.minor_total = estimate.minor_total

                # 見積りの消費税を契約テーブルに保存
                contract.tax = estimate.tax

                # 見積りの合計を契約テーブルに保存
                contract.total = estimate.total

                # 見積りの支払い方法を支払いテーブルに保存
                payment.method_payment = estimate.method_payment

                # 保存
                contract.save()
                payment.save()


                # 見積り使用フラグをON
                estimate.is_use = True

                estimate.save()

        except payjp.error.CardError as e:
            context = {
                "err_message":"このカードはご利用になれません。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.InvalidRequestError as e:
            context = {
                "err_message":"入力いただいた情報に誤りがあります。今一度ご確認をお願いします。解決できない場合はエラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.AuthenticationError as e:
            context = {
                "err_message":"システムエラーが発生しております。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.APIConnectionError as e:
            context = {
                "err_message":"APIConnectionErroによりエラーが発生しています。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)


        messages.success(request, "お申し込みが完了しました。")


        return redirect('contracts:estimate')



"""
支払い(クレジット) 申し込みからの更新
"""
class UpdateFromOffer(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/update_contract/checkout_from_offer.html'
    context_object_name = 'estimate'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.payjp_cus_id:
            messages.error(request, "クレジットカードが未登録です。登録してください。")
            return redirect('payment:card_info')
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, pk):
        autocheckout = request.POST.get('autocheckout')
        is_start_now = request.POST.get('is_start_now')

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY

        # PAYJPの顧客IDを取得
        customer_id = self.request.user.payjp_cus_id

        # 見積書に記載されたプランのPAY.JPIDを取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        payjp_plan_id = estimate.plan.payjp_plan_id

        # 契約DBへ本契約の有効期限を保存
        contract = Contract.objects.get(user=request.user, service=estimate.service)

        # 支払い管理レコードを作成
        payment = Payment.objects.get(user=request.user)

        # 契約終了日
        contract_end_date = contract.contract_end_date

        unix_contract_end_date = contract_end_date.timestamp()

        print("終了日3", unix_contract_end_date)

        try:

            """
            payjp側処理
            """

            # 既存定期課金の削除
            subscription = payjp.Subscription.retrieve(payment.payjp_plan)
            subscription.delete()

            # 定期課金の作成
            payjp_plan = payjp.Subscription.create(
                plan = payjp_plan_id,
                customer = customer_id,
                # 課金処理を前契約の完了日とするためトライアル日を設定
                trial_end = int(unix_contract_end_date)
            )
            # 作成したPAYJP定期課金のIDを保存
            payment.payjp_plan = payjp_plan.id

            # 自動更新OFFの場合は、その場でキャンセルする
            if autocheckout ==  "False":
                payjp_plan.cancel()

            # 定期課金が作成された
            if payjp_plan.created:

                # 見積書に記載されたディスクサイズオプションのPAY.JPIDを取得
                if estimate.option.all():

                    for option in estimate.option.all():
                        # 定期課金の作成
                        option_plan = payjp.Subscription.create(
                            plan = option.payjp_plan_id,
                            customer = customer_id
                        )
                        payjp_option_id = option_plan.id

                        # 自動更新OFFの場合は、その場でキャンセルする
                        if autocheckout ==  "False":
                            option_plan.cancel()

                        # ManyToManyに登録するためオブジェクトを作成
                        payjp_option, created = PayjpOption.objects.get_or_create(name=option.name, payjp_id=payjp_option_id)

                        # 支払いテーブルと紐付け
                        payment.payjp_option.add(payjp_option)

                    # 見積りのオプションを契約テーブルに上書き保存
                    contract.option.set(estimate.option.all())

                # 支払いフラグをON
                payment.is_paymented = True

                # 支払い回数をカウントアップ
                payment.pay_count = payment.pay_count + 1


                # 支払い日を登録
                payment.created_date = datetime.fromtimestamp(payjp_plan.created)

                # 契約日付
                # すぐに開始の場合は支払い日付をセット
                if is_start_now == None:
                    contract.contract_start_date = estimate.start_day
                    contract.contract_end_date = estimate.end_day
                else:
                    contract.contract_start_date = datetime.fromtimestamp(payjp_plan.current_period_start)
                    contract.contract_end_date = datetime.fromtimestamp(payjp_plan.current_period_end)

                # 支払い日付
                contract.pay_start_date = datetime.fromtimestamp(payjp_plan.current_period_start)
                contract.pay_end_date = datetime.fromtimestamp(payjp_plan.current_period_end)


                """
                後処理
                """
                # 試用プランの削除
                contract.plan = None

                # 紐づく支払いを契約テーブルに保存
                contract.payment=payment

                # 見積りのプランを契約テーブルに保存
                contract.plan = estimate.plan

                # ステータスの変更
                contract.status = "2" #本番

                # 自動更新フラグをON
                if autocheckout ==  "True":
                    contract.is_autocheckout = True
                else:
                    contract.is_autocheckout = False

                # 見積りIDを保存
                contract.estimate.add(estimate)

                # 請求書オプションを契約テーブルに保存
                contract.is_invoice_need = estimate.is_invoice_need

                # 見積りの小計を契約テーブルに保存
                contract.minor_total = estimate.minor_total

                # 見積りの消費税を契約テーブルに保存
                contract.tax = estimate.tax

                # 見積りの合計を契約テーブルに保存
                contract.total = estimate.total

                # 見積りの支払い方法を支払いテーブルに保存
                payment.method_payment = estimate.method_payment

                # 保存
                contract.save()
                payment.save()


                # 見積り使用フラグをON
                estimate.is_use = True

                estimate.save()

        except payjp.error.CardError as e:
            context = {
                "err_message":"このカードはご利用になれません。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.InvalidRequestError as e:
            context = {
                "err_message":"入力いただいた情報に誤りがあります。今一度ご確認をお願いします。解決できない場合はエラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.AuthenticationError as e:
            context = {
                "err_message":"システムエラーが発生しております。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name

            }
            return  render(request, 'payment/checkout_error.html', context)

        except payjp.error.APIConnectionError as e:
            context = {
                "err_message":"APIConnectionErroによりエラーが発生しています。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name

            }
            return  render(request, 'payment/checkout_error.html', context)


        messages.success(request, "お申し込みが完了しました。")


        return redirect('manager:estimate')



"""
支払い(銀行振込)
"""
class CheckoutBank(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/checkout_bank.html'
    context_object_name = 'estimate'
    login_url = '/login/'


    def post(self, request, pk):

        # 見積書に記載された情報を取得
        estimate = Estimates.objects.select_related().get(pk=pk)

        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=request.user)

        # 契約DBへ本契約の有効期限を保存
        contract, created = Contract.objects.get_or_create(user=request.user, service=estimate.service)

        try:

            # 試用プランの削除
            contract.plan = None

            # 紐づく支払いを契約テーブルに保存
            contract.payment=payment

            # 見積りのプランを契約テーブルに保存
            contract.plan = estimate.plan

            # 見積りのオプションを契約テーブルに上書き保存
            contract.option.set(estimate.option.all())

            # ステータスの変更
            contract.status = "2" #本番

            # 銀行振込なので自動更新もNull
            contract.is_autocheckout = None

            # 見積りIDを保存
            contract.estimate.add(estimate)

            # 請求書オプションを契約テーブルに保存
            contract.is_invoice_need = estimate.is_invoice_need

            # 見積りの小計を契約テーブルに保存
            contract.minor_total = estimate.minor_total

            # 見積りの消費税を契約テーブルに保存
            contract.tax = estimate.tax

            # 見積りの合計を契約テーブルに保存
            contract.total = estimate.total

            # 契約開始・終了日付をセット
            contract.contract_start_date = estimate.start_day
            contract.contract_end_date = estimate.end_day

            # 支払いフラグをOFF(入金未確認)
            payment.is_paymented = False

            # 見積りの支払い方法を支払いテーブルに保存
            payment.method_payment = estimate.method_payment

            # 保存
            contract.save()
            payment.save()

            # 見積り使用フラグをON
            estimate.is_use = True
            estimate.save()

        except Exception as e:
            context = {
                "err_message":"問題が発生しました。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)


        messages.success(request, "お申し込みが完了しました。")

        return redirect('contracts:estimate')



"""
支払い(銀行振込)
"""
class CheckoutBankFromOffer(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/checkout_bank_from_offer.html'
    context_object_name = 'estimate'
    login_url = '/login/'


    def post(self, request, pk):

        # 見積書に記載された情報を取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        print('CheckoutBankFromOfferestimateの値取れているか',estimate)
        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=request.user)

        # 契約DBへ本契約の有効期限を保存
        contract, created = Contract.objects.get_or_create(user=request.user, service=estimate.service)

        try:

            # 試用プランの削除
            contract.plan = None

            # 紐づく支払いを契約テーブルに保存
            contract.payment=payment

            # 見積りのプランを契約テーブルに保存
            contract.plan = estimate.plan

            # 見積りのオプションを契約テーブルに上書き保存
            contract.option.set(estimate.option.all())

            # ステータスの変更
            contract.status = "2" #本番

            # 銀行振込なので自動更新もNull
            contract.is_autocheckout = None

            # 見積りIDを保存
            contract.estimate.add(estimate)

            # 請求書オプションを契約テーブルに保存
            contract.is_invoice_need = estimate.is_invoice_need

            # 見積りの小計を契約テーブルに保存
            contract.minor_total = estimate.minor_total

            # 見積りの消費税を契約テーブルに保存
            contract.tax = estimate.tax

            # 見積りの合計を契約テーブルに保存
            contract.total = estimate.total

            # 契約開始・終了日付をセット
            contract.contract_start_date = estimate.start_day
            contract.contract_end_date = estimate.end_day

            # 支払いフラグをOFF(入金未確認)
            payment.is_paymented = False

            # 見積りの支払い方法を支払いテーブルに保存
            payment.method_payment = estimate.method_payment

            # 保存
            contract.save()
            payment.save()

            # 見積り使用フラグをON
            estimate.is_use = True
            estimate.save()

        except Exception as e:
            context = {
                "err_message":"問題が発生しました。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)


        messages.success(request, "お申し込みが完了しました。")

        return redirect('contracts:estimate')


"""
来年度分の手動支払い
"""
# @method_decorator(login_required, name = 'dispatch')
class ManualCheckout(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/manualcheckout.html'
    context_object_name = 'estimate'
    login_url = '/manager/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #PAY.JPのパブリックキーをテンプレートへ渡す
        context["pay_public_key"] = settings.PAYJP_PUBLICKEY
        return context


    def post(self, request, pk):
        """手動支払いにチェックが入っている場合"""
        print("来年度分の手動支払い")
        # トークンの取得
        payjp_token = request.POST.get("payjp-token")
        print(payjp_token)

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY

        # 見積書に記載された合計額を取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        total = estimate.total
        print("合計額", total)

        #　支払い
        try:
            charge = payjp.Charge.create(
                amount = total,
                card = payjp_token,
                currency='jpy',
            )

            # 作成日付を取得して終了日を生成
            start_date = datetime.fromtimestamp(charge.created)
            end_date = start_date + relativedelta(years=1) - relativedelta(days=1)

            # 契約DBへ本契約の有効期限を保存
            print("見積書内のサービス", estimate.service)
            contract = Contract.objects.get(user=request.user.id, service=estimate.service)

            contract.status = "2"

            # 契約日付
            contract.contract_start_date = start_date
            contract.contract_end_date = end_date

            # 支払い日付
            contract.pay_start_date = start_date
            contract.pay_end_date = end_date

            # 手動支払いフラグ
            contract.is_manualcheckout = True

            contract.save()

        except payjp.error.InvalidRequestError as e:
            context = {
                "err_message":"エラーが発生しました。運営に問い合わせてください。メッセージ：" + str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        return redirect('payment:checkout_done')


"""
支払い完了
"""
# @method_decorator(login_required, name = 'dispatch')
# class CheckoutDone(LoginRequiredMixin, TemplateView, CommonView):
#     template_name = 'payment/checkout_done.html'
#     login_url = '/manager/login/'


"""
プラン・オプション変更
"""
# @method_decorator(login_required, name = 'dispatch')
class ChangeContract(LoginRequiredMixin, OnlyOurContractMixin, UpdateView, CommonView):
    model = Contract
    template_name = 'payment/change_contract/change_contract_1.html'
    form_class = ChangeContractForm
    success_url = reverse_lazy('payment:change_plan_confirm')
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_id = self.kwargs['pk']
        contract = Contract.objects.get(pk=contract_id)

        context["contract"] = contract

        return context


    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(ChangeContract, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        kwargs.update({'contract_id': self.kwargs['pk']})

        return kwargs

    def form_valid(self, form):
        print("form_validだよ")

        # 変更後のプラン情報を取得
        plan = form.cleaned_data['plan']
        disksize = form.cleaned_data['disksize']
        usernum = form.cleaned_data['usernum']

        # 古い契約情報の取得
        old_contract_data = Contract.objects.get(pk=self.kwargs['pk'])

        print("旧プラン", old_contract_data.plan)

        # ベーシックプランの新旧IDを取得
        old_plan = old_contract_data.plan
        print("旧プラン2", old_contract_data.plan)

        new_plan = plan

        # ディスクサイズオプションの新旧IDを取得
        old_disksize = old_contract_data.disksize
        new_disksize = disksize

        # ユーザー数オプションの新旧IDを取得
        old_usernum = old_contract_data.usernum
        new_usernum = usernum

        print("旧プラン", old_plan)
        print("新プラン", new_plan)

        if old_plan == new_plan:
            print("ベーシックプラン変更無し")
        else:
            old_plan_price = Plan.objects.values("price").get(pk=old_plan.id)
            print("旧プランの金額", old_plan_price)
            new_plan_price = Plan.objects.values("price").get(pk=new_plan.id)
            print("新プランの金額", new_plan_price)

            # 契約中の終了期間を取得
            old_contract_end_date = old_contract_data.contract_end_date
            print("旧プラン日付", old_contract_end_date)
            print("旧プラン日付タイプ", type(old_contract_end_date))

            # 今日の日付を取得
            today = datetime.now(timezone.utc)
            print("新プラン日付", today)

            # 未来日付 - 本日
            remaining_day = (old_contract_end_date.date() - today.date()).days

            print("残日数", remaining_day)

            # remaining_day_str =  remaining_day.strftime('%d')

            # 差額を計算
            difference_price = (int(new_plan_price["price"]) - int(old_plan_price["price"])) / 365 * int(remaining_day)

            # 切り捨て
            difference_price_math = math.floor(difference_price)

            print("差額", difference_price_math)

            # 入力した値を、セッションに保存
            self.request.session['form_data'] = self.request.POST
            self.request.session['remaining_day'] = remaining_day
            self.request.session['difference_price_math'] = difference_price_math


        contract = form.save(commit=False)

        return super().form_valid(form)

"""
プラン変更確認画面
"""
# @method_decorator(login_required, name = 'dispatch')
class ChangePlanConfirm(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'payment/change_contract/change_contract_2.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form_data = self.request.session.get('form_data', None)
        difference_price_math = self.request.session.get('difference_price_math', None)

        print(form_data)
        print(difference_price_math)
        context['form'] = PlanChangeForm(form_data)
        context['difference_price_math'] = difference_price_math

        #PAY.JPのパブリックキーをテンプレートへ渡す
        context["pay_public_key"] = settings.PAYJP_PUBLICKEY

        return context

    def post(self, request):
            print("差額手動支払い")
            # トークンの取得
            payjp_token = request.POST.get("payjp-token")
            print(payjp_token)

            # PAYJPのシークレットキーの読み込み
            payjp.api_key = settings.PAYJP_SECRETKEY

            # 見積書に記載された合計額を取得
            difference_price_math = request.session.pop('difference_price_math', None)

            print(difference_price_math)
            #　支払い
            try:
                charge = payjp.Charge.create(
                    amount = difference_price_math,
                    card = payjp_token,
                    currency='jpy',
                )

            except payjp.error.InvalidRequestError as e:
                context = {
                    "err_message":"エラーが発生しました。運営に問い合わせてください。メッセージ：" + str(e)
                }
                return  render(request, 'payment/checkout_error.html', context)

            return redirect('payment:checkout_done')

"""
解約
"""
# @method_decorator(login_required, name = 'dispatch')
class Cancellation(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request):

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY
        contract_id = request.POST.get('contract_id')
        contract = Contract.objects.filter(pk=contract_id).select_related('payment').first()
        estimate = contract.estimate.all().first()
        
        if contract.payment.method_payment.id == 1:
            #payjpはオリジナル保持
            try:

                # 基本プランの解約(PAYJPとしてはキャンセル処理)
                subscription_plan = payjp.Subscription.retrieve(contract.payment.payjp_plan)
                cancel_sub_plan = subscription_plan.delete()

                # 基本プランの解約(PAYJPとしてはキャンセル処理)
                for option in contract.payment.payjp_option.all():
                    subscription_option = payjp.Subscription.retrieve(option.payjp_id)
                    cancel_sub_option = subscription_option.delete()


                contract.status = "3" #3は解約

                # 契約終了日を解約した日に更新
                contract.contract_end_date = datetime.now()

                contract.save()

            except payjp.error.CardError as e:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました" + str(e),
                                    })

            except payjp.error.InvalidRequestError as e:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました" + str(e),
                                    })

            except payjp.error.AuthenticationError as e:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました" + str(e),
                                    })

            except payjp.error.APIConnectionError as e:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました" + str(e),
                                    })

            except:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました",
                                    })



            return JsonResponse({"status": "ok",
                                "message": "解約しました",
                                })
        else:
            contract.status = "3" #3は解約

            # 契約終了日を解約した日に更新
            contract.contract_end_date = datetime.now()

            contract.save()

            estimate.is_use = False
            estimate.save()

            return JsonResponse({"status": "ok",
                                "message": "解約しました",
                                })



"""
自動更新ON/OFF(Ajax)
"""
class AutoCheckoutChange(View):
    def post(self, request):
        # POSTで送られてきた削除対象のID(リスト)を取得
        is_checked = request.POST.get('is_checked')
        contract_id = request.POST.get('contract_id')

        # PAYJPのシークレットキーの読み込み
        payjp.api_key = settings.PAYJP_SECRETKEY

        # 契約オブジェクトの取得
        contract = Contract.objects.filter(pk=contract_id).select_related('payment').first()

        # 自動更新ONの場合
        if is_checked == "true":
            try:
                # 基本プランの再開(PAYJPとしては、キャンセル状態の定期課金を再開させる)
                subscription_plan = payjp.Subscription.retrieve(contract.payment.payjp_plan)
                subscription_plan.resume()

                # 契約に紐づくオプションの再開
                for option in contract.payment.payjp_option.all():
                    subscription_option = payjp.Subscription.retrieve(option.payjp_id)
                    subscription_option.resume()

                # 自動更新フラグをON
                contract.is_autocheckout = True

                contract.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "変更しました",
                                    })

            except Exception as e:
                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })
        # 自動更新OFFの場合
        else:
            try:

                # 基本プランの解約(PAYJPとしてはキャンセル処理。現在の周期の終了日をもって定期課金を終了させる。)
                subscription_plan = payjp.Subscription.retrieve(contract.payment.payjp_plan)
                subscription_plan.cancel()

                # 契約に紐づくオプションの解約
                for option in contract.payment.payjp_option.all():
                    subscription_option = payjp.Subscription.retrieve(option.payjp_id)
                    subscription_option.cancel()

                # 自動更新フラグをOFF
                contract.is_autocheckout = False

                contract.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "変更しました",
                                    })


            except Exception as e:
                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })