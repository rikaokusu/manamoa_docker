from django.urls import path, include

# from .views import CreateCard,CreateCardDone
from . import views
from django.views.decorators.csrf import csrf_exempt

app_name = 'payment'

urlpatterns = [
    # カードの作成
    path('card_create/', views.CardCreate.as_view(), name='card_create'),
    # カードの情報
    path('card/', views.CardInfo.as_view(), name='card_info'),
    # カードの更新
    path('card_update/', views.CardUpdate.as_view(), name='card_update'),

    # 支払い
    path('update_return/', views.UpdateContractCard.as_view(), name='update_contract_card'),
    path('payment_return/', views.PaymentReturnView.as_view(), name='payment_return'),
    
    path('checkout/<uuid:pk>', views.Checkout.as_view(), name='checkout'),
    path('checkout_from_offer/<uuid:pk>', views.CheckoutFromOffer.as_view(), name='checkout_from_offer'),
    path('checkout_bank/<uuid:pk>', views.CheckoutBank.as_view(), name='checkout_bank'),
    path('checkout_bank_from_offer/<uuid:pk>', views.CheckoutBankFromOffer.as_view(), name='checkout_bank_from_offer'),
    path('checkout_done/', views.CheckoutDone.as_view(), name='checkout_done'),
    path('checkout_from_offer_done/', views.CheckoutFromOfferDone.as_view(), name='checkout_from_offer_done'),
    #　戻るボタン
    path('contract_return/', views.ContractReturnView.as_view(), name='contract_return'),

    # 契約更新(カード)
    path('update_contract_card/<uuid:pk>', views.UpdateContractCard.as_view(), name='update_contract_card'),
    # 契約更新(振込)
    path('update_contract_bank/<uuid:pk>', views.UpdateContractBank.as_view(), name='update_contract_bank'),
    # 契約更新完了
    path('update_contract_done', views.UpdateContractDone.as_view(), name='update_contract_done'),

    # 契約更新
    path('update_from_offer/<uuid:pk>', views.UpdateFromOffer.as_view(), name='update_from_offer'),

    # 契約更新(変更あり)
    path('update_from_offer_change/<uuid:pk>', views.UpdateFromOffer.as_view(), name='update_from_offer_change'),


    #自動更新変更
    path('autocheckchange', views.AutoCheckoutChange.as_view(), name='autocheckchange'),

    # プラン変更
    path('contract_cancel/', views.ContractCancelView.as_view(), name='contract_cancel'),
    path('change_contract_1/<uuid:pk>', views.ChangeContract.as_view(), name='change_contract_1'),
    path('change_contract_2_card/', views.ChangePlanConfirmCard.as_view(), name='change_contract_2_card'),
    path('change_contract_2_bank/', views.ChangePlanConfirmBank.as_view(), name='change_contract_2_bank'),

    # 来年度分の手動支払い
    path('manualcheckout/<uuid:pk>', views.ManualCheckout.as_view(), name='manual_checkout'),

    # 解約
    path('cancellation', views.Cancellation.as_view(), name='cancellation'),
    #WebhookでサブスクID書き換え
    path('update_subscription', csrf_exempt(views.UpdateSubscription.as_view()), name='update_subscription'),

]
