from django.conf import settings
from django.shortcuts import render,redirect
from django.views.generic import View, TemplateView, DetailView, UpdateView, FormView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin, ModelFormMixin
from accounts.models import User, Company, Messages, Service, Stripe,Notification,Read
from contracts.models import Estimates, Contract, Plan
from .models import Payment
from .forms import ChangeContractForm
from django.urls import reverse_lazy
#UpdateSubscription用
from django.views.decorators.csrf import csrf_exempt

# import requests
import stripe
# 有効期限の保存
from datetime import datetime, timezone, time
import pytz
from dateutil.relativedelta import relativedelta

# ログインのデコレータ
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
import re

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

from django.db.models import Q


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
        not_paymented = Contract.objects.filter(company=current_user.company, payment__is_paymented=False)
        context["not_paymented"] = not_paymented
        #STRIPEのパブリックキーをテンプレートへ渡す
        context["stripe_public_key"] = settings.STRIPE_PUBLISHABLE_KEY
        url_name = self.request.resolver_match.url_name

        context["url_name"] = url_name

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
カード情報
"""
class CardInfo(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'payment/card_info.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY

        user = self.request.user
        company = Company.objects.get(pk=user.company_id)
        stripe_obj = Stripe.objects.filter(company=company).first()


        if stripe_obj:

            # 顧客情報の取得
            stripe_customer = stripe.Customer.retrieve(stripe_obj.stripe_cus_id)

            # カード情報の取得
            card_list = stripe.Customer.list_payment_methods(
            customer=stripe_customer.id,# CustomerオブジェクトID
            type="card",
            )

            # カード情報から有効期限、ブランド、下4桁を取得
            context["card_list"] = card_list
            context["company"] = company
            # SetupIntentオブジェクト生成
            setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer.id,# 生成したCustomerのIDを指定
            payment_method_types=["card"],# 支払い方法→今回はクレジットカード（"card"）
            )
            
            # 作成したSetupIntentからclient_secretを取得する→テンプレートへ渡す
            context["client_secret"] = setup_intent.client_secret
            print('ここまで終了CradInfo')
        else:
            #会社名作成
            if company.pic_corp_class == "1":
                if company.pic_legal_personality == '99' or company.pic_legal_personality == '':
                    company_name = company.pic_company_name
                else:
                    if company.pic_legal_person_posi == '1':
                        company_name = '{} {}'.format(company.get_pic_legal_personality_display(), company.pic_company_name)
                    else:
                        company_name = '{} {}'.format(company.pic_company_name, company.get_pic_legal_personality_display())

            else:
                company_name = company.pic_company_name


            # Customerオブジェクト生成
            stripe_customer = stripe.Customer.create(
                name= user.company_id,
                preferred_locales = ['ja'],
                description = company_name
            )
            # SetupIntentオブジェクト生成
            setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer.id,# 生成したCustomerのIDを指定
            payment_method_types=["card"],# 支払い方法→今回はクレジットカード（"card"）
            )
            
            # 作成したSetupIntentからclient_secretを取得する→テンプレートへ渡す
            context["client_secret"] = setup_intent.client_secret

            #顧客IDをユーザーに登録
            stripe_obj,created = Stripe.objects.get_or_create(company=user.company)
            stripe_obj.stripe_cus_id = stripe_customer.id
            stripe_obj.save()


        return context


"""
カードの登録
"""
class CardCreate(LoginRequiredMixin, View, CommonView):
    login_url = '/login/'

    def post(self, request):
        """
        カードの作成(Stripe側で顧客情報の作成)
        """
        # トークンの取得
        stripe_token = request.POST.get("token_id")
        
        user = self.request.user
        company = user.company
        stripe_customer_id = company.stripe.stripe_cus_id

        stripe.api_key = settings.STRIPE_API_KEY

        new_token = stripe.Token.retrieve(
            stripe_token,
        )

        #対象のカード会社をジャッジ
        if new_token['card']['brand'] == 'Visa' or new_token['card']['brand'] == 'MasterCard' or new_token['card']['brand'] == 'American Express':
            # クレジットカードの登録
            stripe_source = stripe.Customer.create_source(
                stripe_customer_id,
                source=stripe_token,
            )
            company.stripe.stripe_card_id = stripe_source['id']
            company.stripe.save()
            messages.success(request, "クレジットカードを登録しました。")
            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "クレジットカードを登録しました",
                                })
        else:
            print('すすんだ・・・・・・・・',stripe_customer_id)
            stripe.Customer.delete(stripe_customer_id)
            company.stripe.delete()
            # print('顧客消去')
            messages.error(request, "こちらのカード会社はご利用いただけません。")
            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ng",
                                "message": "こちらのカード会社はご利用いただけません。",
                                })

        # # クレジットカードの登録
        # stripe_source = stripe.Customer.create_source(
        # stripe_customer_id,
        # source=stripe_token,
        # )

        

"""
カードの更新
"""
class CardUpdate(LoginRequiredMixin, View, CommonView):
    login_url = '/login/'

    def post(self, request):

        """
        カードの更新（既存を削除して新規登録）
        """
        # トークンの取得
        stripe_token = request.POST.get("token_id")
        
        user = self.request.user
        company = user.company

        stripe_customer_id = company.stripe.stripe_cus_id
        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY


        new_token = stripe.Token.retrieve(
            stripe_token,
        )

        #対象のカード会社をジャッジ
        if new_token['card']['brand'] == 'Visa' or new_token['card']['brand'] == 'MasterCard' or new_token['card']['brand'] == 'American Express':
            stripe_cus_modify = stripe.Customer.modify(
                stripe_customer_id,
                source=stripe_token,
            )
            company.stripe.stripe_card_id = stripe_cus_modify['default_source']
            company.stripe.save()
            messages.success(request, "クレジットカードを更新しました。")
            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "クレジットカードを更新しました",
                                })
        else:
            messages.error(request, "こちらのカード会社はご利用いただけません。")
            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ng",
                                "message": "こちらのカード会社はご利用いただけません。",
                                })

        # # 既存カードの取得
        # stripe_cus_modify = stripe.Customer.modify(
        #     stripe_customer_id,
        #     source=stripe_token,
        # )


        # company.stripe.stripe_card_id = stripe_cus_modify['default_source']
        # company.stripe.save()

        # messages.success(request, "クレジットカードを更新しました。")


        # メッセージを生成してJSONで返す
        # return JsonResponse({"status": "ok",
        #                     "message": "クレジットカードを更新しました",
        #                     })

"""
戻るボタンの処理
"""
#★部分は遷移するURLでPKなどを指定している場合に、設定する方法です。
class PaymentReturnView(View):
    def get(self, request, *args, **kwargs):
        print('もどるしょり',self.request.session)
        # 不正な遷移をチェック
        if not 'page_num' in self.request.session:
            raise PermissionDenied
        cont = self.request.session['old_id']

        print('こんと',cont)
        
        # return HttpResponseRedirect(reverse('payment:change_contract_1'))
        return HttpResponseRedirect(reverse('payment:change_contract_1', kwargs={'pk': cont}))


"""
戻るボタンの処理
"""
#★部分は遷移するURLでPKなどを指定している場合に、設定する方法です。
class ContractReturnView(View):
    def get(self, request, *args, **kwargs):
        # 不正な遷移をチェック
        if not 'page_num' in self.request.session:
            raise PermissionDenied
        page_num = self.request.session['page_num']

        if 'contract_update_change1' in self.request.session:
            
            est = self.request.session['contract_update_change1']

            if page_num == 3:
                print('もどるしょり２')
                self.request.session['page_num'] = 2

                return HttpResponseRedirect(reverse('contracts:cont_update_change_step1_2'))
        if 'contract_update_step1' in self.request.session:
            
            est = self.request.session['contract_update_step1']

            if page_num == 2:
                self.request.session['page_num'] = 1
                contract_id = self.request.session['contract_id']

                return HttpResponseRedirect(reverse('contracts:cont_update_nochange_step1', kwargs={'pk': contract_id}))

from django.urls import resolve
"""
キャンセル処理
"""
class ContractCancelView(LoginRequiredMixin, View):
    login_url = '/login/'

    def get(self, request, *args, **kwargs):

        # セッションに「estimate」があれば、取得した行を削除
        if 'estimate' in request.session:
            estimate = Estimates.objects.get(pk = request.session['estimate'])
            estimate.delete()
        if 'contract_update_step1' in request.session:
            estimate = Estimates.objects.get(pk = request.session['contract_update_step1'])
            estimate.delete()
        if 'contract_update_change1' in request.session:
            estimate = Estimates.objects.get(pk = request.session['contract_update_change1'])
            estimate.delete()


        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]


        return HttpResponseRedirect(reverse('contracts:contract'))



"""
支払い(クレジット)
"""
class Checkout(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/checkout.html'
    context_object_name = 'estimate'
    login_url = '/login/'


    def get_context_data(self, **kwargs):
        print('card@__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@')
        user = self.request.user
        context = super().get_context_data(**kwargs)
        estimate = Estimates.objects.get(pk = self.kwargs['pk'])
        #差額の値がある場合はプラン変更用決済処理へ
        if estimate.difference:
            contract = Contract.objects.get(service=estimate.service,status='2',company=user.company)
            context['contract'] = contract

        context['estimate'] = estimate

        return context


    def dispatch(self, request, *args, **kwargs):
        
        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company).first()

        if not stripe_obj:
            messages.error(request, "クレジットカードが未登録です。登録してください。")
            return redirect('payment:card_info')
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, pk):
        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company_id).first()
        autocheckout = request.POST.get('autocheckout')
        is_start_now = request.POST.get('is_start_now')

        # Stripeのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY

        # Stripeの顧客IDを取得
        customer_id = user.company.stripe.stripe_cus_id

        # 見積書に記載されたプランのStripeIDを取得
        estimate = Estimates.objects.select_related().get(pk=pk)

        stripe_plan_id = estimate.plan.stripe_plan_id

        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=user)

        # 契約テーブル作成
        #プラン変更
        if estimate.difference:
            old_contract = Contract.objects.get(service=estimate.service,status='2',company=user.company)
            new_start_date = old_contract.contract_end_date + relativedelta(days=1,hour=0,minute=0,second=0,microsecond=0)
            contract = Contract.objects.create(user=user,service=estimate.service, company=user.company)
            today = datetime.now()
            #支払い手段の情報を取得
            cus_card = stripe.Customer.list_payment_methods(
                customer_id,
                type="card",
            )
            #通常のサブスクリプション
            if old_contract.payment.stripe_plan:
                subscription = stripe.Subscription.retrieve(old_contract.payment.stripe_plan)
            if not old_contract.payment.stripe_plan:
                #予約されたサブスクリプション
                sched_subscription = stripe.SubscriptionSchedule.retrieve(old_contract.payment.stripe_sched_plan)
                print('予約されたサブスクリプション',sched_subscription)
        #通常契約
        else:
            contract, created = Contract.objects.get_or_create(user=self.request.user, service=estimate.service, company=user.company)
            #支払日を設定
            trial_day = estimate.start_day - relativedelta(days=1)

        #Subscription.createに渡す
        if estimate.unit_total >= 30000:
            item_set = [{"price":estimate.plan.stripe_price_id}]
        else:
            item_set = [{"price":estimate.plan.stripe_price_id},{"price":"price_1MUgVyI8iZ48PSn6ctfLVE2H"}]

        option_list = []

        if estimate.option1 and not estimate.option1.stripe_plan_id == 'pln':
            option_1 = {'price':estimate.option1.stripe_price_id}
            item_set.append(option_1)
            option_list.append(estimate.option1)
        if estimate.option2 and not estimate.option2.stripe_plan_id == 'pln':
            option_2 = {'price':estimate.option2.stripe_price_id}
            item_set.append(option_2)
            option_list.append(estimate.option2)
        if estimate.option3 and not estimate.option3.stripe_plan_id == 'pln':
            option_3 = {'price':estimate.option3.stripe_price_id}
            item_set.append(option_3)
            option_list.append(estimate.option3)
        if estimate.option4 and not estimate.option4.stripe_plan_id == 'pln':
            option_4 = {'price':estimate.option4.stripe_price_id}
            item_set.append(option_4)
            option_list.append(estimate.option4)
        if estimate.option5 and not estimate.option5.stripe_plan_id == 'pln':
            option_5 = {'price':estimate.option5.stripe_price_id}
            item_set.append(option_5)
            option_list.append(estimate.option5)

        print('オプションリスト作成',item_set)

       

        try:

            """
            Stripe側処理
            """
            if estimate.difference > 0:
                # if estimate.discount:
                #     print('割引あり')
                #     #クーポン保存
                #     contract.discount = estimate.discount

                #     stripe.PaymentIntent.create(
                #         amount=estimate.difference,# 支払金額
                #         currency='jpy',# 利用通貨
                #         customer=customer_id,# CustomerオブジェクトID
                #         payment_method=cus_card["data"][0]["id"],# 支払いに使用するクレジットカード
                #         off_session=True,# サーバーのみで処理
                #         confirm=True,# PaymentIntentの作成と確認を同時に行う
                #         description=user.id,
                #     )

                #     if 'sched_subscription' in locals() and 'subscription' in locals():
                #         #現在の支払い済みのサブスクリプションを期間終了後にキャンセルさせる
                #         stripe.Subscription.modify(
                #             subscription.id,
                #             cancel_at_period_end=True
                #         )
                #     elif 'subscription' in locals():
                #         #現在の支払い済みのサブスクリプションを期間終了後にキャンセルさせる
                #         stripe.Subscription.modify(
                #             subscription.id,
                #             cancel_at_period_end=True
                #         )
                #     elif 'sched_subscription' in locals():
                #         stripe.SubscriptionSchedule.cancel(
                #             sched_subscription.id,
                #         )   

                #     #次年度分のサブスクリプション登録
                #     stripe_plan = stripe.SubscriptionSchedule.create(
                #         customer=customer_id,
                #         start_date=new_start_date,
                #         end_behavior='release',
                #         phases=[
                #             {
                #             'items': item_set,
                #             'iterations': 12,
                #             'default_tax_rates' : ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                #             },
                #         ],
                #     )

                
                print('プラン変更決済',estimate.difference)

                stripe.PaymentIntent.create(
                    amount=estimate.difference,# 支払金額
                    currency='jpy',# 利用通貨
                    customer=customer_id,# CustomerオブジェクトID
                    payment_method=cus_card["data"][0]["id"],# 支払いに使用するクレジットカード
                    off_session=True,# 支払いの実行時に顧客が決済フローに存在しないことを示す
                    confirm=True,# PaymentIntentの作成と確認を同時に行う
                    description=user.id,
                )

                if old_contract.payment.stripe_plan:
                    #現在の支払い済みのサブスクリプションを期間終了後にキャンセルさせる
                    stripe.Subscription.modify(
                        subscription.id,
                        cancel_at_period_end=True
                    )
                else:
                    stripe.SubscriptionSchedule.cancel(
                        sched_subscription.id,
                    )   

                #次年度分のサブスクリプション登録
                stripe_plan = stripe.SubscriptionSchedule.create(
                    customer=customer_id,
                    start_date=new_start_date,
                    end_behavior='release',
                    phases=[
                        {
                        'items': item_set,
                        'iterations': 12,
                        'default_tax_rates' : ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        },
                    ],
                )
                # 作成したStripe定期課金スケジュールのIDを保存
                payment.stripe_sched_plan = stripe_plan.id
                # 支払いフラグをON
                payment.is_paymented = True

                # 支払い日を登録
                payment.created_date = today
                # 見積りフラグをオフ
                estimate.is_change = False
                # 自動更新フラグをON
                contract.is_autocheckout = old_contract.is_autocheckout
                # 契約開始・終了日付をセット
                contract.contract_start_date = estimate.start_day
                contract.contract_end_date = estimate.end_day

                contract.pay_start_date = today
                contract.pay_end_date = today

                # 見積りのオプションを契約テーブルに上書き保存
                if estimate.option1:
                    contract.option1 = estimate.option1
                if estimate.option2:
                    contract.option2 = estimate.option2
                if estimate.option3:
                    contract.option3 = estimate.option3
                if estimate.option4:
                    contract.option4 = estimate.option4
                if estimate.option5:
                    contract.option5 = estimate.option5

                #旧契約を解約済みにする
                old_contract.status = "4"
                #旧契約の契約終了日を変更
                old_contract.contract_end_date = estimate.start_day
                old_contract.is_updating = False
                old_contract.save()
                
            else:
                #日付が本日の場合
                st = datetime.combine(estimate.start_day, time())

                if st > trial_day.replace(tz=None):
                
                    print('今日の日付！！！')
                    if option_list:
                        if estimate.discount:

                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(
                                customer = customer_id,
                                items = item_set,
                                default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                                coupon = estimate.discount.coupon_id,
                                description = user.id,
                            )
                            print('定期課金の作成')

                            contract.discount = estimate.discount
                        else:
                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(
                                customer = customer_id,
                                items = item_set,
                                default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                                description = user.id,
                            )
                            print('定期課金の作成')

                        # 見積りのオプションを契約テーブルに上書き保存
                        if estimate.option1:
                            contract.option1 = estimate.option1
                        if estimate.option2:
                            contract.option2 = estimate.option2
                        if estimate.option3:
                            contract.option3 = estimate.option3
                        if estimate.option4:
                            contract.option4 = estimate.option4
                        if estimate.option5:
                            contract.option5 = estimate.option5
                    
                    else:

                        if estimate.discount:

                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(

                            customer = customer_id,
                            items = [
                                {"price":estimate.plan.stripe_price_id},
                            ],
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            coupon = estimate.discount.coupon_id,
                            description = user.id,
                            )
                            print('プランのみ定期課金の作成')
                            contract.discount = estimate.discount

                        else:
                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(
                            customer = customer_id,
                            items = [
                                {"price":estimate.plan.stripe_price_id},
                            ],
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            description = user.id,
                            )
                            print('プランのみ定期課金の作成')

                #開始日が未来
                else:

                    if option_list:
                        if estimate.discount:

                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(
                                customer = customer_id,
                                items = item_set,
                                default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                                coupon = estimate.discount.coupon_id,
                                description = user.id,
                                # 課金処理を前契約の完了日とするためトライアル日を設定
                                trial_end = trial_day
                            )
                            print('定期課金の作成')

                            contract.discount = estimate.discount
                        else:
                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(
                                customer = customer_id,
                                items = item_set,
                                default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                                description = user.id,
                                # 課金処理を前契約の完了日とするためトライアル日を設定
                                trial_end = trial_day
                            )
                            print('定期課金の作成')

                        # 見積りのオプションを契約テーブルに上書き保存
                        if estimate.option1:
                            contract.option1 = estimate.option1
                        if estimate.option2:
                            contract.option2 = estimate.option2
                        if estimate.option3:
                            contract.option3 = estimate.option3
                        if estimate.option4:
                            contract.option4 = estimate.option4
                        if estimate.option5:
                            contract.option5 = estimate.option5
                
                    else:

                        if estimate.discount:

                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(

                            customer = customer_id,
                            items = [
                                {"price":estimate.plan.stripe_price_id},
                            ],
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            coupon = estimate.discount.coupon_id,
                            description = user.id,
                            # 課金処理を前契約の完了日とするためトライアル日を設定
                            trial_end = trial_day
                            )
                            print('プランのみ定期課金の作成')
                            contract.discount = estimate.discount

                        else:
                            # 定期課金の作成
                            stripe_plan = stripe.Subscription.create(
                            customer = customer_id,
                            items = [
                                {"price":estimate.plan.stripe_price_id},
                            ],
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            description = user.id,
                            # 課金処理を前契約の完了日とするためトライアル日を設定
                            trial_end = trial_day
                            )
                            print('プランのみ定期課金の作成')

                # 作成したStripe定期課金のIDを保存
                payment.stripe_plan = stripe_plan.id
                print('作成したStripe定期課金のIDを保存')
                # 自動更新OFFの場合は、その場でキャンセルする
                if autocheckout ==  "False":
                    stripe_plan.cancel()

                # 定期課金が作成された
                if stripe_plan.created:

                    # 支払いフラグをON
                    payment.is_paymented = True

                    # 支払い日を登録
                    payment.created_date = datetime.fromtimestamp(stripe_plan.created)

                # 自動更新フラグをON
                if autocheckout ==  "True":
                    contract.is_autocheckout = True
                else:
                    contract.is_autocheckout = False

                # 契約日付
                # すぐに開始の場合は支払い日付をセット
                if is_start_now == None:
                    contract.contract_start_date = estimate.start_day
                    contract.contract_end_date = estimate.end_day
                else:
                    contract.contract_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                    contract.contract_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)

                # 支払い日付
                contract.pay_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                contract.pay_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)


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
            contract.is_updating = False
            # 保存
            contract.save()
            payment.save()

            # 見積り使用フラグをON
            estimate.is_use = True
            # 契約フラグをON
            estimate.is_signed = True
            estimate.is_updating = False

            estimate.save()

        except stripe.error.CardError as e:
            context = {
                "err_message":"このカードはご利用になれません。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.InvalidRequestError as e:
            context = {
                "err_message":"入力いただいた情報に誤りがあります。今一度ご確認をお願いします。解決できない場合はエラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.AuthenticationError as e:
            context = {
                "err_message":"システムエラーが発生しております。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.APIConnectionError as e:
            context = {
                "err_message":"お客様のサーバーと Stripe の間でネットワークの問題が発生しました。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)

        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract'] = contract.id
        
        return redirect('payment:checkout_done')


"""
支払い(クレジット) 申し込みからの支払い
"""
class CheckoutFromOffer(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/checkout_from_offer.html'
    context_object_name = 'estimate'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company_id).first()

        if not stripe_obj:
            messages.error(request, "クレジットカードが未登録です。登録してください。")
            return redirect('payment:card_info')
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, pk):
        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company_id).first()
        autocheckout = request.POST.get('autocheckout')
        is_start_now = request.POST.get('is_start_now')

        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY

        # STRIPEの顧客IDを取得
        customer_id = user.company.stripe.stripe_cus_id

        # 見積書に記載されたプランのPAY.JPIDを取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        stripe_plan_id = estimate.plan.stripe_plan_id

        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=user)

        # 契約DBへ本契約の有効期限を保存
        contract, created = Contract.objects.get_or_create(user=request.user, service=estimate.service, company=request.user.company)

        #Subscription.createに渡す
        if estimate.unit_total >= 30000:
            item_set = [{"price":estimate.plan.stripe_price_id}]
        else:
            item_set = [{"price":estimate.plan.stripe_price_id},{"price":"price_1MUgVyI8iZ48PSn6ctfLVE2H"}]
        
        #支払日を設定
        trial_day = estimate.end_day - relativedelta(years=1)
        # trial_day = estimate.end_day - relativedelta(years=1,days=-1,hour=23,minute=59,second=59,microsecond=999999)
        print('＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝すたーとでい',type(trial_day))
        option_list = []

        if estimate.option1 and not estimate.option1.stripe_plan_id == 'pln':
            option_1 = {'price':estimate.option1.stripe_price_id}
            item_set.append(option_1)
            option_list.append(estimate.option1)
        if estimate.option2 and not estimate.option2.stripe_plan_id == 'pln':
            option_2 = {'price':estimate.option2.stripe_price_id}
            item_set.append(option_2)
            option_list.append(estimate.option2)
        if estimate.option3 and not estimate.option3.stripe_plan_id == 'pln':
            option_3 = {'price':estimate.option3.stripe_price_id}
            item_set.append(option_3)
            option_list.append(estimate.option3)
        if estimate.option4 and not estimate.option4.stripe_plan_id == 'pln':
            option_4 = {'price':estimate.option4.stripe_price_id}
            item_set.append(option_4)
            option_list.append(estimate.option4)
        if estimate.option5 and not estimate.option5.stripe_plan_id == 'pln':
            option_5 = {'price':estimate.option5.stripe_price_id}
            item_set.append(option_5)
            option_list.append(estimate.option5)

        try:

            """
            Stripe側処理
            """
            #日付が本日の場合
            st = datetime.combine(estimate.start_day, time())

            if st > trial_day.replace(tzinfo=None):
                print('今日の日付！！！')
                if option_list:
                    if estimate.discount:
                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                            customer = customer_id,
                            items = item_set,
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            coupon = estimate.discount.coupon_id,
                            description = user.id,
                        )
                        contract.discount = estimate.discount

                    else:
                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                            customer = customer_id,
                            items = item_set,
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            description = user.id,
                        )
                        print('定期課金の作成')
                    
                    # 見積りのオプションを契約テーブルに上書き保存
                    if estimate.option1:
                        contract.option1 = estimate.option1
                    if estimate.option2:
                        contract.option2 = estimate.option2
                    if estimate.option3:
                        contract.option3 = estimate.option3
                    if estimate.option4:
                        contract.option4 = estimate.option4
                    if estimate.option5:
                        contract.option5 = estimate.option5

                else:
                    
                    if estimate.discount:

                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                        customer = customer_id,
                        items = [
                            {"price":estimate.plan.stripe_price_id},
                        ],
                        default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        coupon = estimate.discount.coupon_id,
                        description = user.id,
                        )
                        contract.discount = estimate.discount

                        print('プランのみ定期課金の作成')

                    else:
                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                        customer = customer_id,
                        items = [
                            {"price":estimate.plan.stripe_price_id},
                        ],
                        default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        description = user.id,
                        )

            #開始日が未来
            else:

                if option_list:
                    if estimate.discount:
                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                            customer = customer_id,
                            items = item_set,
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            coupon = estimate.discount.coupon_id,
                            description = user.id,
                            # 課金処理を前契約の完了日とするためトライアル日を設定
                            trial_end = trial_day
                        )
                        contract.discount = estimate.discount

                    else:
                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                            customer = customer_id,
                            items = item_set,
                            default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            description = user.id,
                            # 課金処理を前契約の完了日とするためトライアル日を設定
                            trial_end = trial_day
                        )
                        print('定期課金の作成')
                    
                    # 見積りのオプションを契約テーブルに上書き保存
                    if estimate.option1:
                        contract.option1 = estimate.option1
                    if estimate.option2:
                        contract.option2 = estimate.option2
                    if estimate.option3:
                        contract.option3 = estimate.option3
                    if estimate.option4:
                        contract.option4 = estimate.option4
                    if estimate.option5:
                        contract.option5 = estimate.option5

                else:
                   
                    if estimate.discount:

                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                        customer = customer_id,
                        items = [
                            {"price":estimate.plan.stripe_price_id},
                        ],
                        default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        coupon = estimate.discount.coupon_id,
                        description = user.id,
                        # 課金処理を前契約の完了日とするためトライアル日を設定
                        trial_end = trial_day
                        )
                        contract.discount = estimate.discount

                        print('プランのみ定期課金の作成')

                    else:
                        # 定期課金の作成
                        stripe_plan = stripe.Subscription.create(
                        customer = customer_id,
                        items = [
                            {"price":estimate.plan.stripe_price_id},
                        ],
                        default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        description = user.id,
                        # 課金処理を前契約の完了日とするためトライアル日を設定
                        trial_end = trial_day
                        )

            # 作成したSTRIPE定期課金のIDを保存
            payment.stripe_plan = stripe_plan.id

            # 自動更新OFFの場合は、その場でキャンセルする
            if autocheckout ==  "False":
                # stripe_plan.cancel()
                stripe.Subscription.modify(
                    stripe_plan.id,
                    cancel_at_period_end=True
                )

            # 定期課金が作成された
            if stripe_plan.created:

                # 支払いフラグをON
                payment.is_paymented = True

                # 支払い日を登録
                payment.created_date = datetime.fromtimestamp(stripe_plan.created)

                # 契約日付
                # すぐに開始の場合は支払い日付をセット
                if is_start_now == None:
                    contract.contract_start_date = estimate.start_day
                    contract.contract_end_date = estimate.end_day
                else:
                    contract.contract_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                    contract.contract_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)

                # 支払い日付
                contract.pay_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                contract.pay_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)


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

                contract.is_updating = False
                # 保存
                contract.save()
                payment.save()


                # 見積り使用フラグをON
                estimate.is_use = True
                # 契約フラグをON
                estimate.is_signed = True
                
                estimate.is_updating = False
                
                estimate.save()

        except stripe.error.CardError as e:
            context = {
                "err_message":"このカードはご利用になれません。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.InvalidRequestError as e:
            context = {
                "err_message":"入力いただいた情報に誤りがあります。今一度ご確認をお願いします。解決できない場合はエラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.AuthenticationError as e:
            context = {
                "err_message":"システムエラーが発生しております。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.APIConnectionError as e:
            context = {
                "err_message":"APIConnectionErroによりエラーが発生しています。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name,
                "err_message_app" : self.request.resolver_match.app_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract'] = contract.id
        
        return redirect('payment:checkout_from_offer_done')



"""
支払い(クレジット) 申し込みからの更新
"""
class UpdateFromOffer(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/update_contract/checkout_from_offer.html'
    context_object_name = 'estimate'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):

        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company).first()

        if not stripe_obj:
            messages.error(request, "クレジットカードが未登録です。登録してください。")
            return redirect('payment:card_info')
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, pk):
        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company_id).first()
        autocheckout = request.POST.get('autocheckout')
        is_start_now = request.POST.get('is_start_now')

        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY

        # STRIPEの顧客IDを取得
        customer_id = user.company.stripe.stripe_cus_id

        # 見積書に記載されたプランのStripeIDを取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        stripe_plan_id = estimate.plan.stripe_plan_id

        # 契約DBへ本契約の有効期限を保存
        contract = Contract.objects.get(company=user.company, service=estimate.service)

        # 支払い管理レコードを作成
        payment = Payment.objects.get(user=user)

        # 契約終了日
        contract_end_date = contract.contract_end_date

        unix_contract_end_date = contract_end_date.timestamp()

        print("終了日3", unix_contract_end_date)

        #Subscription.createに渡す
        if estimate.unit_total >= 30000:
            item_set = [{"price":estimate.plan.stripe_price_id}]
        else:
            item_set = [{"price":estimate.plan.stripe_price_id},{"price":"price_1MUgVyI8iZ48PSn6ctfLVE2H"}]

        
        option_list = []

        if estimate.option1 and not estimate.option1.stripe_plan_id == 'pln':
            option_1 = {'price':estimate.option1.stripe_price_id}
            item_set.append(option_1)
            option_list.append(estimate.option1)
        if estimate.option2 and not estimate.option2.stripe_plan_id == 'pln':
            option_2 = {'price':estimate.option2.stripe_price_id}
            item_set.append(option_2)
            option_list.append(estimate.option2)
        if estimate.option3 and not estimate.option3.stripe_plan_id == 'pln':
            option_3 = {'price':estimate.option3.stripe_price_id}
            item_set.append(option_3)
            option_list.append(estimate.option3)
        if estimate.option4 and not estimate.option4.stripe_plan_id == 'pln':
            option_4 = {'price':estimate.option4.stripe_price_id}
            item_set.append(option_4)
            option_list.append(estimate.option4)
        if estimate.option5 and not estimate.option5.stripe_plan_id == 'pln':
            option_5 = {'price':estimate.option5.stripe_price_id}
            item_set.append(option_5)
            option_list.append(estimate.option5)

        try:

            """
            stripe側処理
            """

            # 既存定期課金の削除
            subscription = stripe.Subscription.retrieve(payment.stripe_plan)
            if subscription:
                subscription.delete()

            if option_list:
                if estimate.discount:

                    # 定期課金の作成
                    stripe_plan = stripe.Subscription.create(
                        customer = customer_id,
                        items = item_set,
                        default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        coupon = estimate.discount.coupon_id,
                        description = user.id,
                        # 課金処理を前契約の完了日とするためトライアル日を設定
                        trial_end = int(unix_contract_end_date)
                    )
                    print('定期課金の作成')

                    contract.discount = estimate.discount
                else:
                    print('オプションありの契約更新へ')
                    # 定期課金の作成
                    stripe_plan = stripe.Subscription.create(
                        customer = customer_id,
                        items = item_set,
                        default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        description = user.id,
                        # 課金処理を前契約の完了日とするためトライアル日を設定
                        trial_end = int(unix_contract_end_date)
                    )
                    print('定期課金の作成')

                # 見積りのオプションを契約テーブルに上書き保存
                if estimate.option1:
                    contract.option1 = estimate.option1
                if estimate.option2:
                    contract.option2 = estimate.option2
                if estimate.option3:
                    contract.option3 = estimate.option3
                if estimate.option4:
                    contract.option4 = estimate.option4
                if estimate.option5:
                    contract.option5 = estimate.option5
            
            else:
                # 契約テーブル上のオプションをリセット
                contract.option1.clear()
                contract.option2.clear()
                contract.option3.clear()
                contract.option4.clear()
                contract.option5.clear()


                if estimate.discount:

                    # 定期課金の作成
                    stripe_plan = stripe.Subscription.create(

                    customer = customer_id,
                    items = [
                        {"price":estimate.plan.stripe_price_id},
                    ],
                    default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                    coupon = estimate.discount.coupon_id,
                    description = user.id,
                    # 課金処理を前契約の完了日とするためトライアル日を設定
                    trial_end = int(unix_contract_end_date)
                    )
                    contract.discount = estimate.discount

                else:
                    # 定期課金の作成
                    stripe_plan = stripe.Subscription.create(
                    customer = customer_id,
                    items = [
                        {"price":estimate.plan.stripe_price_id},
                    ],
                    default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                    description = user.id,
                    # 課金処理を前契約の完了日とするためトライアル日を設定
                    trial_end = int(unix_contract_end_date)
                    )
                
            # 作成したSTRIPE定期課金のIDを保存
            payment.stripe_plan = stripe_plan.id

            # 自動更新OFFの場合は、その場でキャンセルする
            if autocheckout ==  "False":
                stripe_plan.cancel()

            # 定期課金が作成された
            if stripe_plan.created:

                # 支払いフラグをON
                payment.is_paymented = True

                # 支払い回数をカウントアップ
                payment.pay_count = payment.pay_count + 1

                # 支払い日を登録
                payment.created_date = datetime.fromtimestamp(stripe_plan.created)

                # 契約日付
                # すぐに開始の場合は支払い日付をセット
                if is_start_now == None:
                    contract.contract_start_date = estimate.start_day
                    contract.contract_end_date = estimate.end_day
                else:
                    contract.contract_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                    contract.contract_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)

                # 支払い日付
                contract.pay_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                contract.pay_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)


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

                contract.is_updating = False
                # 保存
                contract.save()
                payment.save()


                # 見積り使用フラグをON
                estimate.is_use = True
                # 契約フラグをON
                estimate.is_signed = True
                
                estimate.is_updating = False
                
                estimate.save()

        except stripe.error.CardError as e:
            context = {
                "err_message":"このカードはご利用になれません。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.InvalidRequestError as e:
            context = {
                "err_message":"入力いただいた情報に誤りがあります。今一度ご確認をお願いします。解決できない場合はエラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.AuthenticationError as e:
            context = {
                "err_message":"システムエラーが発生しております。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name

            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.APIConnectionError as e:
            context = {
                "err_message":"APIConnectionErroによりエラーが発生しています。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name

            }
            return  render(request, 'payment/checkout_error.html', context)


        messages.success(request, "お申し込みが完了しました。")
         # セッションがあれば削除
        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return redirect('contract:estimate')



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
        contract, created = Contract.objects.get_or_create(user=request.user, service=estimate.service, company=request.user.company)

        try:

            # 試用プランの削除
            contract.plan = None

            # 紐づく支払いを契約テーブルに保存
            contract.payment=payment

            # 見積りのプランを契約テーブルに保存
            contract.plan = estimate.plan

            # 見積りのオプションを契約テーブルに上書き保存
            if estimate.option1:
                contract.option1 = estimate.option1
            if estimate.option2:
                contract.option2 = estimate.option2
            if estimate.option3:
                contract.option3 = estimate.option3
            if estimate.option4:
                contract.option4 = estimate.option4
            if estimate.option5:
                contract.option5 = estimate.option5

            #クーポンを保存
            if estimate.discount:
                contract.discount = estimate.discount

            # ステータスの変更
            contract.status = "2" #本番

            # 銀行振込なので自動更新もNull
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

            # 契約開始・終了日付をセット
            contract.contract_start_date = estimate.start_day
            contract.contract_end_date = estimate.end_day

            # 支払いフラグをOFF(入金未確認)
            payment.is_paymented = False

            # 見積りの支払い方法を支払いテーブルに保存
            payment.method_payment = estimate.method_payment

            contract.is_updating = False
            # 保存
            contract.save()
            payment.save()

            # 見積り使用フラグをON
            estimate.is_use = True
            # 契約フラグをON
            estimate.is_signed = True
            
            estimate.is_updating =False
            estimate.save()

        except Exception as e:
            context = {
                "err_message":"問題が発生しました。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)
        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract'] = contract.id
        
        return redirect('payment:checkout_done')



"""
申込みからの支払い(銀行振込)
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
        contract, created = Contract.objects.get_or_create(user=request.user, service=estimate.service, company=request.user.company)

        try:

            # 試用プランの削除
            contract.plan = None

            # 紐づく支払いを契約テーブルに保存
            contract.payment=payment

            # 見積りのプランを契約テーブルに保存
            contract.plan = estimate.plan

            # 見積りのオプションを契約テーブルに上書き保存
            if estimate.option1:
                contract.option1 = estimate.option1
            if estimate.option2:
                contract.option2 = estimate.option2
            if estimate.option3:
                contract.option3 = estimate.option3
            if estimate.option4:
                contract.option4 = estimate.option4
            if estimate.option5:
                contract.option5 = estimate.option5

            # ステータスの変更
            contract.status = "2" #本番

            # 銀行振込なので自動更新もNull
            contract.is_autocheckout = False

            # 見積りIDを保存
            contract.estimate.add(estimate)

            # 請求書オプションを契約テーブルに保存
            contract.is_invoice_need = estimate.is_invoice_need

            #クーポンを契約テーブルに保存
            if estimate.discount:
                contract.discount = estimate.discount

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

            contract.is_updating =False
            # 保存
            contract.save()
            payment.save()

            # 見積り使用フラグをON
            estimate.is_use = True
            # 契約フラグをON
            estimate.is_signed = True
            
            estimate.is_updating =False
            
            estimate.save()

        except Exception as e:
            context = {
                "err_message":"問題が発生しました。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)
        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract'] = contract.id
        
        return redirect('payment:checkout_from_offer_done')


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

        #STRIPEのパブリックキーをテンプレートへ渡す
        context["pay_public_key"] = settings.STRIPE_PUBLISHABLE_KEY
        return context


    def post(self, request, pk):
        """手動支払いにチェックが入っている場合"""
        print("来年度分の手動支払い")
        # トークンの取得
        stripe_token = request.POST.get("stripe-token")
        print(stripe_token)

        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY

        # 見積書に記載された合計額を取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        total = estimate.total
        print("合計額", total)

        #　支払い
        try:
            charge = stripe.Charge.create(
                amount = total,
                source = stripe_token,
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

        except stripe.error.InvalidRequestError as e:
            context = {
                "err_message":"エラーが発生しました。運営に問い合わせてください。メッセージ：" + str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)
        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]
        return redirect('payment:checkout_done')


"""
支払い完了
"""
#申し込み完了
class CheckoutDone(LoginRequiredMixin, TemplateView, CommonView):
    model = Contract
    template_name = 'payment/checkout_done.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.filter(pk = self.request.session['contract']).first()
        print('こんとらくとのなかみ',contract)
        context['contract'] = contract
        return context

#ホームからの申し込み完了
class CheckoutFromOfferDone(LoginRequiredMixin, TemplateView, CommonView):
    model = Contract
    template_name = 'payment/checkout_from_offer_done.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.filter(pk = self.request.session['contract']).first()
        print('こんとらくとのなかみ',contract)
        context['contract'] = contract
        return context
    
    

"""
プラン・オプション変更
"""
# @method_decorator(login_required, name = 'dispatch')
class ChangeContract(LoginRequiredMixin, FormView, CommonView):
    model = Contract
    template_name = 'payment/change_contract/change_contract_1.html'
    form_class = ChangeContractForm
    login_url = '/login/'


    def get_initial(self):
        # initial={}
        # initial = super().get_initial()
        initial = super(ChangeContract, self).get_initial()
        if 'estimate' in self.request.session:
            est_obj = Estimates.objects.filter(pk = self.request.session['estimate']).first()
            if est_obj.plan:
                # initial={
                #     # 'plan': Plan.objects.filter(pk=est_obj.plan.id).first(),
                #     'plan': est_obj.plan,
                # }
                initial['plan'] = est_obj.plan
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
            print("bbbb")
            pass

            # 返す
        return initial
    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(ChangeContract, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        kwargs.update({'contract': self.kwargs['pk']})

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_id = self.kwargs['pk']
        contract = Contract.objects.get(pk=contract_id)
        service = Service.objects.get(pk=contract.service_id)
        contract.is_updating = True
        contract.save()
        context["contract"] = contract
        context["service"] = service
        # サービスに紐づくプランの数
        options_list = []
        options = Plan.objects.filter(service=service, is_option=True, is_trial=False,).distinct().values_list('category')
        for op  in options:
            for number in op:
                options_list.append(number)

        context["options_list"] = options_list
        return context

    def post(self, request, *args, **kwargs):
        
        print("selfselfselfselfself",self)
        print("requestrequest",request)
        form = self.get_form()

        if form.is_valid():
            print("validformをゲット")

            return self.form_valid(form)

        else:
            print("invalidformをゲット")

            return self.form_invalid(form)

    def form_valid(self, form):
        print("form_validだよ")
        user = self.request.user

        # 旧契約情報の取得
        old = Contract.objects.get(pk=self.kwargs['pk'])
        old_id = old.id
        # 旧契約の見積り取得
        old_estimate = old.estimate.all().first()

        # 新しい見積り作成
        if not 'estimate' in self.request.session:
            estimate = Estimates.objects.create(user=user,service=old_estimate.service)
        else:
            estimate = Estimates.objects.filter(pk = self.request.session['estimate']).first()

        # 変更後のプランIDを取得
        new_plan = form.cleaned_data['plan']
        print("新プラン", new_plan)
        estimate.plan = new_plan
        # 旧プランIDを取得
        old_plan = old.plan
        print("旧プラン", old.plan)

        option_price_list = []

        # オプションの新IDを取得
        new_option1 = form.cleaned_data['option1']
        if new_option1:
            estimate.option1 = new_option1
            option_price_list.append(estimate.option1.price)
        new_option2 = form.cleaned_data['option2']
        if new_option2:
            estimate.option2 = new_option2
            option_price_list.append(estimate.option2.price)
        new_option3 = form.cleaned_data['option3']
        if new_option3:
            estimate.option3 = new_option3
            option_price_list.append(estimate.option3.price)
        new_option4 = form.cleaned_data['option4']
        if new_option4:
            estimate.option4 = new_option4
            option_price_list.append(estimate.option4.price)
        new_option5 = form.cleaned_data['option5']
        if new_option5:
            estimate.option5 = new_option5
            option_price_list.append(estimate.option5.price)

        
        # オプションの旧IDを取得
        old_option1 = old.option1
        old_option2 = old.option2
        old_option3 = old.option3
        old_option4 = old.option4
        old_option5 = old.option5

        #新旧オプションリスト作成
        options_list = [[old_option1,new_option1],[old_option2,new_option2],[old_option3,new_option3],[old_option4,new_option4],[old_option5,new_option5]]
        print('おぷしょんりすとのなかみ＝＝＝',options_list)
        
        today = datetime.now()
        
        # 作成日を登録
        estimate.created_date = today
        
        #見積りに旧データコピー
        estimate.start_day = today
        estimate.end_day = old.contract_end_date
        estimate.is_invoice_need = old_estimate.is_invoice_need
        estimate.bill_address = old_estimate.bill_address
        estimate.method_payment = old_estimate.method_payment

        # 有効期限を生成(+1ヶ月)
        expiration_date = today + relativedelta(months=1,days=-1,hour=23,minute=59,second=59,microsecond=999999)
        estimate.expiration_date = expiration_date

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

        
        # if old_estimate.discount:
        #     estimate.discount = old_estimate.discount
        #     coupon_code = estimate.discount.coupon_code
        # else:
        #     coupon_code = None


        #プランとオプションの合計
        unit_total = sum(option_price_list) + estimate.plan.price
        estimate.unit_total = unit_total

        #プランとオプションの月額
        estimate.unit_minor_total = unit_total / 12

        # 小計(税抜)
        if estimate.method_payment.id == 1:
           
            if estimate.unit_total >= 30000: #割引あり
                minor_total = estimate.unit_total - estimate.method_payment.payment_discount
            else:#割引なし
                minor_total = estimate.unit_total
        else:
            minor_total = estimate.unit_total
        # if estimate.method_payment.id == 1:
        #     if coupon_code and estimate.unit_total >= 30000: #クーポンあり、割引あり
        #         minor_total = estimate.unit_total - estimate.method_payment.payment_discount - estimate.discount.discount_rate
        #     elif estimate.unit_total >= 30000: #クーポンなし、割引あり
        #         minor_total = estimate.unit_total - estimate.method_payment.payment_discount
        #     elif coupon_code: # クーポンあり、割引なし
        #         minor_total = estimate.unit_total - estimate.discount.discount_rate
        #     else:# クーポンなし、割引なし
        #         minor_total = estimate.unit_total
        # else:
        #     if coupon_code: # クーポンあり
        #         minor_total = estimate.unit_total - estimate.discount.discount_rate
        #     else:# クーポンなし
        #         minor_total = estimate.unit_total


        estimate.minor_total = minor_total

        # 消費税
        tax  = minor_total * settings.TAX
        estimate.tax = tax

        # 合計
        total = minor_total + tax
        estimate.total = total
        #仮作成フラグをオフ
        estimate.temp_check = False
        #プラン変更用フラグをTrueに
        estimate.is_change = True


        # 契約中の終了期間を取得
        old_contract_end_date = old.contract_end_date
        print("旧プラン日付", old_contract_end_date)
        print("旧プラン日付タイプ", type(old_contract_end_date))

        # 現在の契約期限 - 本日　＝　契約残日数
        print('oldのひづけどうなっている？？',old_contract_end_date.date())
        print('todayのひづけどうなっている？？',today.date())

        remaining_day = (old_contract_end_date.date() - today.date()).days
        print('残りの契約日数',int(remaining_day))


        difference_price_math = 0

        #プラン変更無
        if old_plan == new_plan:
            print("プラン変更無し")

            
            #リストを回して各オプション比較
            for old , new in options_list:
                #オプションどちらもあり    
                if old and new:
                    #オプション変更あり
                    if not old == new:
                        print('プラン変更なし＆オプション変更有り＆どちらもオプション存在')
                        dif_option_price_math = 0

                        old_option_price = Plan.objects.values("price").get(pk=old.id)
                        new_option_price = Plan.objects.values("price").get(pk=new.id)
                        dif_option_price = (int(new_option_price["price"]) - int(old_option_price["price"])) / 365 * int(remaining_day)
                        dif_option_price_math = math.floor(dif_option_price)
                    #変化なし
                    else:
                        dif_option_price_math = 0


                #新オプションのみあり
                elif new:
                    dif_option_price_math = 0

                    new_option_price = Plan.objects.values("price").get(pk=new.id)
                    dif_option_price = int(new_option_price["price"]) / 365 * int(remaining_day)

                    dif_option_price_math = math.floor(dif_option_price)

                    print('プラン変更なし＆オプション変更有り＆新オプションあり',dif_option_price_math)

                #新旧オプションなし
                else:
                    print('他にオプション無し')
                    dif_option_price_math = 0
                    


                difference_price_math += dif_option_price_math
            print('difference_price_mathのあたい',difference_price_math)


        #プラン変更有
        else:
            print("プラン変更有り")

            old_plan_price = Plan.objects.values("price").get(pk=old_plan.id)
            print("旧プランの金額", old_plan_price)
            new_plan_price = Plan.objects.values("price").get(pk=new_plan.id)
            print("新プランの金額", new_plan_price)

            # プラン差額を計算
            dif_plan_price = (int(new_plan_price["price"]) - int(old_plan_price["price"])) / 365 * int(remaining_day)
            print('dif_plan_priceの情報',dif_plan_price)
            # 切り捨て
            dif_plan_price_math = math.floor(dif_plan_price)
            print("プランの差額", dif_plan_price_math)

            #オプション変更
            difference_price_math = dif_plan_price_math
            dif_option_price_math = 0

            #リストを回して各オプション比較
            for old , new in options_list:
                #オプションどちらもあり
                if old and new:
                    #オプション変更あり
                    if not old == new:
                        dif_option_price_math = 0

                        print('プランオプション変更有り＆どちらもオプション存在')

                        old_option_price = Plan.objects.values("price").get(pk=old.id)
                        new_option_price = Plan.objects.values("price").get(pk=new.id)
                        dif_option_price = (int(new_option_price["price"]) - int(old_option_price["price"])) / 365 * int(remaining_day)
                        dif_option_price_math = math.floor(dif_option_price)

                #新オプションのみあり
                elif new:
                    dif_option_price_math = 0

                    new_option_price = Plan.objects.values("price").get(pk=new.id)
                    dif_option_price = int(new_option_price["price"]) / 365 * int(remaining_day)

                    dif_option_price_math = math.floor(dif_option_price)

                    print('プラン変更あり＆オプション変更有り＆新オプションあり',dif_option_price_math)

                #新旧オプションなし
                else:
                    dif_option_price_math = 0


                difference_price_math += dif_option_price_math

            print('difference_price_mathのあたい',difference_price_math)
        estimate.difference = difference_price_math
        
        estimate.is_updating = True
        # 保存
        estimate.save()
        # 入力した値を、セッションに保存    
        self.request.session['page_num'] = 2
        self.request.session['form_data'] = self.request.POST
        self.request.session['remaining_day'] = remaining_day
        self.request.session['old_id'] = old_id
        self.request.session['difference_price_math'] = difference_price_math
        self.request.session['estimate'] = estimate.id

        contract = form.save(commit=False)
        print('コントラクトのフォーム保存')
        # 支払いへ遷移
        if estimate.method_payment.id == 1:
            return HttpResponseRedirect(reverse('payment:change_contract_2_card'))
        else:
            return HttpResponseRedirect(reverse('payment:change_contract_2_bank'))


"""
プラン変更確認画面(カード)
"""
# @method_decorator(login_required, name = 'dispatch')
class ChangePlanConfirmCard(LoginRequiredMixin, TemplateView, CommonView):
    model = Contract
    template_name = 'payment/change_contract/change_contract_2_card.html'
    login_url = '/login/'

    def dispatch(self, request, *args, **kwargs):
        # 不正遷移check
        if not 'page_num' in self.request.session:
            return render(request, '406.html', status=406)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        print('card@__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@')
        user = self.request.user
        context = super().get_context_data(**kwargs)
        form_data = self.request.session.get('form_data', None)
        estimate = Estimates.objects.get(pk = self.request.session['estimate'])
        contract = Contract.objects.filter(service=estimate.service,status='2',company=user.company).first()
        print('～～～～～～～～～～こんとらくとの有無',contract)
        difference_price_math = self.request.session.get('difference_price_math', None)
        form = self.request.session.get('form_data', None)

        print(form_data)
        print(difference_price_math)
        context['estimate'] = estimate
        context['contract'] = contract

        context['form'] = form
        context['difference_price_math'] = difference_price_math

        #STRIPEのパブリックキーをテンプレートへ渡す
        context["pay_public_key"] = settings.STRIPE_PUBLISHABLE_KEY

        return context

    def post(self, request):
            print("差額自動支払い")

            user = self.request.user
            
            stripe_obj = Stripe.objects.filter(company=user.company_id).first()

            # STRIPEのシークレットキーの読み込み
            stripe.api_key = settings.STRIPE_API_KEY

            # STRIPEの顧客IDを取得
            customer_id = user.company.stripe.stripe_cus_id
            print('stripeID',customer_id)
            estimate = Estimates.objects.get(pk = self.request.session['estimate'])
            old_contract = Contract.objects.filter(service=estimate.service,status='2',company=user.company).first()
            new_start_date = old_contract.contract_end_date + relativedelta(days=1 ,hour=0,minute=0,second=0,microsecond=0)
            #通常のサブスクリプション
            if old_contract.payment.stripe_plan:
                subscription = stripe.Subscription.retrieve(old_contract.payment.stripe_plan)
                print('通常のサブスクリプション',subscription)
            elif old_contract.payment.stripe_sched_plan:
                #予約されたサブスクリプション
                sched_subscription = stripe.SubscriptionSchedule.retrieve(old_contract.payment.stripe_sched_plan)
                print('予約されたサブスクリプション',sched_subscription)
            # 支払い管理レコードを作成
            payment = Payment.objects.create(user=user)
            #更新後の契約(statusは更新用の4)
            contract = Contract.objects.create(user=user,service=estimate.service, company=user.company)
            today = datetime.now()
            
            
            print('差額・・・・・・・・・',estimate.difference)

             # 紐づく支払いを契約テーブルに保存
            contract.payment = payment
            contract.plan = estimate.plan
            print('planOKOKOKOKOKOKOKOKOKOKOKOKOK')
                
            #Subscription.createに渡す
            if estimate.unit_total >= 30000:
                item_set = [{"price":estimate.plan.stripe_price_id}]
            else:
                item_set = [{"price":estimate.plan.stripe_price_id},{"price":"price_1MUgVyI8iZ48PSn6ctfLVE2H"}]

            if estimate.option1 and not estimate.option1.stripe_plan_id == 'pln':
                option_1 = {'price':estimate.option1.stripe_price_id}
                item_set.append(option_1)
                contract.option1 = estimate.option1
            if estimate.option2 and not estimate.option2.stripe_plan_id == 'pln':
                option_2 = {'price':estimate.option2.stripe_price_id}
                item_set.append(option_2)
                contract.option2 = estimate.option2
            if estimate.option3 and not estimate.option3.stripe_plan_id == 'pln':
                option_3 = {'price':estimate.option3.stripe_price_id}
                item_set.append(option_3)
                contract.option3 = estimate.option3
            if estimate.option4 and not estimate.option4.stripe_plan_id == 'pln':
                option_4 = {'price':estimate.option4.stripe_price_id}
                item_set.append(option_4)
                contract.option4 = estimate.option4
            if estimate.option5 and not estimate.option5.stripe_plan_id == 'pln':
                option_5 = {'price':estimate.option5.stripe_price_id}
                item_set.append(option_5)
                contract.option5 = estimate.option5
            print('optionOKOKOKOKOKOKOKOKOKOKOKOKOK')
            
            #支払い手段の情報を取得
            cus_card = stripe.Customer.list_payment_methods(
                customer_id,
                type="card",
            )

            #　支払い
            try:
                print('とらいきた')
                stripe.PaymentIntent.create(
                    amount=estimate.difference,# 支払金額
                    currency='jpy',# 利用通貨
                    customer=customer_id,# CustomerオブジェクトID
                    payment_method=cus_card["data"][0]["id"],# 支払いに使用するクレジットカード
                    off_session=True,# 支払いの実行時に顧客が決済フローに存在しないことを示す
                    confirm=True,# PaymentIntentの作成と確認を同時に行う
                    description=user.id,
                )

                if old_contract.payment.stripe_plan:
                    #現在の支払い済みのサブスクリプションを期間終了後にキャンセルさせる
                    stripe.Subscription.modify(
                        subscription.id,
                        cancel_at_period_end=True
                    )
                    if old_contract.payment.stripe_sched_plan:
                        stripe.SubscriptionSchedule.cancel(
                            sched_subscription.id,
                        )
                        old_contract.payment.stripe_sched_plan = None
                elif old_contract.payment.stripe_sched_plan:
                    stripe.SubscriptionSchedule.cancel(
                        sched_subscription.id,
                    )

                #次年度分のサブスクリプション登録
                stripe_plan = stripe.SubscriptionSchedule.create(
                    customer=customer_id,
                    start_date=new_start_date,
                    end_behavior='release',
                    phases=[
                        {
                        'items': item_set,
                        'iterations': 12,
                        'default_tax_rates' : ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                        },
                    ],
                )
                # if estimate.discount:
                #     print('割引あり')
                #     stripe.PaymentIntent.create(
                #         amount=estimate.difference,# 支払金額
                #         currency='jpy',# 利用通貨
                #         customer=customer_id,# CustomerオブジェクトID
                #         payment_method=cus_card["data"][0]["id"],# 支払いに使用するクレジットカード
                #         off_session=True,# サーバーのみで処理
                #         confirm=True,# PaymentIntentの作成と確認を同時に行う
                #         description=user.id,
                #     )


                #     if 'sched_subscription' in locals() and 'subscription' in locals():
                #         #現在の支払い済みのサブスクリプションを期間終了後にキャンセルさせる
                #         stripe.Subscription.modify(
                #             subscription.id,
                #             cancel_at_period_end=True
                #         )
                #     elif 'subscription' in locals():
                #         #現在の支払い済みのサブスクリプションを期間終了後にキャンセルさせる
                #         stripe.Subscription.modify(
                #             subscription.id,
                #             cancel_at_period_end=True
                #         )
                #     elif 'sched_subscription' in locals():
                #         stripe.SubscriptionSchedule.cancel(
                #             sched_subscription.id,
                #         )   


                #     #次年度分のサブスクリプション登録
                #     stripe_plan = stripe.SubscriptionSchedule.create(
                #         customer=customer_id,
                #         start_date=new_start_date,
                #         end_behavior='release',
                #         phases=[
                #             {
                #             'items': item_set,
                #             'iterations': 12,
                #             'default_tax_rates' : ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                #             },
                #         ],
                #     )

                # else:
                #     print('割引なし',estimate.difference)

                #     stripe.PaymentIntent.create(
                #         amount=estimate.difference,# 支払金額
                #         currency='jpy',# 利用通貨
                #         customer=customer_id,# CustomerオブジェクトID
                #         payment_method=cus_card["data"][0]["id"],# 支払いに使用するクレジットカード
                #         off_session=True,# 支払いの実行時に顧客が決済フローに存在しないことを示す
                #         confirm=True,# PaymentIntentの作成と確認を同時に行う
                #         description=user.id,
                #     )

                #     if old_contract.payment.stripe_plan:
                #         #現在の支払い済みのサブスクリプションを期間終了後にキャンセルさせる
                #         stripe.Subscription.modify(
                #             subscription.id,
                #             cancel_at_period_end=True
                #         )
                #     else:
                #         stripe.SubscriptionSchedule.cancel(
                #             sched_subscription.id,
                #         )   

                #     #次年度分のサブスクリプション登録
                #     stripe_plan = stripe.SubscriptionSchedule.create(
                #         customer=customer_id,
                #         start_date=new_start_date,
                #         end_behavior='release',
                #         phases=[
                #             {
                #             'items': item_set,
                #             'iterations': 12,
                #             'default_tax_rates' : ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                #             },
                #         ],
                #     )

                # 見積りIDを保存
                contract.estimate.add(estimate)
                # 請求書オプションを契約テーブルに保存
                contract.is_invoice_need = estimate.is_invoice_need
                # #クーポンを契約テーブルに保存
                # if estimate.discount:
                #     contract.discount = estimate.discount
                # 見積りの小計を契約テーブルに保存
                contract.minor_total = estimate.minor_total

                # 見積りの消費税を契約テーブルに保存
                contract.tax = estimate.tax

                # 見積りの合計を契約テーブルに保存
                contract.total = estimate.total

                # 契約開始・終了日付をセット
                contract.contract_start_date = estimate.start_day
                contract.contract_end_date = estimate.end_day
                # 作成したStripe定期課金スケジュールのIDを保存
                payment.stripe_sched_plan = stripe_plan.id
                # 見積りの支払い方法を支払いテーブルに保存
                payment.method_payment = estimate.method_payment
                # 支払いフラグをON
                payment.is_paymented = True 
                # 使用フラグをON
                estimate.is_use = True
                # 契約フラグをON
                estimate.is_signed = True
                #プラン変更用フラグをFalseに
                estimate.is_change = False
                contract.status = "2"
                contract.pay_start_date = today
                contract.pay_end_date = today
                # 自動更新フラグをON
                contract.is_autocheckout = old_contract.is_autocheckout
                #旧契約を解約済みにする
                old_contract.status = "4"
                #旧契約の契約終了日を変更
                old_contract.contract_end_date = estimate.start_day
                old_contract.payment.save()
                old_contract.is_updating = False
                old_contract.save()
                
                contract.is_updating = False
                estimate.is_updating = False
                # 保存
                contract.save()
                payment.save()
                
                estimate.save()

                print('tryの処理終了～～～～～～～～～～～～～～～～～～～～～～～～～')
            
            except stripe.error.InvalidRequestError as e:
                context = {
                    "err_message":"エラーが発生しました。運営に問い合わせてください。メッセージ：" + str(e)
                }
                return  render(request, 'payment/checkout_error.html', context)
            # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
            for key in list(self.request.session.keys()):
                if not key.startswith("_"):
                    del self.request.session[key]
            self.request.session['contract'] = contract.id

            return redirect('payment:checkout_done')



"""
プラン変更確認画面(銀行振込)
"""
class ChangePlanConfirmBank(LoginRequiredMixin, TemplateView, CommonView):
    model = Contract
    template_name = 'payment/change_contract/change_contract_2_bank.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        print('bank@__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@ @__@')
        user = self.request.user
        context = super().get_context_data(**kwargs)
        form_data = self.request.session.get('form_data', None)
        estimate = Estimates.objects.get(pk = self.request.session['estimate'])
        contract = Contract.objects.get(service=estimate.service,status='2',company=user.company)

        difference_price_math = self.request.session.get('difference_price_math', None)
        form = self.request.session.get('form_data', None)

        print(form_data)
        print(difference_price_math)
        context['estimate'] = estimate
        context['contract'] = contract

        context['form'] = form
        context['difference_price_math'] = difference_price_math

        return context

    def post(self, request):
        print("銀行支払い処理開始")
        user = request.user
        # 見積書に記載された情報を取得
        estimate = Estimates.objects.get(pk = self.request.session['estimate'])
        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=request.user)
        print('paymentidは～～～',payment.id)
        #現契約
        old_contract = Contract.objects.get(service=estimate.service,status='2',company=user.company)
        #更新後の契約(statusは更新用の4)
        contract = Contract.objects.create(user=user,service=estimate.service, company=user.company)
        
        today = datetime.now()

        #　支払い
        try:
            # 紐づく支払いを契約テーブルに保存
            contract.payment = payment
            print('tryにすすんだ～～～～～～～～～～～～～～～～～～')
            contract.payment.is_paymented = False
            print('method_paymentOKOKOKOKOKOKOKOKOKOKOKOKOK',contract.payment.id)
            contract.plan = estimate.plan
            print('planOKOKOKOKOKOKOKOKOKOKOKOKOK')

            # 見積りのオプションを契約テーブルに上書き保存
            if estimate.option1:
                contract.option1 = estimate.option1
            if estimate.option2:
                contract.option2 = estimate.option2
            if estimate.option3:
                contract.option3 = estimate.option3
            if estimate.option4:
                contract.option4 = estimate.option4
            if estimate.option5:
                contract.option5 = estimate.option5
            print('optionOKOKOKOKOKOKOKOKOKOKOKOKOK')
            
            # 銀行振込なので自動更新もNull
            contract.is_autocheckout = False
            # 見積りIDを保存
            contract.estimate.add(estimate)
            # 請求書オプションを契約テーブルに保存
            contract.is_invoice_need = estimate.is_invoice_need
            #クーポンを契約テーブルに保存
            # if estimate.discount:
            #     contract.discount = estimate.discount
            # 見積りの小計を契約テーブルに保存
            contract.minor_total = estimate.minor_total

            # 見積りの消費税を契約テーブルに保存
            contract.tax = estimate.tax

            # 見積りの合計を契約テーブルに保存
            contract.total = estimate.total

            # 契約開始・終了日付をセット
            contract.contract_start_date = estimate.start_day
            contract.contract_end_date = estimate.end_day
            
            # 見積りの支払い方法を支払いテーブルに保存
            payment.method_payment = estimate.method_payment
            
            #プラン変更用フラグをFalseに
            estimate.is_use = True
            estimate.is_change = False
            # 契約フラグをON
            estimate.is_signed = True
            contract.status = "2"

            #旧契約にステータス更新
            old_contract.status = '4'
            #旧契約の契約終了日を変更
            old_contract.contract_end_date = estimate.start_day
            old_contract.save()
            old_contract.is_updating = False
            
            contract.is_updating = False
            estimate.is_updating = False
            # 保存
            contract.save()
            payment.save()
            
            estimate.save()

            print('tryの処理終了～～～～～～～～～～～～～～～～～～～～～～～～～')
        except Exception as e:
            context = {
                "err_message":"エラーが発生しました。運営に問い合わせてください。メッセージ：" + str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)
        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]
        self.request.session['contract'] = contract.id
        print('セッションにcontract保存～～～～～～～～～～～～～～～～～')
        return redirect('payment:checkout_done')


"""
解約
"""
# @method_decorator(login_required, name = 'dispatch')
class Cancellation(LoginRequiredMixin, View):
    login_url = '/login/'

    def post(self, request):

        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY
        contract_id = request.POST.get('contract_id')
        contract = Contract.objects.filter(pk=contract_id).select_related('payment').first()


        if contract.payment.method_payment.id == 1:
            #stripeはオリジナル保持
            try:

                # プランの解約(STRIPEとしてはキャンセル処理)
                if contract.payment.stripe_plan:
                    subscription_plan = stripe.Subscription.retrieve(contract.payment.stripe_plan)
                    # cancel_sub_plan = subscription_plan.delete()
                    stripe.Subscription.modify(
                        subscription_plan.id,
                        cancel_at_period_end=True
                    )
                    contract.status = "3" #3は解約
                
                if contract.payment.stripe_sched_plan:
                    sched_subscription = stripe.SubscriptionSchedule.retrieve(contract.payment.stripe_sched_plan)

                    if sched_subscription:
                        stripe.SubscriptionSchedule.cancel(
                            sched_subscription.id,
                        )
                        contract.payment.stripe_sched_plan=None

                # 契約終了日を解約した日に更新
                contract.contract_end_date = datetime.now()

                contract.save()

            except stripe.error.CardError as e:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました" + str(e),
                                    })

            except stripe.error.InvalidRequestError as e:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました" + str(e),
                                    })

            except stripe.error.AuthenticationError as e:
                return JsonResponse({"status": "ng",
                                    "message": "解約失敗しました" + str(e),
                                    })

            except stripe.error.APIConnectionError as e:
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

        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY

        # 契約オブジェクトの取得
        contract = Contract.objects.filter(pk=contract_id).select_related('payment').first()

        # 自動更新ONの場合
        if is_checked == "true":
            try:
                print('おんにはいった')
                # 基本プランの再開(STRIPEとしては、キャンセル状態の定期課金を再開させる)
                if contract.payment.stripe_plan:
                    subscription_plan = stripe.Subscription.retrieve(contract.payment.stripe_plan)

                    stripe.Subscription.modify(
                                subscription_plan.id,
                                cancel_at_period_end=False
                            )
                else:
                    # #次年度分のサブスクリプション登録
                    new_start_date = contract.contract_end_date + relativedelta(days=1 ,hour=0,minute=0,second=0,microsecond=0)
                    customer_id = self.request.user.company.stripe.stripe_cus_id

                    if contract.minor_total >= 30000:
                        item_set = [{"price":contract.plan.stripe_price_id}]
                    else:
                        item_set = [{"price":contract.plan.stripe_price_id},{"price":"price_1MUgVyI8iZ48PSn6ctfLVE2H"}]

                    if contract.option1 and not contract.option1.stripe_plan_id == 'pln':
                        option_1 = {'price':contract.option1.stripe_price_id}
                        item_set.append(option_1)
                    if contract.option2 and not contract.option2.stripe_plan_id == 'pln':
                        option_2 = {'price':contract.option2.stripe_price_id}
                        item_set.append(option_2)
                    if contract.option3 and not contract.option3.stripe_plan_id == 'pln':
                        option_3 = {'price':contract.option3.stripe_price_id}
                        item_set.append(option_3)
                    if contract.option4 and not contract.option4.stripe_plan_id == 'pln':
                        option_4 = {'price':contract.option4.stripe_price_id}
                        item_set.append(option_4)
                    if contract.option5 and not contract.option5.stripe_plan_id == 'pln':
                        option_5 = {'price':contract.option5.stripe_price_id}
                        item_set.append(option_5)

                    stripe_plan = stripe.SubscriptionSchedule.create(
                        customer=customer_id,
                        start_date=new_start_date,
                        end_behavior='release',
                        phases=[
                            {
                            'items': item_set,
                            'iterations': 12,
                            'default_tax_rates' : ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                            },
                        ],
                    )

                    contract.payment.stripe_sched_plan = stripe_plan.id
                    contract.payment.save()

                # 自動更新フラグをON
                contract.is_autocheckout = True

                contract.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "自動更新を有効にしました",
                                    })

            except Exception as e:
                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })
        # 自動更新OFFの場合
        else:
            try:

                # 基本プランの解約(STRIPEとしてはキャンセル処理。現在の周期の終了日をもって定期課金を終了させる。)            
                #サブスクリプションキャンセル予約
                if contract.payment.stripe_plan:
                    subscription_plan = stripe.Subscription.retrieve(contract.payment.stripe_plan)
                    print('キャンセルしたいサブスクリプションsubscription_plan',subscription_plan)
                    stripe.Subscription.modify(
                        subscription_plan.id,
                        cancel_at_period_end=True
                    )
                    print('サブスクリプションキャンセル予約OK')
                #サブスクリプションスケジュール解約
                if contract.payment.stripe_sched_plan:
                    sched_subscription = stripe.SubscriptionSchedule.retrieve(contract.payment.stripe_sched_plan)
                    
                    if sched_subscription:
                        stripe.SubscriptionSchedule.cancel(
                            sched_subscription.id,
                        )
                        contract.payment.stripe_sched_plan=None
                        contract.payment.save()
                        print('サブスクリプションスケジュールキャンセルOK')


                # 自動更新フラグをOFF
                contract.is_autocheckout = False

                contract.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "自動更新を無効にしました",
                                    })


            except Exception as e:
                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                                    契約更新
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


"""
カード支払いの手動契約更新
"""
class UpdateContractCard(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/update_contract/card.html'
    context_object_name = 'estimate'
    login_url = '/login/'


    def dispatch(self, request, *args, **kwargs):

        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company).first()

        if not stripe_obj:
            messages.error(request, "クレジットカードが未登録です。登録してください。")
            return redirect('payment:card_info')
        return super().dispatch(request, *args, **kwargs)


    def post(self, request, pk):
        user = self.request.user
        stripe_obj = Stripe.objects.filter(company=user.company_id).first()
        autocheckout = request.POST.get('autocheckout')
        is_start_now = request.POST.get('is_start_now')

        # STRIPEのシークレットキーの読み込み
        stripe.api_key = settings.STRIPE_API_KEY

        # STRIPEの顧客IDを取得
        customer_id = user.company.stripe.stripe_cus_id

        # 見積書に記載されたプランのStripeIDを取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        stripe_plan_id = estimate.plan.stripe_plan_id

        # 契約DBを取得
        contract = Contract.objects.get(company=user.company, service=estimate.service,status="2")

        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=user)

        # 契約終了日
        contract_end_date = contract.contract_end_date
        print("=====================================================契約終了日", contract_end_date)

        unix_contract_end_date = contract_end_date.timestamp()

        print("終了日3", unix_contract_end_date)

        #Subscription.createに渡す
        if estimate.unit_total >= 30000:
            item_set = [{"price":estimate.plan.stripe_price_id}]
        else:
            item_set = [{"price":estimate.plan.stripe_price_id},{"price":"price_1MUgVyI8iZ48PSn6ctfLVE2H"}]

        option_list = []

        if estimate.option1 and not estimate.option1.stripe_plan_id == 'pln':
            option_1 = {'price':estimate.option1.stripe_price_id}
            item_set.append(option_1)
            option_list.append(estimate.option1)
        if estimate.option2 and not estimate.option2.stripe_plan_id == 'pln':
            option_2 = {'price':estimate.option2.stripe_price_id}
            item_set.append(option_2)
            option_list.append(estimate.option2)
        if estimate.option3 and not estimate.option3.stripe_plan_id == 'pln':
            option_3 = {'price':estimate.option3.stripe_price_id}
            item_set.append(option_3)
            option_list.append(estimate.option3)
        if estimate.option4 and not estimate.option4.stripe_plan_id == 'pln':
            option_4 = {'price':estimate.option4.stripe_price_id}
            item_set.append(option_4)
            option_list.append(estimate.option4)
        if estimate.option5 and not estimate.option5.stripe_plan_id == 'pln':
            option_5 = {'price':estimate.option5.stripe_price_id}
            item_set.append(option_5)
            option_list.append(estimate.option5)

        # 契約テーブル上のオプションをリセット
        if contract.option1:
            contract.option1 = None
        if contract.option2:
            contract.option2 = None
        if contract.option3:
            contract.option3 = None
        if contract.option4:
            contract.option4 = None
        if contract.option5:
            contract.option5 = None

        try:

            """
            stripe側処理
            """
            if option_list:
                # if estimate.discount:

                #     # 定期課金の作成
                #     stripe_plan = stripe.Subscription.create(
                #         customer = customer_id,
                #         items = item_set,
                #         default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                #         coupon = estimate.discount.coupon_id,
                #         description = user.id,
                #         # 課金処理を前契約の完了日とするためトライアル日を設定
                #         trial_end = int(unix_contract_end_date)
                #     )
                #     print('定期課金の作成')

                #     contract.discount = estimate.discount
                # 定期課金の作成
                stripe_plan = stripe.Subscription.create(
                    customer = customer_id,
                    items = item_set,
                    default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                    description = user.id,
                    # 課金処理を前契約の完了日とするためトライアル日を設定
                    trial_end = int(unix_contract_end_date)
                )
                print('定期課金の作成')
                # 前契約の割引を削除
                if contract.discount:
                    contract.discount = None

                # 見積りのオプションを契約テーブルに上書き保存
                if estimate.option1:
                    contract.option1 = estimate.option1
                if estimate.option2:
                    contract.option2 = estimate.option2
                if estimate.option3:
                    contract.option3 = estimate.option3
                if estimate.option4:
                    contract.option4 = estimate.option4
                if estimate.option5:
                    contract.option5 = estimate.option5
            
            else:

                # if estimate.discount:

                #     # 定期課金の作成
                #     stripe_plan = stripe.Subscription.create(

                #     customer = customer_id,
                #     items = [
                #         {"price":estimate.plan.stripe_price_id},
                #     ],
                #     default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                #     coupon = estimate.discount.coupon_id,
                #     description = user.id,
                #     # 課金処理を前契約の完了日とするためトライアル日を設定
                #     trial_end = int(unix_contract_end_date)
                #     )
                    
                #     contract.discount = estimate.discount

                # 定期課金の作成
                stripe_plan = stripe.Subscription.create(
                customer = customer_id,
                items = [
                    {"price":estimate.plan.stripe_price_id},
                ],
                default_tax_rates = ['txr_1LfIZxI8iZ48PSn6MKzDy1LK'],
                description = user.id,
                # 課金処理を前契約の完了日とするためトライアル日を設定
                trial_end = int(unix_contract_end_date)
                )
                # 前契約の割引を削除
                if contract.discount:
                    contract.discount = None


            # 作成したSTRIPE定期課金のIDを保存
            payment.stripe_plan = stripe_plan.id

            # 自動更新OFFの場合は、その場でキャンセルする
            if autocheckout ==  "False":
                stripe.Subscription.modify(
                    stripe_plan.id,
                    cancel_at_period_end=True
                )

            # 定期課金が作成された
            if stripe_plan.created:

                # 支払いフラグをON
                payment.is_paymented = True

                # 支払い回数をカウントアップ
                payment.pay_count = payment.pay_count + 1

                # 支払い日を登録
                payment.created_date = datetime.fromtimestamp(stripe_plan.created)

                # 契約日付
                # すぐに開始の場合は支払い日付をセット
                if is_start_now == None:
                    contract.contract_start_date = estimate.start_day
                    contract.contract_end_date = estimate.end_day
                else:
                    contract.contract_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                    contract.contract_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)

                # 支払い日付
                contract.pay_start_date = datetime.fromtimestamp(stripe_plan.current_period_start)
                contract.pay_end_date = datetime.fromtimestamp(stripe_plan.current_period_end)


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

                #仮作成フラグをオフ
                estimate.tempcheck = False
                # 見積り使用フラグをON
                estimate.is_use = True
                # 契約フラグをON
                estimate.is_signed = True
                
                estimate.save()

        except stripe.error.CardError as e:
            context = {
                "err_message":"このカードはご利用になれません。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.InvalidRequestError as e:
            context = {
                "err_message":"入力いただいた情報に誤りがあります。今一度ご確認をお願いします。解決できない場合はエラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name
            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.AuthenticationError as e:
            context = {
                "err_message":"システムエラーが発生しております。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name

            }
            return  render(request, 'payment/checkout_error.html', context)

        except stripe.error.APIConnectionError as e:
            context = {
                "err_message":"APIConnectionErroによりエラーが発生しています。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e),
                "err_message_url" : self.request.resolver_match.url_name

            }
            return  render(request, 'payment/checkout_error.html', context)

        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract'] = contract.id
       
        return redirect('payment:update_contract_done')

"""
銀行振込の手動契約更新
"""
class UpdateContractBank(LoginRequiredMixin, DetailView, CommonView, View):
    model = Estimates
    template_name = 'payment/update_contract/bank.html'
    context_object_name = 'estimate'
    login_url = '/login/'

    def post(self, request, pk):

        # 見積書に記載された情報を取得
        estimate = Estimates.objects.select_related().get(pk=pk)
        # 支払い管理レコードを作成
        payment = Payment.objects.create(user=request.user)

        user = request.user
        # 契約DBへ本契約の有効期限を保存
        contract, created = Contract.objects.get_or_create(user=user, service=estimate.service, company=user.company)

        try:

            # 試用プランの削除
            contract.plan = None

            # 紐づく支払いを契約テーブルに保存
            contract.payment=payment

            # 見積りのプランを契約テーブルに保存
            contract.plan = estimate.plan

            # 契約テーブル上のオプションをリセット
            if contract.option1:
                contract.option1 = None
            if contract.option2:
                contract.option2 = None
            if contract.option3:
                contract.option3 = None
            if contract.option4:
                contract.option4 = None
            if contract.option5:
                contract.option5 = None

            # 見積りのオプションを契約テーブルに上書き保存
            if estimate.option1:
                contract.option1 = estimate.option1
            if estimate.option2:
                contract.option2 = estimate.option2
            if estimate.option3:
                contract.option3 = estimate.option3
            if estimate.option4:
                contract.option4 = estimate.option4
            if estimate.option5:
                contract.option5 = estimate.option5
            

            # ステータスの変更
            contract.status = "2" #本番

            # 銀行振込なので自動更新もNull
            contract.is_autocheckout = False

            # 見積りIDを保存
            contract.estimate.add(estimate)

            # 請求書オプションを契約テーブルに保存
            contract.is_invoice_need = estimate.is_invoice_need

            # 前契約の割引を削除
            if contract.discount:
                contract.discount = None
            #クーポンを契約テーブルに保存
            # if estimate.discount:
            #     contract.discount = estimate.discount

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

            #仮作成フラグをオフ
            estimate.tempcheck = False

            # 見積り使用フラグをON
            estimate.is_use = True
            # 契約フラグをON
            estimate.is_signed = True
            
            estimate.save()

        except Exception as e:
            context = {
                "err_message":"問題が発生しました。エラーコードを添えてお問い合わせください。",
                "err_message_raw" : str(e)
            }
            return  render(request, 'payment/checkout_error.html', context)
        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]
        # 生成されたDBの対象行のIDをセッションに保存しておく
        self.request.session['contract'] = contract.id
        
        return redirect('payment:update_contract_done')

"""
更新完了
"""
#プラン変更完了
class UpdateContractDone(LoginRequiredMixin, TemplateView, CommonView):
    model = Contract
    template_name = 'payment/update_contract/update_contract_done.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract = Contract.objects.filter(pk = self.request.session['contract']).first()
        context['contract'] = contract
        return context


"""
Webhookでサブスク書き換え
"""
from django.http import HttpResponse
import json
class UpdateSubscription(View):
    template_name = 'payment/update_subscription.html'

    def post(self, request):
        post_data = json.loads(request.body.decode("utf-8"))

        #前年度中にプラン変更があり、契約更新の際に予約IDからサブスクリプション本IDに変わる場合のイベント
        if post_data['type'] == 'subscription_schedule.updated':

            subscription_schedule = post_data['data']['object']['id']
            if subscription_schedule:
                sched_sub = Payment.objects.filter(stripe_sched_plan=subscription_schedule).first()
                if sched_sub:
                    sched_sub.stripe_plan = post_data['data']['object']['subscription']
                    sched_sub.save()

        #自動契約更新にて、stripe側から更新イベントを受け取り、契約の期間を上書きするためのイベント
        elif post_data['type'] == 'invoice.finalized':
            subscription_id = post_data['data']['object']['subscription']
            ts_start = post_data['data']['object']['lines']['data'][0]['period']['start']
            ts_end = post_data['data']['object']['lines']['data'][0]['period']['end']
            subscription_start = datetime.fromtimestamp(ts_start)
            subscription_end = datetime.fromtimestamp(ts_end)

            if subscription_id:
                subscription = Payment.objects.filter(stripe_plan=subscription_id).first()
                if subscription:
                    contract =  Contract.objects.filter(payment_id=subscription.id).first()
                    ##差の絶対値を求める処理
                    different = abs(subscription_start.date() - contract.contract_start_date.date())

                    #stripeで受け取った契約期間と現在の契約書の契約期間に20日以上差があれば契約書を１年上書きする処理
                    if different.days > 20:
                        contract.contract_start_date = contract.contract_start_date + relativedelta(years=1)
                        contract.contract_end_date = contract.contract_end_date + relativedelta(years=1)
                        contract.save()

        else:
            print('Unhandled event type {}'.format(post_data['type']))

        return HttpResponse('ok')
