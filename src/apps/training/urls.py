from django.urls import path, include
from . import views
# from . import settings

from django.conf.urls.static import static
from django.conf import settings

"""
app_nameを定義することで、テンプレートから"manager:<nameに定義した値>"という
形でURLを指定できる。
そうすることでどのアプリのURLを指定しているかがわかり、アプリをまたいで同じpathを
指定した場合、重複を防げる。
"""
app_name = 'training'

# if not settings.DEBUG:
#     STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
#     # AWS_ACCESS_KEY_ID = env('AWS_ACCESS_')

urlpatterns = [
    # """
    # ホーム画面 トレー二ング一覧
    # """
    # path('', views.TrainingTemplateView.as_view(),name='training'),

    # ホーム画面 コース一覧
    # path('subject/',views.SubjectTemplateView.as_view(),name='subject'),
    path('', views.SubjectTemplateView.as_view(), name='training'),

    # コースに紐づいているトレーニングの一覧が表示される
    path('subject_training/<uuid:pk>/',views.SubjectTrainingTemplateView.as_view(),name='subject_training'),

    # ゲストユーザー用
    path('guest_training/',views.GuestTemplateView.as_view(),name='guest_training'),

    # トレーニングの完了非表示
    path('training_done_chg/', views.TrainingDoneChgAjaxView.as_view(), name='training_done_chg'),

    # トグルボタン展開縮小の制御
    path('folder_is_open_change/', views.FolderIsOpenChangeAjaxView.as_view(), name='folder_is_open_change'),


    # """
    # 動画
    # """
    # path('movie/<uuid:pk>/<uuid:training_id>',views.MovieTemplateView.as_view(),name='movie'),
    path('movie/<uuid:pk>/',views.MovieTemplateView.as_view(),name='movie'),

    # """
    # テスト(試験)
    # """
    path('test/<uuid:pk>',views.TestView.as_view(),name='test'),
    path('test_confirm/<uuid:pk>',views.TestConfirmView.as_view(),name='test_confirm'),
    path('test_done/<uuid:pk>',views.TestDoneView.as_view(),name='test_done'),

    # """
    # アンケート
    # """
    path('questionnaire/<uuid:pk>',views.QuestionnaireTemplateView.as_view(),name='questionnaire'),
    path('questionnaire_confirm/<uuid:pk>',views.QuestionnaireConfirmView.as_view(),name='questionnaire_confirm'),
    path('questionnaire_done/',views.QuestionnaireDoneView.as_view(),name='questionnaire_done'),

    # 配布ファイルダウンロードの情報を取得
    path('file_download_status', views.FileDownloadStatus.as_view(), name='file_download_status'),

    # 動画再生情報を取得
    path('movie_play_status', views.MoviePlayStatus.as_view(), name='movie_play_status'),

    # 配布ファイルのZipダウンロード
    path('file_download_zip/<uuid:pk>/', views.FileDownloadZipView.as_view(), name='file_download_zip'),


    # ユーザー状況エクスポート
    path('user_status/<uuid:pk>/', views.UserStatusView.as_view(), name='user_status'),

    # アンケートエクスポート
    path('user_questionnaire/<uuid:pk>/', views.UserQuestionnaireView.as_view(), name='user_questionnaire'),

    # テストエクスポート
    path('user_question/<uuid:pk>/', views.UserQuestioneView.as_view(), name='user_question'),

    # 管理者権限設定ページ、権限付与
    path('user_management/',views.UserManagementView.as_view(),name='user_management'),

    # 権限の個別削除
    path('is_staff_delete/<uuid:pk>/',views.IsStaffDeleteView.as_view(),name='is_staff_delete'),

    # 共同管理者権限設定ページ、権限付与
    path('co_admin_management/',views.CoAdminManagementView.as_view(),name='co_admin_management'),

    # 権限の個別削除
    path('co_admin_user_delete/<uuid:pk>/',views.CoAdminUserDeleteView.as_view(),name='co_admin_user_delete'),

    # ゲストユーザー設定ページ
    path('guest_user_management/',views.GuestUserManagementView.as_view(),name='guest_user_management'),

    # ゲストユーザー登録
    path('guest_user_create/',views.GuestUserCreateView.as_view(),name='guest_user_create'),

    # ゲストユーザーの変更
    path('guest_user_update/<uuid:pk>/', views.GuestUserUpdateView.as_view(), name='guest_user_update'),

    # ゲストユーザーのパスワード変更
    path('password_update/<uuid:pk>/', views.PasswordUpdate.as_view(), name='password_update'),

    # ゲストユーザーの個別削除
    path('guest_user_delete/<uuid:pk>/',views.GuestUserDeleteView.as_view(),name='guest_user_delete'),

    # ゲストユーザーの削除(一括)
    path('all_guest_user_delete/', views.AllGuestUserDeleteView.as_view(), name='all_guest_user_delete'),

    # ゲストユーザーに紐づいているトレーニングの一覧
    path('training_link/<uuid:pk>/', views.TrainingLinkView.as_view(), name='training_link'),

    # ゲストユーザーに紐づいているトレーニングの削除(個別)
    path('training_link_delete/<uuid:pk>/', views.TrainingLinkDeleteView.as_view(), name='training_link_delete'),

    # ゲストユーザーに紐づいているトレーニングの削除(一括)
    path('training_all_delete/', views.TrainingAllDeleteView.as_view(), name='training_all_delete'),

    # 受講履歴
    path('training_history',views.TrainingHistoryView.as_view(),name='training_history'),

    # アプリ管理ページ
    path('app_admin/',views.AppAdminView.as_view(),name='app_admin'),

    # 円グラフに値を渡す
    # path('get_pie_data/<uuid:pk>/', views.GetPieDataAjaxView.as_view(), name='get_pie_data'),
    path('get_pie_data/', views.GetPieDataAjaxView.as_view(), name='get_pie_data'),

    # CSVモーダル(Training)
    path('get_csv_training_modal/', views.GetCsvTrainingAjaxView.as_view(), name='get_csv_training_modal'),

    # 未提出者リマインダー
    path('reminder/<uuid:pk>/', views.ReminderView.as_view(), name='reminder'),

    # リマインダー閲覧チェック
    path('notif_status/', views.NotificationStatus.as_view(), name='notif_status'),

    # インポート
    path('import/', views.PostImport.as_view(), name='import'),

    # リソース状況
    path('resource_management/',views.ResourceManagementView.as_view(),name='resource_management'),

    # トレーニング作成ページ
    # path('register_training/', views.RegisterIncidentAjaxView.as_view(),name='register_training'),
    path('training_create/', views.TrainingCreateView.as_view(), name='training_create'),

    # 続けて設問を作成しない場合の処理(トレーニング詳細設定)
    path('cancel_parts_register/<uuid:pk>', views.CancelPartsRegisterView.as_view(), name='cancel_parts_register'),

    # 戻るボタン押下時の処理
    path('return/', views.ReturnView.as_view(), name='return'),

    # トレーニング管理ページ
    path('training_management/', views.TrainingManagementView.as_view(), name='training_management'),

    # 完了したトレーニングの表示・非表示
    path('training_done/', views.TrainingDoneAjaxView.as_view(), name='training_done'),

    # パーツ並び替え画面
    # path('parts_create_top/', views.PartsCreateTopView.as_view(), name='parts_create_top'),
    # path('parts_create_top/<uuid:pk>/', views.PartsCreateTopView.as_view(), name='parts_create_top'),
    path('parts_sorting/<uuid:pk>/', views.PartsCreateTopView.as_view(), name='parts_sorting'),


    # パーツ作成 Ajax処理
    path('parts_create/', views.PartsCreateAjaxView.as_view(), name='parts_create'),

    # テストパーツ作成
    # path('test_parts_create/<uuid:pk>/<int:order>/', views.TestPartsCreateView.as_view(), name='test_parts_create'),
    path('test_parts_create/<uuid:pk>/', views.TestPartsCreateView.as_view(), name='test_parts_create'),

    # テストパーツ作成の説明ウィンドウ
    path('test_parts_create_help/', views.TestPartsCreateHelpView.as_view(), name='test_parts_create_help'),

    # アンケートパーツ作成
    # path('questionnaire_parts_create/<uuid:pk>/<int:order>/', views.QuestionnairePartsCreateView.as_view(), name='questionnaire_parts_create'),
    path('questionnaire_parts_create/<uuid:pk>/', views.QuestionnairePartsCreateView.as_view(), name='questionnaire_parts_create'),

    # 動画パーツ作成
    # path('movie_parts_create/<uuid:pk>/<int:order>/', views.MoviePartsCreateView.as_view(), name='movie_parts_create'),
    path('movie_parts_create/<uuid:pk>/', views.MoviePartsCreateView.as_view(), name='movie_parts_create'),


    # 動画アップロード
    path('movie_upload/', views.MovieUploadView.as_view(), name='movie_upload'),


    # ファイルパーツ作成
    # path('file_parts_create/<uuid:pk>/<int:order>/', views.FilePartsCreateView.as_view(), name='file_parts_create'),
    path('file_parts_create/<uuid:pk>/', views.FilePartsCreateView.as_view(), name='file_parts_create'),

    # ファイルアップロード
    path('file_upload/', views.FileUploadView.as_view(), name='file_upload'),

    # ポスターアップロード
    path('poster_upload/', views.PosterUploadView.as_view(), name='poster_upload'),

    # 画像アップロード
    path('image_upload/', views.ImageUploadView.as_view(), name='image_upload'),


    # アンケートの作成画面
    path('questionnaire_register/<uuid:pk>/', views.QuestionnaireRegisterView.as_view(), name='questionnaire_register'),
    # path('questionnaire_register/', views.QuestionnaireRegisterView.as_view(), name='questionnaire_register'),

    # アンケートの設問管理
    path('questionnaire_management/<uuid:pk>/', views.QuestionnairManagementView.as_view(), name='questionnaire_management'),

    # アンケートの設問、選択肢の変更
    path('questionnaire_update/<int:pk>/', views.QuestionnaireUpdateView.as_view(), name='questionnaire_update'),

    # アンケートの設問、選択肢の削除
    path('questionnaire_delete/<int:pk>/', views.QuestionnaireDeleteView.as_view(), name='questionnaire_delete'),

    # アンケートの設問の並び替え画面
    path('questionnaire_sort_top/<uuid:pk>/', views.QuestionnaireSortTopView.as_view(), name='questionnaire_sort_top'),

    # アンケートの設問の並び替え画面
    path('questionnaire_sort_done/', views.QuestionnaireSortDoneView.as_view(), name='questionnaire_sort_done'),


    # テストの設問作成画面
    path('question_register/<uuid:pk>/', views.QuestionRegisterView.as_view(), name='question_register'),
    # path('question_register/', views.QuestionRegisterView.as_view(), name='question_register'),

    # テストの設問管理
    path('question_management/<uuid:pk>/', views.QuestionManagementView.as_view(), name='question_management'),

    # テストのパーツの変更
    path('test_parts_update/<uuid:pk>/', views.TestPartsUpdateView.as_view(), name='test_parts_update'),

    # テストの設問、選択肢の変更
    path('question_update/<int:pk>/', views.QuestionUpdateView.as_view(), name='question_update'),

    # テストの設問、選択肢の変更
    # path('question_update2/<int:pk>/', views.QuestionUpdateView2.as_view(), name='question_update2'),

    # テストの設問、選択肢の削除
    path('question_delete/<int:pk>/', views.QuestionDeleteView.as_view(), name='question_delete'),

    # テストの設問の並び替え画面
    path('question_sort_top/<uuid:pk>/', views.QuestionSortTopView.as_view(), name='question_sort_top'),

    # テストの設問の並び替え Ajax処理
    path('question_sort_done/', views.QuestionSortDoneAjaxView.as_view(), name='question_sort_done'),

    # カスタムグループ管理画面
    path('customgroup_management/', views.CustomGroupManagementView.as_view(), name='customgroup_management'),

    # コース管理画面
    path('subject_management/', views.SubjectManagementView.as_view(), name='subject_management'),

    # コース作成
    path('subject_management_create/', views.SubjectManagementCreateView.as_view(), name='subject_management_create'),

    # コース変更
    path('subject_management_update/<uuid:pk>/', views.SubjectManagementUpdateView.as_view(), name='subject_management_update'),

    # コース削除
    path('subject_delete/<uuid:pk>/', views.SubjectDeleteView.as_view(), name='subject_delete'),

    # コース一括削除
    path('all_subject_delete/', views.AllSubjectDeleteView.as_view(), name='all_subject_delete'),

    # コース、ポスターアップロード
    path('subject_poster_upload/', views.SubjectPosterUploadView.as_view(), name='subject_poster_upload'),

    # コース、ポスター削除
    path('subject_poster_delete/', views.SubjectPosterDeleteView.as_view(), name='subject_poster_delete'),


    # コースに登録されているトレーニングが5件以上で表示するボタン
    path('training_list/<uuid:pk>', views.TrainingListView.as_view(), name='training_list'),


    # カスタムグループ作成
    # path('customgroup_create/', views.CustomGroupCreateView.as_view(), name='customgroup_create'),
    path('input_customgroup/', views.CustomGroupCreateView.as_view(), name='input_customgroup'),

    # カスタムグループ編集(新規トレーニング作成)
    path('customgroup_group_update/<uuid:pk>', views.CustomGroupUpdateView.as_view(), name='customgroup_group_update'),

    # カスタムグループ編集(グループ一覧)
    # path('customgroup_group_update_grplist/<uuid:pk>', views.CustomGroupUpdateGrplistView.as_view(), name='customgroup_group_update_grplist'),

    # カスタムグループ作成（メールアドレス）
    path('customgroup_bulk_create/', views.CustomGroupBulkCreateView.as_view(), name='customgroup_bulk_create'),

    # カスタムグループ詳細
    path('destination_group_detail/<uuid:pk>', views.DestinationGroupDetailView.as_view(), name='destination_group_detail'),

    # カスタムグループ削除(個別)
    path('customgroup_delete/<uuid:pk>', views.CustomgroupDeleteView.as_view(), name='customgroup_delete'),

    # カスタムグループ削除(一括)
    path('all_customgroup_delete/', views.AllCustomgroupDeleteView.as_view(), name='all_customgroup_delete'),

    # トレーニング変更管理画面
    # 全て表示
    path('training_change_management_all/', views.TrainingChangeManagementView.as_view(), name='training_change_management_all'),

    # 未対応
    path('training_change_management_waiting/', views.TrainingChangeManagementWaitingView.as_view(), name='training_change_management_waiting'),

    # 対応中
    path('training_change_management_working/', views.TrainingChangeManagementWorkingView.as_view(), name='training_change_management_working'),

    # 完了
    path('training_change_management_done/', views.TrainingChangeManagementDoneView.as_view(), name='training_change_management_done'),

    # トレーニング詳細設定
    path('training_edit_menu/<uuid:pk>', views.TrainingEditMenulView.as_view(), name='training_edit_menu'),

    # 続けて設問を作成しない場合の処理(トレーニング詳細設定)
    path('cancel_question_register/<uuid:pk>', views.CancelQuestionRegisterView.as_view(), name='cancel_question_register'),

    # 続けて設問を作成しない場合の処理(トレーニング詳細設定)
    path('cancel_questionnaire_register/<uuid:pk>', views.CancelQuestionnaireRegisterView.as_view(), name='cancel_questionnaire_register'),

    # 続けてボタン有効化制御の設定をしない場合の処理(トレーニング詳細設定)
    path('cancel_button_activate_ctl_register/<uuid:pk>', views.CancelButtonActivateCtlRegisterView.as_view(), name='cancel_button_activate_ctl_register'),

    # トレーニング編集画面
    path('training_edit_menu/<uuid:pk>', views.TrainingEditMenulView.as_view(), name='training_edit_menu'),

    # トレーニング削除
    path('training_delete/<uuid:pk>', views.TrainingDeleteView.as_view(), name='training_delete'),

    # トレーニング変更
    path('training_update/<uuid:pk>', views.TrainingUpdateView.as_view(), name='training_update'),

    # グループの変更を行った場合、トレーニング変更画面に値を渡す
    path('group_edit_check_ajax/<uuid:pk>/', views.GroupEditCheckAjaxView.as_view(), name='group_edit_check_ajax'),


    # 戻るボタン押下時の処理
    path('return_training_update/<uuid:pk>', views.ReturnTrainingUpdateView.as_view(), name='return_training_update'),

    # トレーニングの複製
    path('training_copy/<uuid:pk>', views.TrainingCopyView.as_view(), name='training_copy'),


    # ボタン制御 / 制御条件登録画面
    path('button_activate_ctl/<uuid:pk>/', views.ButtonActivateCtlView.as_view(), name='button_activate_ctl'),
    # path('button_activate_ctl/', views.ButtonActivateCtlView.as_view(), name='button_activate_ctl'),

    # ボタン制御 / 制御条件編集画面
    # path('button_activate_ctl_edit/<uuid:pk>/', views.ButtonActivateCtlEditView.as_view(), name='button_activate_ctl_edit'),

    # ボタン制御 / 制御条件編集画面に値を渡す
    path('button_activate_ctl_edit_ajax/<uuid:pk>/', views.ButtonActivateCtlEditAjaxView.as_view(), name='button_activate_ctl_edit_ajax'),

    # ボタン制御の登録処理 Ajax
    path('button_activate_ctl_update/', views.ButtonActivateCtlUpdateView.as_view(), name='button_activate_ctl_update'),

    # 制御条件の登録処理 Ajax
    path('control_conditions_update/', views.ControlConditionsUpdateView.as_view(), name='control_conditions_update'),






    # パーツ削除
    path('parts_delete/<uuid:pk>', views.PartsDeleteView.as_view(), name='parts_delete'),

    # テストパーツ変更
    path('parts_test_update/<uuid:pk>', views.PartsTestUpdateView.as_view(), name='parts_test_update'),

    # アンケートパーツ変更
    path('parts_questionnaire_update/<uuid:pk>', views.PartsQuestionnaireUpdateView.as_view(), name='parts_questionnaire_update'),

    # 動画パーツ変更
    path('parts_movie_update/<uuid:pk>', views.PartsMovieUpdateView.as_view(), name='parts_movie_update'),

    # ファイルパーツ変更
    path('parts_file_update/<uuid:pk>', views.PartsFileUpdateView.as_view(), name='parts_file_update'),

    # ポスター削除
    path('poster_delete/', views.PosterDeleteView.as_view(), name='poster_delete'),

    # 画像の削除
    path('image_delete/', views.ImageDeleteView.as_view(), name='image_delete'),


    # ファイル削除 C:\Users\user\Dropbox\08.開発\training_pj\config\settings\local.py
    path('file_delete/', views.FileDeleteView.as_view(), name='file_delete'),

    # テストの設問変更 選択肢の削除
    path('choice_delete/', views.ChoiceDeleteView.as_view(), name='choice_delete'),

    # アンケートの設問変更 選択肢の削除
    path('questionnairechoice_delete/', views.QuestionnaireChoiceDeleteView.as_view(), name='questionnairechoice_delete'),

    # ユーザー一覧(ユーザーアサインモーダル用)
    # path('user_list/<uuid:pk>/', views.UserListAjaxView.as_view(), name='user_list'),
    path('member_list/<uuid:pk>', views.MemberListView.as_view(), name='member_list')



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
