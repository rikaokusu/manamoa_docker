from django.urls import path, include
from . import views

app_name = 'contracts'


urlpatterns = [
    #契約管理
    path('contract/', views.ContractIndexView.as_view(), name='contract'),
    path('trial_contract_reg/', views.TrialContractRegAjaxView.as_view(), name='trial_contract_reg'),
    path('createEstimate/<uuid:pk>/pdf', views.EstimateToPDF.as_view(), name='estimateToPdf'),
    path('createEstimate/<uuid:pk>/html', views.EstimateToHTML.as_view(), name='estimateToHtml'),
    
    # 契約更新キャンセル
    # path('cont_update_cancel/<uuid:pk>', views.UpdateCancelView.as_view(), name='cont_update_cancel'),
    # 契約更新見積り作成(変更なし)
    path('cont_update_nochange_step1/<uuid:pk>', views.UpdateContractNoChangeStep1.as_view(), name='cont_update_nochange_step1'),
    # path('cont_update_nochange_step2/', views.UpdateContractNoChangeStep2.as_view(), name='cont_update_nochange_step2'),

    # 契約更新見積り作成(変更あり)
    path('cont_update_change_step1_1/<uuid:pk>', views.UpdateContractChangeStep1.as_view(), name='cont_update_change_step1_1'),
    path('cont_update_change_step1_2/', views.UpdateContractChangeStep2.as_view(), name='cont_update_change_step1_2'),
    #path('createEstimateforUpdate/<int:pk>', views.EstimateForUpdateCreate.as_view(), name='createEstimateforUpdate'),
    #path('createEstimateforUpdateNoChange/<int:pk>', views.EstimateForUpdateNoChangeCreate.as_view(), name='createEstimateforUpdateNoChange'),
    #契約更新見積り確認
    path('cont_update_step2/', views.UpdateContractStep2.as_view(), name='cont_update_step2'),
    path('update_estimate_done/', views.UpdateEstimateDone.as_view(), name='update_estimate_done'),

    # 見積管理
    path('estimate/', views.EstimateIndexView.as_view(), name='estimate'),
    #1つ前に戻る処理
    path('estimate_return/', views.EstimateReturnView.as_view(), name='estimate_return'),
    #キャンセル
    path('estimate_cancel/', views.EstimateCancelView.as_view(), name='estimate_cancel'),
    #見積り作成
    path('estimate_step1/', views.EstimateStep1.as_view(), name='estimate_step1'),
    path('estimate_step2/', views.EstimateStep2.as_view(), name='estimate_step2'),
    path('estimate_step3/', views.EstimateStep3.as_view(), name='estimate_step3'),
    path('estimate_step4/', views.EstimateStep4.as_view(), name='estimate_step4'),
    path('estimate_step5/', views.EstimateStep5.as_view(), name='estimate_step5'),
    #見積書複製
    path('estimate_copy1/<uuid:pk>', views.EstimateCopy1.as_view(), name='estimate_copy1'),
    path('estimate_copy2', views.EstimateCopy2.as_view(), name='estimate_copy2'),
    path('estimate_copy_done', views.EstimateCopyDone.as_view(), name='estimate_copy_done'),
    
    #見積書削除用
    path('estimate/delete_estimate/', views.delete_estimate, name='delete_estimate'),
    # 申込管理
    path('contracts/offer_description/<uuid:pk>', views.OfferDescription.as_view(), name='offer_description'),
    path('offer_step1/<uuid:pk>/', views.OfferStep1.as_view(), name='offer_step1'),
    path('select_estimate/<uuid:pk>/', views.SelectEstimate.as_view(), name='select_estimate'),

    # path('offer_step1/<uuid:pk>/<uuid:service_id>', views.OfferStep1.as_view(), name='offer_step1'),
    path('offer_step2/', views.OfferStep2.as_view(), name='offer_step2'),
    # path('offer_cancel/', views.OfferCancelView.as_view(), name='offer_cancel'),
    #見積存在確認
    path('estimate_collation/', views.EstimateAjaxView.as_view(), name='estimate_collation'),
    #クーポン適用可否
    path('discount_check/', views.DiscountCheckView.as_view(), name='discount_check'),
]
