from django.urls import path

# from .views import CreateCard,CreateCardDone
from . import views 

app_name = 'bulk'

urlpatterns = [
    # HOME
    path('home/', views.HomeTemplateView.as_view(), name='home'),

    # インポート
    path('ajax_import/', views.AjaxPostImport.as_view(), name='ajax_import'),
    # インポートのテスト
    path('test_import/', views.TestPostImport.as_view(), name='test_import'),

    path('file_delete/', views.file_delete, name='file_delete'),
    path('efile_delete/', views.efile_delete, name='efile_delete'),


    # エクスポート
    path('export/', views.post_export, name='export'),

    # CSVインポート用テンプレートダウンロード
    path('template/', views.template_download, name='template'),

    #削除
    path('delete/', views.PostDelete.as_view(), name='delete'),
    #削除
    path('test_delete/', views.TestPostDelete.as_view(), name='test_delete'),

    #更新
    path('ajax_update/', views.PostUpdate.as_view(), name='ajax_update'),
    #更新のテスト
    path('test_update/', views.TestPostUpdate.as_view(), name='test_update'),
]