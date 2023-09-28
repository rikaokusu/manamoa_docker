from django.contrib import admin

from .models import Training, File, FileManage, TrainingRelation
from .models import Question, Choice
from .models import QuestionnaireQuestion, QuestionnaireChoice
from .models import QuestionnaireResult
# テスト結果登録モデルを追加
from .models import QuestionResult
from .models import Parts, PartsManage
# from .models import Notification
from .models import TrainingManage
from .models import Test
from .models import Movie
from .models import Poster
from .models import Image
from .models import CustomGroup
from .models import ControlConditions
from .models import TrainingHistory
from .models import ResourceManagement
from .models import FolderIsOpen
from .models import CoAdminUserManagement
from .models import GuestUserManagement
from .models import SubjectManagement
from .models import SubjectImage
from .models import TrainingDoneChg
from .models import TrainingDone
from .models import UserCustomGroupRelation
from .models import CoAdminUserManagementRelation

# CSV imoprt
from import_export import resources
from import_export.admin import ImportExportModelAdmin


"""
完了フラグ
"""
class TrainingDoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'is_training_done')
    list_display_links = ('id', 'user_id', 'is_training_done')


"""
トレーニングの表示の切り替え
"""
class TrainingDoneChgAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'is_training_done_chg', 'subject')
    list_display_links = ('id', 'user_id', 'is_training_done_chg')


"""
コースの画像
"""
class SubjectImageResource(admin.ModelAdmin):
    list_display = ('id', 'subject_image', 'name', 'image_id', 'size')
    list_display_links = ('id', 'name',)

"""
コース管理テーブル
"""
class SubjectManagementAdmin(admin.ModelAdmin):
    # list_display = ('id', 'subject_name', 'subject_reg_user', '_subject_reg_training')
    list_display = ('id', 'subject_name', 'subject_reg_user', 'subject_reg_company', 'target', 'objective', 'duration', 'created_subject_date', 'subject_image')
    list_display_links = ('id',)

    # def _subject_reg_training(self, row):
    #     return ','.join([x.title for x in row.subject_reg_training.all()])


"""
ゲストユーザー設定テーブル
"""
class GuestUserManagementAdmin(admin.ModelAdmin):
    list_display = ('id', 'resister_user', 'guest_user_name', 'email', 'company_name', 'guest_user_password',
    'resister_date', 'is_active','is_rogical_deleted', 'last_login', 'is_training_done_chg', 'is_send_mail', 'color_num',
    'origin', 'thumbnail', 'small')
    # list_display = ('id', 'resister_user', 'guest_user_name', 'email', 'company_name', 'guest_user_password',
    #  'last_login', 'is_training_done_chg', 'is_send_mail', 'color_num', 'origin', 'thumbnail', 'small')
    list_display_links = ('id',)



"""
共同管理者管理(自作中間テーブル)
"""
class CoAdminUserManagementRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'admin_user_id', 'co_admin_user_id')
    list_display_links = ('id', 'admin_user_id', 'co_admin_user_id')


"""
共同管理者管理テーブル
"""
class CoAdminUserManagementAdmin(admin.ModelAdmin):
    # list_display = ('admin_user', '_co_admin_user')
    list_display = ('id', 'admin_user',)
    list_display_links = ('id', 'admin_user')

    # def _co_admin_user(self, row):
    #     return ','.join([x.display_name for x in row.co_admin_user.all()])


"""
リソース管理テーブル
"""
class FolderIsOpenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'training', 'is_open')
    list_display_links = ('id',)


"""
リソース管理テーブル
"""
class ResourceManagementyAdmin(admin.ModelAdmin):
    list_display = ('id', 'reg_company_name', 'number_of_training', 'number_of_file', 'total_file_size')
    list_display_links = ('id',)

"""
受講履歴テーブル
"""
class TrainingHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'training', 'title', 'description', 'reg_user', 'start_date','end_date', 'done_date', 'user', 'guest_user_history', 'status', 'del_flg')
    list_display_links = ('id',)


"""
カスタムグループテーブル(自作中間テーブル)
"""
class UserCustomGroupRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'group_id', 'group_user', 'tentative_group_flg')
    list_display_links = ('id', 'group_id', 'group_user', 'tentative_group_flg')


"""
カスタムグループテーブル
"""
class CustomGroupAdmin(admin.ModelAdmin):
    # list_display = ('id', 'name', 'group_reg_user', 'reg_date', '_group_user')
    list_display = ('id', 'name', 'group_reg_user', 'reg_date')
    list_display_links = ('id',)

    # def _group_user(self, row):
    #     return ','.join([x.display_name for x in row.group_user.all()])


"""
テスト
"""
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'title')
    list_display_links = ('id',)

"""
テストの画像
"""
class ImageResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = Image
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('image', 'name', 'image_id')


"""
テストの画像
"""
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'name', 'image_id', 'size')
    list_display_links = ('id', 'name',)

    resource_class = ImageResource


    # def _image(self, row):
    #     return ','.join([x.name for x in row.image.all()])


"""
ポスター
"""
class PosterAdmin(admin.ModelAdmin):
    list_display = ('poster', 'name', 'poster_id', 'size')
    list_display_links = ('poster',)

"""
動画
"""
class MovieAdmin(admin.ModelAdmin):
    list_display = ('movie', 'name', 'movie_id', 'size')
    list_display_links = ('movie',)

"""
CSVのインポート・エクスポート
"""
class TrainingResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = Training
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('title', 'description',)


class PartsResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = Parts
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('order', 'type', 'movie', 'title', 'description', 'poster', 'file_id', 'duration', 'pass_line', 'pass_text1', 'pass_text2', 'unpass_text1', 'unpass_text2', 'is_required', 'file', 'file_desc',)


class QuestionResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = Question
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('parts', 'text', 'order', 'is_multiple', 'question_register_user')


class ChoiceResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = Choice
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('question', 'text', 'is_correct', 'order',)


class QuestionnaireQuestionResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = QuestionnaireQuestion
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('parts', 'text', 'order', 'is_multiple', 'is_type', 'is_multiple_questionnaire', 'questionnair_register_user')


class QuestionnaireChoiceResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = QuestionnaireChoice
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('question', 'text', 'order',)

class FileResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = File
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('file', 'name', 'file_id')


""""-----------------------------"""

"""
トレーニングテーブル(自作中間テーブル)
"""
class TrainingRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'group_id', 'training_id')
    list_display_links = ('id',)


# class TrainingAdmin(admin.ModelAdmin):
class TrainingAdmin(ImportExportModelAdmin):
    list_display = ('id', 'title', 'description', 'reg_user', 'period_date', 'is_open', 'status', '_parts', 'expired_training_flg', '_destination_guest_user', 'subject', 'group_edit_check_flg')
    # list_display = ('id', 'title', 'description', 'reg_user', 'period_date', 'is_open', 'status', '_parts', '_destination_group', 'expired_training_flg', '_destination_guest_user', 'subject')

    list_display_links = ('id',)

    # def _file(self, row):
    #     return ','.join([x.name for x in row.file.all()])

    # def _movie(self, row):
    #     return ','.join([x.title for x in row.movie.all()])

    # def _test(self, row):
    #     return ','.join([x.title for x in row.test.all()])

    def _parts(self, row):
        return ','.join([x.title for x in row.parts.all()])

    # def _destination_group(self, row):
    #     return ','.join([x.name for x in row.destination_group.all()])

    # def _destination_user(self, row):
    #     return ','.join([x.display_name for x in row.destination_user.all()])

    def _destination_guest_user(self, row):
        return ','.join([x.guest_user_name for x in row.destination_guest_user.all()])


    resource_class = TrainingResource

# class PartsAdmin(admin.ModelAdmin):
class PartsAdmin(ImportExportModelAdmin):
    # list_display = ('id', 'order', 'type', 'movie', 'poster' ,'title', 'description', 'title_detail', 'description_detail', 'file_id', 'duration', 'pass_line', 'pass_text1', 'pass_text2', 'unpass_text1', 'unpass_text2', 'created_date', 'parts_user','is_question_random', 'control_conditions',)
    list_display = ('id', 'order', 'type', 'movie', 'poster' ,'title', 'description', 'title_detail', 'description_detail', 'file_id', 'duration', 'pass_line', 'pass_text1', 'pass_text2', 'unpass_text1', 'unpass_text2', 'created_date', 'parts_user','is_question_random',)

    list_display_links = ('id',)

    resource_class = PartsResource


# class FileAdmin(admin.ModelAdmin):
class FileAdmin(ImportExportModelAdmin):
    list_display = ('id', 'file', 'name', 'file_id', 'size')
    list_display_links = ('id', 'name',)

    resource_class = FileResource

class PartsManageAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'type', 'parts', 'user', 'parts_manage_guest_user', 'period_date', 'status', '_file_manage', 'play_start_date', 'movie_duration', 'movie_file_id', 'expected_end_date', 'current_time', '_questionnaire_result', '_question_result', 'del_parts_manage_flg')
    list_display_links = ('id',)
    # search_fields = ('user__display_name', 'parts__title')
    search_fields = ('user', 'parts__title')
    list_filter = ('type', 'status',)

    def _file_manage(self, row):
        return ','.join([str(x.file_id) for x in row.file_manage.all()])

    def _questionnaire_result(self, row):
        return ','.join([str(x.question) + ":" + str(x.answer) for x in row.questionnaire_result.all()])

    # テスト結果保存用に追加
    def _question_result(self, row):
        return ','.join([str(x.question) + ":" + str(x.answer) for x in row.question_result.all()])



# class NotificationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'release_date', 'title', 'category', 'target_user', 'is_read')
#     list_display_links = ('id',)

class TrainingManageAdmin(admin.ModelAdmin):
    list_display = ('id', 'training', 'user', 'guest_user_manage', 'status', 'done_date', 'subject_manage', '_parts_manage',)
    list_display_links = ('id', 'training', 'status', 'done_date', 'subject_manage')

    def _parts_manage(self, row):
        return ','.join([str(x.parts) for x in row.parts_manage.all()])


class FileManageAdmin(admin.ModelAdmin):
    list_display = ('id', 'download_date', 'is_done', 'file_id',)
    list_display_links = ('id', 'download_date', 'is_done',)


# class TestAdmin(admin.ModelAdmin):
#     list_display = ('id', 'title', 'description', 'pass_text1', 'pass_text2' , 'unpass_text1', 'unpass_text2',)
#     list_display_links = ('id', 'title', 'description',)

class ChoiceInline(admin.StackedInline):
    model = Choice
    extra = 3

# class ChoiceAdmin(admin.ModelAdmin):
class ChoiceAdmin(ImportExportModelAdmin):
    list_display = ('id', 'order', 'text', 'is_correct',)
    list_display_links = ('id', 'text',)

    resource_class = ChoiceResource

# class QuestionAdmin(admin.ModelAdmin):
class QuestionAdmin(ImportExportModelAdmin):
    list_display = ('id', 'text', 'order', 'is_multiple', '_image', 'parts', 'number_of_answers',)
    list_display_links = ('id', 'text',)

    inlines = [ChoiceInline]

    resource_class = QuestionResource

    def _image(self, row):
        return ','.join([x.name for x in row.image.all()])



# class QuestionnaireAdmin(admin.ModelAdmin):
#     list_display = ('id', 'title', 'description',)
#     list_display_links = ('id', 'title', 'description',)

class QuestionnaireChoiceInline(admin.StackedInline):
    model = QuestionnaireChoice
    extra = 3

# class QuestionnaireChoiceAdmin(admin.ModelAdmin):
class QuestionnaireChoiceAdmin(ImportExportModelAdmin):
    list_display = ('id', 'order', 'text')
    list_display_links = ('text',)

    resource_class = QuestionnaireChoiceResource

class QuestionnaireQuestionAdmin(ImportExportModelAdmin):
    # list_display = ('id', 'text', 'order', 'is_multiple', 'parts', '_image', 'is_multiple_questionnaire')
    list_display = ('id', 'text', 'order', 'is_multiple', 'parts', '_image', 'is_multiple_questionnaire')

    list_display_links = ('id', 'text',)
    inlines = [QuestionnaireChoiceInline]

    resource_class = QuestionnaireQuestionResource

    def _image(self, row):
        return ','.join([x.name for x in row.image.all()])




# class QuestionnaireManageAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'parts', 'status', '_result')
#     list_display_links = ('id', 'user',)

#     def _result(self, row):
#         return ','.join([str(x.question) + ":" + str(x.answer) for x in row.result.all()])

# アンケート結果
class QuestionnaireResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'questionnairequestion_relation', 'question', 'is_type', 'answer',)
    list_display_links = ('id', 'questionnairequestion_relation', 'question', 'answer',)

# class MoviePlayManageAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'training','period_date' ,'start_date' ,'duration' ,'is_done' ,'file_id' ,'expected_end_date' ,'status' ,'current_time')
#     list_display_links = ('id',)


# テスト結果
class QuestionResultAdmin(admin.ModelAdmin):
    # list_display = ('id', 'question_id', 'question', 'is_type', 'answer',)
    # list_display_links = ('id', 'question_id', 'question', 'answer',)

    list_display = ('id', 'question_relation', 'question', 'is_type', 'answer',)
    list_display_links = ('id', 'question_relation', 'question', 'answer',)


"""
制御条件設定テーブル
"""
class ControlConditionsAdmin(admin.ModelAdmin):
    list_display = ('parts_origin', 'parts_destination')
    list_display_links = ('parts_origin', 'parts_destination')




# テスト結果登録モデル追加
admin.site.register(SubjectImage, SubjectImageResource)
admin.site.register(SubjectManagement, SubjectManagementAdmin)
admin.site.register(QuestionResult, QuestionResultAdmin)
admin.site.register(UserCustomGroupRelation, UserCustomGroupRelationAdmin)
admin.site.register(CustomGroup, CustomGroupAdmin,)
admin.site.register(ControlConditions, ControlConditionsAdmin)
admin.site.register(Image, ImageAdmin,)
admin.site.register(Poster, PosterAdmin,)
admin.site.register(Movie, MovieAdmin,)
admin.site.register(Test, TestAdmin,)
admin.site.register(TrainingRelation, TrainingRelationAdmin)
admin.site.register(Training, TrainingAdmin,)
admin.site.register(File, FileAdmin)
# admin.site.register(Notification, NotificationAdmin)
admin.site.register(FileManage, FileManageAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(QuestionnaireChoice, QuestionnaireChoiceAdmin)
admin.site.register(QuestionnaireQuestion, QuestionnaireQuestionAdmin)
admin.site.register(QuestionnaireResult, QuestionnaireResultAdmin)
admin.site.register(Parts, PartsAdmin)
admin.site.register(PartsManage, PartsManageAdmin)
admin.site.register(TrainingManage, TrainingManageAdmin)
admin.site.register(TrainingHistory, TrainingHistoryAdmin)
admin.site.register(ResourceManagement, ResourceManagementyAdmin)
admin.site.register(FolderIsOpen, FolderIsOpenAdmin)
admin.site.register(CoAdminUserManagementRelation, CoAdminUserManagementRelationAdmin)
admin.site.register(CoAdminUserManagement, CoAdminUserManagementAdmin)
admin.site.register(GuestUserManagement, GuestUserManagementAdmin)
admin.site.register(TrainingDoneChg, TrainingDoneChgAdmin)
admin.site.register(TrainingDone, TrainingDoneAdmin)