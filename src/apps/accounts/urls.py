from django.urls import path, include
from . import views

"""
app_nameを定義することで、テンプレートから"manager:<nameに定義した値>"という
形でURLを指定できる。
そうすることでどのアプリのURLを指定しているかがわかり、アプリをまたいで同じpathを
指定した場合、重複を防げる。
"""
app_name = 'accounts'


urlpatterns = [
    # """
    # ホーム画面
    # """
    path('',views.HomeTemplateView.as_view(),name='home'),
    # """
    # ヘルプ
    # """
    path('help/', views.HelpView.as_view(), name='help'),
    # """
    # ユーザー管理画面
    # """
    #管理ユーザー情報
    path('user_infomation/', views.UserInfoView.as_view(), name='user_infomation'),
    # 管理ユーザー情報変更
    path('update_userinfomation/<uuid:pk>', views.UserUpdateInfoView.as_view(), name='update_userinfomation'),

    # ユーザー一覧
    path('user/', views.UserIndexView.as_view(), name='user'),
    #ユーザー表示設定
    path('user/<int:pk>/user_settings/', views.UserSettingsView.as_view(), name='user_settings'),
    #path('use/user_settings/middle_choice', views.MiddleChoiceAjaxView.as_view(), name='middle_choice'),
    # # ユーザー詳細
    # path('user/<uuid:pk>', views.UserDetailView.as_view(), name='user_detail'),
    #　ユーザー変更
    path('user/<uuid:pk>/user_update/', views.UserUpdateView.as_view(), name='user_update'),

    # 一般ユーザーの仮登録（管理者が実行）
    path('user_create/', views.UserCreateView.as_view(), name='user_create'),
    path('user_create/done', views.UserCreateDone.as_view(), name='user_create_done'),
    #　一般ユーザーの本登録
    path('user_create/<token>/', views.UserCreateComplete.as_view(), name='user_create_complete'),
    # 一般ユーザーが本登録時にパスワードを設定
    path('user_create/setpassword/<uuid:pk>/', views.UserCreateSetpassword.as_view(), name='user_create_setpassword'),
    path('user_create/setpassword/done', views.UserCreateSetpasswordDone.as_view(), name='user_create_setpassword_done'),
    #ユーザー無効化用
    path('user/deactive_user/', views.UserDeactive.as_view(), name='deactive_user'),
    #ユーザー有効化用
    path('user/active_user/', views.UserActive.as_view(), name='active_user'),

    # 一般ユーザー削除用
    path('user/delete/', views.UserDelete.as_view(), name='user_delete'),

    # ユーザー向けのリンク再発行
    path('user/<uuid:pk>/link_reissue/', views.UserLinkReissueView.as_view(), name='link_reissue'),

    # 管理者が一般ユーザーのパスワードを変更
    path('user_change/password/<uuid:pk>/', views.UserChangePassword.as_view(), name='user_chenge_password'),
    path('user_change/password/done', views.UserChangePasswordDone.as_view(), name='user_chenge_password_done'),


    path('load_admin_count/', views.load_admin_count, name='load_admin_count'),

    # サムネイル(写真の削除)
    path('delete_thumbnail', views.DeleteThumbnailAjaxView.as_view(), name='delete_thumbnail'),


    # """
    # 初めての方はこちら(管理者登録)
    # """
    # 管理者の仮登録
    path('user_registration/', views.UserRegistration.as_view(), name='user_registration'),
    path('user_registration/done', views.UserRegistrationDone.as_view(), name='user_registration_done'),

    # 管理者の本登録
    path('user_registration/complete/<token>/', views.UserRegistrationComplete.as_view(), name='user_registration_complete'),

    # 管理者の本登録時追加情報入力
    path('user_reg/<uuid:pk>/', views.UserRegistrationAddinfo.as_view(), name='user_registration_addinfo'),
    path('user_registration/addinfo/done', views.UserRegistrationAddinfoDone.as_view(), name='user_registration_addinfo_done'),

    #会社の登録状況確認
    path('company_confirm/', views.CompanyConfirm.as_view(), name='company_confirm'),
    path('company_confirm_done/', views.CompanyConfirmDone.as_view(), name='company_confirm_done'),


    # """
    # パスワードを忘れた方
    # """
    # ユーザーのパスワードリセット（ログイン画面にて）
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),

    # """
    # ログイン・ログアウト
    # """
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),

    # ゲストユーザーログイン・ログアウト
    path('guest_user_login/', views.GuestUserLogin.as_view(), name='guest_user_login'),
    path('guest_user_logout/', views.GuestUserLogout.as_view(), name='guest_user_logout'),

    # 会社情報
    path('companyprofile/',views.CompanyProfile.as_view(),name='companyprofile'),
    path('companyprofile/<int:pk>/update_companyprofile/', views.CompanyprofileUpdateView.as_view(), name='update_companyprofile'),
    path('companyprofile/middle_choice', views.MiddleChoiceAjaxView.as_view(), name='middle_choice'),

    #問い合わせ
    path('contact/', views.ContactFormView.as_view(), name='contact'),
    path('contact_done/', views.ContactDoneView.as_view(), name='contact_done'),

    # 共通
    path('cancel/<int:pk>/<str>',views.Cancel.as_view(),name='cancel'),
    path('reset_session/',views.ResetSession.as_view(),name='reset_session'),


    # リマインダー閲覧チェック
    path('notif_status/', views.NotificationStatus.as_view(), name='notif_status'),



    # サーバー設定
    # path('server_setting/', views.ServerSettingView.as_view(), name='server_setting'),
    # サーバー設定変更
    # path('update_server_setting/', views.ServerSettingUpdateView.as_view(), name='update_server_setting'),




]
