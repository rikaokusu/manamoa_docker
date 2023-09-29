from django.db import models

from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.base_user import BaseUserManager
import os
from django.conf import settings

# IDをUUID化
import uuid
from django.db import models

from accounts.models import User
from accounts.models import Company

from django_mysql.models import ListCharField

from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError


# ImageKit
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

STATUS_CHOICE = (
    (1, '未対応'),
    (2, '対応中'),
    (3, '完了'),
)


"""
完了フラグ
"""
class TrainingDone(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.CharField('user_id', max_length=255, blank=True, null=True)

    # 完了フラグ
    is_training_done = models.BooleanField(('is_training_done'), default=False)


# """
# トレーニングの表示の切り替え
# """
# class TrainingDoneChg(models.Model):
#     # id
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     user_id = models.CharField('user_id', max_length=255, blank=True, null=True)

#     # トレーニングの表示の切り替えフラグ
#     is_training_done_chg = models.BooleanField(_('is_training_done_chg'), default=False)


"""
ゲストユーザー設定テーブル
"""
class GuestUserManagement(models.Model):

    # id
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 登録者
    # resister_user = models.ForeignKey(User, verbose_name = _("登録者"), blank=True, null=True, on_delete=models.SET_NULL, related_name='resister_user')
    resister_user = models.CharField('登録者', max_length=255, blank=True, null=True)

    # 登録者の所属する会社
    resister_user_company = models.CharField('登録者の所属する会社', max_length=255, blank=True, null=True)

    # ゲストユーザー名
    guest_user_name = models.CharField('ゲストユーザー名', max_length=30, blank=True, null=True)

    # メールアドレス
    email = models.CharField(_('メールアドレス'), unique=True, max_length=255)

    # 会社名
    company_name = models.CharField('会社名', max_length=100, blank=True, null=True)

    # パスワード
    guest_user_password = models.CharField('パスワード', max_length=255, blank=True, null=True)

    # 作成日
    resister_date = models.DateTimeField(_('登録日'), default=timezone.now)

    # 追加
    last_login = models.DateTimeField(_('last_login'), default=timezone.now)

    # メール送信可否
    is_send_mail = models.BooleanField(_('is_send_mail'), default=True)

    # 色番号
    color_num = models.IntegerField(_('color num'), default=99)

    # 画像のアップロード先を指定
    origin = models.ImageField(upload_to="uploads", default="", null=True, blank=True)

    # オリジンからサムネイル画像を自動生成
    thumbnail = ImageSpecField(source='origin',
                            processors=[ResizeToFill(250,250)],
                            format="JPEG",
                            options={'quality': 60}
                            )

    # オリジンからスモール画像を自動生成
    small = ImageSpecField(source='origin',
                            processors=[ResizeToFill(75,75)],
                            format="JPEG",
                            options={'quality': 50}
                            )

    # トレーニングの表示の切り替え
    is_training_done_chg = models.BooleanField(
        _('is_training_done_chg'),
        default=False,
    )

    # ステータス falseにするとログインできなくなる、Djangoのデフォルトで用意されているもの
    is_active = models.BooleanField(
        _('is_active'),
        default=True,
    )

    # 論理的削除
    is_rogical_deleted = models.BooleanField(
        _('論理的削除'),
        default=False,
    )

    def __str__(self):
        return self.guest_user_name


"""
共同管理者管理(自作中間テーブル)
"""
class CoAdminUserManagementRelation(models.Model):
    # 管理者のID
    admin_user_id = models.CharField('管理者のID', max_length=500, blank=True, null=True)

    # 共同管理者のID
    co_admin_user_id = models.CharField('共同管理者のID', max_length=500, null=True, blank=True)

"""
共同管理者管理テーブル
"""
class CoAdminUserManagement(models.Model):
    # 管理者名
    # admin_user = models.ForeignKey(User, verbose_name = _("管理者名"), blank=True, null=True, on_delete=models.SET_NULL, related_name='admin_user')
    admin_user = models.CharField('管理者名', max_length=255, blank=True, null=True)

    # 共同管理者名
    # co_admin_user = models.ManyToManyField(User, verbose_name = _("共同管理者名"), blank=True, related_name='co_admin_user_name')


"""
リソース管理テーブル
"""
class ResourceManagement(models.Model):
    # 会社
    # reg_company_name = models.ForeignKey(Company, blank=True, null=True, on_delete=models.CASCADE, related_name='reg_company_name')
    reg_company_name = models.CharField(_('会社名'), max_length=225, blank=True, null=True) # 会社のIDの文字列が入る
    number_of_training = models.IntegerField(_('会社に紐づくトレーニング数'), blank=True, null=True, default=0)# トレーニング = 20KB(=20480B)
    number_of_file = models.IntegerField(_('トレーニングの合計サイズ(バイト)'), blank=True, null=True, default=0)
    # トレーニング数×20キロバイトの値
    total_file_size = models.IntegerField(_('会社のディスク使用量(=トレーニングの合計サイズ+ファイルの合計サイズ)'), blank=True, null=True, default=0)


"""
テストテーブル
"""
class Test(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('title'), max_length=30, blank=True)
    order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)

    def __str__(self):
        return self.title


def get_default_subject_image():
    subject_image = SubjectImage.objects.filter(name="default_subject_image").first()
    if subject_image:
        return subject_image.id
    else:
        return None


"""
コースの画像テーブル
"""
class SubjectImage(models.Model):
    subject_image = models.FileField(_('subject_image'), upload_to='uploads/subject_image/', null=True, blank=True)
    name = models.CharField(_('name'), max_length=255, blank=True)
    image_id = models.CharField(_('image_id'), max_length=255, blank=True)
    size = models.CharField(_('size'), max_length=255, blank=True)

    def __str__(self):
        return self.name


"""
テストの画像テーブル
"""
class Image(models.Model):
    image = models.FileField(_('image'), upload_to='uploads/image/', null=True, blank=True)
    name = models.CharField(_('name'), max_length=255, blank=True)
    image_id = models.CharField(_('image_id'), max_length=255, blank=True)
    size = models.CharField(_('size'), max_length=255, blank=True)


    def __str__(self):
        return self.name


"""
ポスターテーブル
"""
class Poster(models.Model):
    poster = models.FileField(_('poster'), upload_to='uploads/poster/', null=True, blank=True)
    name = models.CharField(_('name'), max_length=255, blank=True)
    poster_id = models.CharField(_('poster_id'), max_length=255, blank=True)
    size = models.CharField(_('size'), max_length=255, blank=True)


    def __str__(self):
        return self.name


"""
動画テーブル
"""
class Movie(models.Model):
    movie = models.FileField(_('movie'), upload_to='uploads/movie/', null=True, blank=True)
    name = models.CharField(_('name'), max_length=255, blank=True)
    movie_id = models.CharField(_('movie_id'), max_length=255, blank=True)
    # サイズ
    size = models.CharField(_('size'), max_length=255, blank=True)


    def __str__(self):
        return self.name


"""
ファイルテーブル
"""
class File(models.Model):
    file = models.FileField(_('file'), upload_to='uploads/doc/', null=True, blank=True)
    name = models.CharField(_('name'), max_length=255, blank=True)
    file_id = models.CharField(_('file_id'), max_length=255, blank=True)
    size = models.CharField(_('size'), max_length=255, blank=True)


    def __str__(self):
        return self.name

"""
ファイル管理テーブル
"""
class FileManage(models.Model):
    download_date = models.DateTimeField(_('download date'), blank=True, null=True)
    is_done = models.CharField(_('is_done'), max_length=255, blank=True)
    file_id = models.CharField(_('file_id'), max_length=255, blank=True)


# """
# アンケート結果登録テーブル
# """
# class QuestionnaireResult(models.Model):

#     # 質問
#     question = models.CharField(_('question'), max_length=255, blank=True)

#     # タイプ
#     is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

#     # 回答
#     answer = ListCharField(models.CharField(max_length=1000),size=6, max_length=(6 * 1001), null=True, blank=True)
#     # answer = models.CharField(_('answer'), null=True, blank=True)

#     def __str__(self):
#         return str(self.id)


# """
# テスト結果登録テーブル
# """
# class QuestionResult(models.Model):

#     # 質問
#     question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)

#     # 質問のID
#     question = models.CharField(_('question'), max_length=255, blank=True)
#     # question_id = models.CharField(_('question'), max_length=255, blank=True)

#     # タイプ
#     is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

#     # 回答
#     answer = ListCharField(models.CharField(max_length=1000),size=6, max_length=(6 * 1001), null=True, blank=True)


#     def __str__(self):
#         return str(self.id)


"""
カスタムグループテーブル(自作中間テーブル)
"""
class UserCustomGroupRelation(models.Model):
    # グループのID
    group_id = models.CharField(max_length=255, verbose_name="group_id", null=True, blank=True)

    # グルーピングユーザーのID
    group_user = models.CharField(max_length=500, verbose_name="group_user", null=True, blank=True)

    # 仮生成用のグループの目印
    tentative_group_flg = models.BooleanField(_('仮生成'), default=False)


"""
カスタムグループテーブル
"""
class CustomGroup(models.Model):
    # ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 名前
    name = models.CharField(_('group name'), max_length=255)

    # group_user = models.ManyToManyField(
    #     User, verbose_name="ユーザー",
    #     blank=True,
    #     related_name='group_user')

    # ゲストユーザー
    group_guest_user = models.ManyToManyField(GuestUserManagement, verbose_name="ゲストユーザー", blank=True, related_name='group_guest_user')

    # 登録ユーザー
    # group_reg_user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name='group_reg_user')
    group_reg_user = models.CharField('登録ユーザー', max_length=255, blank=True, null=True)

    # 登録日
    reg_date = models.DateTimeField(_('registration date'), default=timezone.now)

    # テンポラリフラグ
    tempo_flg = models.BooleanField(_('テンポラリフラグ'), default=False)


    def __str__(self):
        return self.name


PARTS_TYPE = (
    (1, 'file'),
    (2, 'movie'),
    (3, 'test'),
    (4, 'questionnaire'),
)


def get_default_poster():
    poster = Poster.objects.filter(name="default_poster").first()
    if poster:
        return poster.id
    else:
        return None


def get_default_subject():
    subject = SubjectManagement.objects.filter(subject_name="デフォルト").first()
    if subject:
        return subject.id
    else:
        return None


"""
パーツ(Test、File、Movie、Questionnaire)テーブル
"""
class Parts(models.Model):
    # ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)         #kyoutuu
    type = models.IntegerField(choices=PARTS_TYPE, default=0)                                       #kyoutuu
    # movie = models.FileField(_('movie'), upload_to='uploads/movie/', null=True, blank=True)
    movie = models.ForeignKey(Movie, null=True, on_delete=models.CASCADE)
    title = models.CharField(_('title'), max_length=30, blank=True)                                 #kyoutuu
    description = models.CharField(_('desc'), blank=True, max_length=255)

    # 各パーツ内に表示するタイトルと説明
    title_detail = models.CharField(_('title_detail'), max_length=255, blank=True)                  #test , anke-to
    description_detail = models.CharField('description_detail', max_length=500, blank=True)         #test , anke-to

    # poster = models.FileField(_('poster'), upload_to='uploads/poster/', null=True, blank=True)      #movie
    poster = models.ForeignKey(Poster, null=True, on_delete=models.SET_DEFAULT, default=get_default_poster)

    file_id = models.CharField(_('file_id'), max_length=255, blank=True)                            #movie
    duration = models.CharField(_('duration'), max_length=255, blank=True)                          #movie
    pass_line = models.IntegerField('pass_line', blank=True, null=True, default=0)
    # pass_line = models.IntegerField('pass_line', blank=True, default=0)                              #test
    pass_text1 = models.CharField('pass_text1', max_length=255, blank=True)                         #test
    pass_text2 = models.CharField('pass_text2', max_length=255, blank=True)                         #test
    unpass_text1 = models.CharField('unpass_text1', max_length=255, blank=True)                     #test
    unpass_text2 = models.CharField('unpass_text2', max_length=255, blank=True)                     #test
    is_required = models.BooleanField(_('is_required'), default=False) # 受講必須を表す               #kyoutuu

    # 配布ファイル
    file = models.ManyToManyField(File, verbose_name = _('file'), blank=True)
    file_desc = models.CharField(_('file_desc'), max_length=255, blank=True)

    # 作成日
    created_date = models.DateTimeField(_('created date'), default=timezone.now, blank=True)

    # 投稿者
    # parts_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='parts_user')
    parts_user = models.CharField('投稿者', max_length=255, blank=True, null=True)

    # ランダムソートON / OFF
    is_question_random = models.BooleanField(_('is_question_random'), default=False,)

    # ボタン有効化制御
    btn_activate_ctl = models.BooleanField(_('ボタン有効化制御'), default=False,)

    # テスト結果の〇✖表記の表示有無
    answer_content_show = models.BooleanField(_('answer_content_show'), default=False,)


    def __str__(self):
        return self.title


ANSWER_TYPE = (
    # (1, 'ラジオボタン'),
    # (2, 'チェックボックス'),
    (1, '多肢選択(正答は1つ)'),
    (2, '多肢選択(正答は2つ以上)'),
    (3, '記述式(完全一致)'),
    (4, '記述式(部分一致)'),
)


"""
テスト質問(設問)テーブル
"""
class Question(models.Model):
    parts = models.ForeignKey(Parts, blank=True, null=True, on_delete=models.CASCADE, related_name='question_parts')
    # parts = models.ManyToManyField(Parts, blank=True, null=True, related_name='question_parts')
    text = models.CharField(_('text'), max_length=500, blank=True)
    order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)
    is_multiple = models.IntegerField(choices=ANSWER_TYPE, verbose_name =_('テスト回答タイプ'), blank=True, null=True, default=0)
    # is_multiple = models.ChoiceField(choices=ANSWER_TYPE, verbose_name =_('テスト回答タイプ'), blank=True, null=True, default=0)
    # 画像の追加
    image = models.ManyToManyField(Image, verbose_name = _('画像'), blank=True)
    # 回答数の設定
    number_of_answers = models.IntegerField(verbose_name =_('number_of_answers'), blank=True, null=True, default=0)
    # 投稿者
    # question_register_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='question_register_user')
    question_register_user = models.CharField('投稿者', max_length=255, blank=True, null=True)
    def __str__(self):
        return self.text


"""
テスト選択肢テーブル
"""
class Choice(models.Model):
    # question = models.ForeignKey(Question, blank=True, null=True, on_delete=models.CASCADE, related_name='question')
    question = models.ForeignKey(Question, blank=True, null=True, on_delete=models.CASCADE)

    text = models.CharField(_('text'), max_length=120, blank=True)

    # チェックボックス、完全 / 部分一致
    # is_correct = models.BooleanField(_('is_correct'), choices=BOOL_CHOICES, default=False, null=True, blank=True)
    is_correct = models.BooleanField(_('is_correct'), default=False, null=True, blank=True)

    # ラジオボタンの回答を保存
    # is_correct_radio = models.BooleanField(_('is_correct_radio'), default=False, null=True, blank=True)

    order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)
    # is_multiple = models.IntegerField(choices=ANSWER_TYPE, verbose_name =_('テスト回答タイプ'), blank=True, null=True, default=0)

    #テストの設問保存時に選択肢のorderの値をセットする
    def save(self, *args, **kwargs):

        # orderの値が存在しない場合
        if not self.order:
            # print("--------------- pk", self.pk)# None
            # print("--------------- 選択肢", self.text)# 選択肢
            # print("--------------- 選択肢の数", self.text)
            # print("--------------- 設問", self.question)# 設問
            # print("--------------- order", self.order)# 0
            # print("---------------- all ----------------", self.question.choice_set.all().count())

            self.order = self.question.choice_set.all().count() + 1


        super().save(*args, **kwargs)


    def __str__(self):
        return self.text


ANSWER_TYPE_QUESTIONNAIRE = (
    # (1, 'ラジオボタン'),
    # (2, 'チェックボックス'),
    (1, '多肢選択(回答は1つ)'),
    (2, '多肢選択(回答は2つ以上)'),
    (3, '記述式'),
)


"""
テスト結果登録テーブル
"""
class QuestionResult(models.Model):

    # 質問
    question_relation = models.ForeignKey(Question, verbose_name = _("question_relation"), on_delete=models.SET_NULL, null=True, related_name='question_relation')

    # 質問のID
    question = models.CharField(_('question'), max_length=255, blank=True)
    # question_id = models.CharField(_('question_id'), max_length=255, blank=True)

    # タイプ
    is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

    # 回答
    answer = ListCharField(models.CharField(max_length=1000),size=6, max_length=(6 * 1001), null=True, blank=True)


    def __str__(self):
        return str(self.id)


"""
アンケート質問テーブル
"""
class QuestionnaireQuestion(models.Model):
    parts = models.ForeignKey(Parts, blank=True, null=True, on_delete=models.CASCADE)
    # parts = models.ManyToManyField(Parts, blank=True, null=True)
    text = models.CharField(_('text'), max_length=500, blank=True)
    order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)
    is_multiple = models.BooleanField(_('is_multiple'), default=True) # falseの場合はシングルでRadioとする
    is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

    # 設問のタイプ
    is_multiple_questionnaire = models.IntegerField(choices=ANSWER_TYPE_QUESTIONNAIRE, verbose_name =_('アンケート回答タイプ'), blank=True, null=True, default=0)

    # 画像
    image = models.ManyToManyField(Image, verbose_name = _('画像'), blank=True)

    # 投稿者
    # questionnair_register_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='questionnair_register_user')
    questionnair_register_user = models.CharField('投稿者', max_length=255, blank=True, null=True)

    def __str__(self):
        return self.text


"""
アンケート選択肢テーブル
"""
class QuestionnaireChoice(models.Model):
    question = models.ForeignKey(QuestionnaireQuestion, blank=True, null=True, on_delete=models.CASCADE)
    text = models.CharField(_('text'), max_length=120, blank=True)
    order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)

    # アンケートの設問保存時に選択肢のorderの値をセットする
    def save(self, *args, **kwargs):

        # orderの値が存在しない場合
        if not self.order:
            # print("--------------- pk", self.pk)# None
            # print("--------------- 選択肢", self.text)# 選択肢
            # print("--------------- 選択肢の数", self.text)
            # print("--------------- 設問", self.question)# 設問
            # print("--------------- order", self.order)# 0
            # print("---------------- all ----------------", self.question.questionnairechoice_set.all().count())#

            self.order = self.question.questionnairechoice_set.all().count() + 1

        super().save(*args, **kwargs)


    def __str__(self):
        return self.text


"""
アンケート結果登録テーブル
"""
class QuestionnaireResult(models.Model):

    # 質問
    questionnairequestion_relation = models.ForeignKey(QuestionnaireQuestion, verbose_name = _("questionnairequestion_relation"), on_delete=models.SET_NULL, null=True, related_name='questionnairequestion_relation')

    # 質問
    question = models.CharField(_('question'), max_length=255, blank=True)

    # タイプ
    is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

    # 回答
    answer = ListCharField(models.CharField(max_length=1000),size=6, max_length=(6 * 1001), null=True, blank=True)

    def __str__(self):
        return str(self.id)


"""
パーツ管理テーブル
"""
class PartsManage(models.Model):
    order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)
    type = models.IntegerField(choices=PARTS_TYPE, default=0)
    # training_id = models.CharField(_('training_id'), max_length=255, blank=True, null=True)
    parts = models.ForeignKey(Parts, on_delete=models.CASCADE, null=True, related_name='parts_manage')# koko
    # ユーザー
    # user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='parts_manage_user')# koko
    user = models.CharField('ユーザー', max_length=255, blank=True, null=True)
    # ゲストユーザー
    parts_manage_guest_user = models.ForeignKey(GuestUserManagement, blank=True, null=True, on_delete=models.CASCADE, related_name='parts_manage_guest_user')# koko
    # 期限
    period_date = models.DateTimeField(_('period date'), blank=True, null=True)
    # ステータス
    status = models.IntegerField(choices=STATUS_CHOICE, default=1)# koko
    # 受講必須
    is_parts_required = models.BooleanField(_('is_parts_required'), default=False)

    """-------ファイル用------"""
    # 配布ファイル
    file_manage = models.ManyToManyField(FileManage, verbose_name = _('file_manage'), blank=True)

    """-------動画用------"""
    play_start_date = models.DateTimeField(_('start date'), blank=True, null=True, default=timezone.now)
    movie_duration = models.IntegerField(_('duration'), blank=True, null=True)
    movie_file_id = models.CharField(_('movie_file_id'), max_length=10, blank=True, null=True)
    expected_end_date = models.DateTimeField(_('expectd_end_date'), blank=True, null=True, default=None)
    current_time = models.IntegerField(_('current_time'), blank=True, null=True, default="0")

    """-------アンケート用------"""
    # 結果登録
    questionnaire_result = models.ManyToManyField(QuestionnaireResult, verbose_name = _('アンケート結果'), blank=True)

    """-------テスト用------"""
    # テスト結果登録
    question_result = models.ManyToManyField(QuestionResult, verbose_name = _('テスト結果'), blank=True)
    # 削除対象フラグ
    del_parts_manage_flg = models.BooleanField(_('削除対象フラグ'), default=False)




"""
制御条件設定テーブル
"""
class ControlConditions(models.Model):

    # 依存元
    parts_origin = models.ForeignKey(Parts, blank=True, null=True, on_delete=models.CASCADE, related_name='parts_origin')

    # 依存先
    parts_destination = models.ForeignKey(Parts, blank=True, null=True, on_delete=models.CASCADE, related_name='parts_destination')

    # def __str__(self):
    #     return self.text




# ANSWER_TYPE = (
#     # (1, 'ラジオボタン'),
#     # (2, 'チェックボックス'),
#     (1, '多肢選択(正答は1つ)'),
#     (2, '多肢選択(正答は2つ以上)'),
#     (3, '記述式(完全一致)'),
#     (4, '記述式(部分一致)'),
# )


# """
# テスト質問(設問)テーブル
# """
# class Question(models.Model):
#     parts = models.ForeignKey(Parts, blank=True, null=True, on_delete=models.CASCADE, related_name='question_parts')
#     # parts = models.ManyToManyField(Parts, blank=True, null=True, related_name='question_parts')
#     text = models.CharField(_('text'), max_length=500, blank=True)
#     order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)
#     is_multiple = models.IntegerField(choices=ANSWER_TYPE, verbose_name =_('テスト回答タイプ'), blank=True, null=True, default=0)
#     # is_multiple = models.ChoiceField(choices=ANSWER_TYPE, verbose_name =_('テスト回答タイプ'), blank=True, null=True, default=0)
#     # 画像の追加
#     image = models.ManyToManyField(Image, verbose_name = _('画像'), blank=True)
#     # 回答数の設定
#     number_of_answers = models.IntegerField(verbose_name =_('number_of_answers'), blank=True, null=True, default=0)
#     # 投稿者
#     # question_register_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='question_register_user')
#     question_register_user = models.CharField('投稿者', max_length=255, blank=True, null=True)
#     def __str__(self):
#         return self.text


# """
# テスト選択肢テーブル
# """
# class Choice(models.Model):
#     # question = models.ForeignKey(Question, blank=True, null=True, on_delete=models.CASCADE, related_name='question')
#     question = models.ForeignKey(Question, blank=True, null=True, on_delete=models.CASCADE)

#     text = models.CharField(_('text'), max_length=120, blank=True)

#     # チェックボックス、完全 / 部分一致
#     # is_correct = models.BooleanField(_('is_correct'), choices=BOOL_CHOICES, default=False, null=True, blank=True)
#     is_correct = models.BooleanField(_('is_correct'), default=False, null=True, blank=True)

#     # ラジオボタンの回答を保存
#     # is_correct_radio = models.BooleanField(_('is_correct_radio'), default=False, null=True, blank=True)

#     order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)
#     # is_multiple = models.IntegerField(choices=ANSWER_TYPE, verbose_name =_('テスト回答タイプ'), blank=True, null=True, default=0)

#     #テストの設問保存時に選択肢のorderの値をセットする
#     def save(self, *args, **kwargs):

#         # orderの値が存在しない場合
#         if not self.order:
#             # print("--------------- pk", self.pk)# None
#             # print("--------------- 選択肢", self.text)# 選択肢
#             # print("--------------- 選択肢の数", self.text)
#             # print("--------------- 設問", self.question)# 設問
#             # print("--------------- order", self.order)# 0
#             # print("---------------- all ----------------", self.question.choice_set.all().count())

#             self.order = self.question.choice_set.all().count() + 1


#         super().save(*args, **kwargs)


#     def __str__(self):
#         return self.text


# ANSWER_TYPE_QUESTIONNAIRE = (
#     # (1, 'ラジオボタン'),
#     # (2, 'チェックボックス'),
#     (1, '多肢選択(回答は1つ)'),
#     (2, '多肢選択(回答は2つ以上)'),
#     (3, '記述式'),
# )


# """
# テスト結果登録テーブル
# """
# class QuestionResult(models.Model):

#     # 質問
#     question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)

#     # 質問のID
#     question = models.CharField(_('question'), max_length=255, blank=True)
#     # question_id = models.CharField(_('question'), max_length=255, blank=True)

#     # タイプ
#     is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

#     # 回答
#     answer = ListCharField(models.CharField(max_length=1000),size=6, max_length=(6 * 1001), null=True, blank=True)


#     def __str__(self):
#         return str(self.id)


# """
# アンケート質問テーブル
# """
# class QuestionnaireQuestion(models.Model):
#     parts = models.ForeignKey(Parts, blank=True, null=True, on_delete=models.CASCADE)
#     # parts = models.ManyToManyField(Parts, blank=True, null=True)
#     text = models.CharField(_('text'), max_length=500, blank=True)
#     order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)
#     is_multiple = models.BooleanField(_('is_multiple'), default=True) # falseの場合はシングルでRadioとする
#     is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

#     # 設問のタイプ
#     is_multiple_questionnaire = models.IntegerField(choices=ANSWER_TYPE_QUESTIONNAIRE, verbose_name =_('アンケート回答タイプ'), blank=True, null=True, default=0)

#     # 画像
#     image = models.ManyToManyField(Image, verbose_name = _('画像'), blank=True)

#     # 投稿者
#     # questionnair_register_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='questionnair_register_user')
#     questionnair_register_user = models.CharField('投稿者', max_length=255, blank=True, null=True)

#     def __str__(self):
#         return self.text


# """
# アンケート選択肢テーブル
# """
# class QuestionnaireChoice(models.Model):
#     question = models.ForeignKey(QuestionnaireQuestion, blank=True, null=True, on_delete=models.CASCADE)
#     text = models.CharField(_('text'), max_length=120, blank=True)
#     order = models.IntegerField(verbose_name =_('order'), blank=True, null=True, default=0)

#     # アンケートの設問保存時に選択肢のorderの値をセットする
#     def save(self, *args, **kwargs):

#         # orderの値が存在しない場合
#         if not self.order:
#             # print("--------------- pk", self.pk)# None
#             # print("--------------- 選択肢", self.text)# 選択肢
#             # print("--------------- 選択肢の数", self.text)
#             # print("--------------- 設問", self.question)# 設問
#             # print("--------------- order", self.order)# 0
#             # print("---------------- all ----------------", self.question.questionnairechoice_set.all().count())#

#             self.order = self.question.questionnairechoice_set.all().count() + 1

#         super().save(*args, **kwargs)


#     def __str__(self):
#         return self.text


# """
# アンケート結果登録テーブル
# """
# class QuestionnaireResult(models.Model):

#     # 質問
#     question = models.CharField(_('question'), max_length=255, blank=True)

#     # タイプ
#     is_type = models.CharField(_('is_type'), max_length=255, default="radio", blank=True, null=True) # Trueの場合はテキストボックスとする

#     # 回答
#     answer = ListCharField(models.CharField(max_length=1000),size=6, max_length=(6 * 1001), null=True, blank=True)

#     def __str__(self):
#         return str(self.id)


"""
コース管理テーブル
"""
class SubjectManagement(models.Model):
    # ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 作成日
    created_subject_date = models.DateTimeField('作成日', default=timezone.now, blank=True)

    # コース名
    subject_name = models.CharField('コース名', max_length=30, blank=True, null=True)

    # 登録者
    # subject_reg_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='subject_reg_user')
    subject_reg_user = models.CharField('登録者', max_length=255, blank=True, null=True)

    # 対象者
    target = models.CharField('対象者', max_length=100, blank=True, null=True)

    # 目的
    objective = models.CharField('目的', max_length=300, blank=True, null=True)

    # 所要時間
    duration = models.CharField('所要時間', max_length=30, blank=True, null=True)

    # 投稿者の所属している会社
    # subject_reg_company = models.ForeignKey(Company, blank=True, null=True, on_delete=models.SET_NULL, related_name='subject_reg_company')
    subject_reg_company = models.CharField(_('投稿者の所属している会社'), max_length=255, blank=True, null=True) # 会社のIDの文字列が入る

    # 画像
    subject_image = models.ForeignKey(SubjectImage, null=True, on_delete=models.SET_DEFAULT, default=get_default_subject_image)


    def __str__(self):
        return self.subject_name



"""
トレーニングテーブル(自作中間テーブル)
"""
class TrainingRelation(models.Model):
    # グループのID
    group_id = models.CharField(max_length=500, verbose_name="グループのID", null=True, blank=True)

    # トレーニングのID
    training_id = models.CharField(max_length=500, verbose_name="トレーニングのID", null=True, blank=True)


"""
トレーニング
"""
class Training(models.Model):
    # ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # タイトル
    title = models.CharField('タイトル', max_length=255)

    # 説明
    description = models.CharField('説明', max_length=255, blank=True)

    # 投稿者
    # reg_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='reg_user')
    reg_user = models.CharField('作成者', max_length=255, blank=True, null=True)

    # 会社
    # reg_company = models.ForeignKey(Company, blank=True, null=True, on_delete=models.CASCADE, related_name='reg_company')
    reg_company = models.CharField('作成者が所属する会社', max_length=255, blank=True, null=True)

    # 期限
    period_date = models.DateTimeField(_('period date'), blank=True, null=True)

    # 開始日
    start_date = models.DateTimeField(_('start_time'), blank=True, null=True, default=timezone.now)

    # 終了日
    end_date = models.DateTimeField(_('end_date'), blank=True, null=True)

    # 完了日
    # done_date = models.DateTimeField(_('done date'), default=timezone.now)

    # 展開縮小のボタン
    is_open = models.BooleanField(_('is_open'), default=True)

    # ステータス
    status = models.IntegerField(choices=STATUS_CHOICE, default=1)

    # 作成日
    created_date = models.DateTimeField(_('created date'), default=timezone.now, blank=True)

    # 更新日時
    update_date = models.DateTimeField(_('update date'), default=None, blank=True, null=True)

    # 宛先グループ
    # destination_group = models.ManyToManyField(CustomGroup, verbose_name = _("Destination Group"), blank=True, related_name='destination_group')

    parts = models.ManyToManyField(Parts, verbose_name = _("Parts"), blank=True, related_name='parts')

    # 期限切れトレーニングの有効化・無効化切り替えフラグ
    expired_training_flg = models.BooleanField(_('期限切れトレーニングの有効化・無効化切り替えフラグ'), default=False)

    # トレーニングに紐づいているゲストユーザー
    destination_guest_user = models.ManyToManyField(GuestUserManagement, verbose_name = _("トレーニングに紐づいているゲストユーザー"), blank=True, related_name='destination_guest_user')

    # コース
    # subject = models.ForeignKey(SubjectManagement, blank=True, null=True, on_delete=models.SET_NULL, related_name='subject')
    subject = models.ForeignKey(SubjectManagement, blank=True, null=True, on_delete=models.SET_DEFAULT, default=get_default_subject, related_name='subject')

    # グループの編集が行われたかを識別するためのフラグ
    group_edit_check_flg = models.BooleanField(_('grpup_edit_check_flg'), default=False)

    def __str__(self):
        return self.title



"""
トレーニングの表示の切り替え
"""
class TrainingDoneChg(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user_id = models.CharField('user_id', max_length=255, blank=True, null=True)

    # コース
    subject = models.ForeignKey(SubjectManagement, blank=True, null=True, on_delete=models.CASCADE, related_name='subject_training_done_chg')

    # トレーニングの表示の切り替えフラグ
    is_training_done_chg = models.BooleanField(_('is_training_done_chg'), default=False)



"""

HOME画面内のトグルボタン展開縮小テーブル

"""
class FolderIsOpen(models.Model):

    # ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ユーザー
    user_id = models.CharField(_('user_id'), max_length=255, blank=True, null=True)

    # トレーニング
    training = models.ForeignKey(Training, blank=True, null=True, on_delete=models.CASCADE, related_name='folder_is_open_training')

    # 展開縮小のボタン
    is_open = models.BooleanField(_('is_open'), default=True)

    def __str__(self):

        return str(self.id)


"""
トレーニング管理テーブル
"""
class TrainingManage(models.Model):
    training = models.ForeignKey(Training, on_delete=models.CASCADE, null=True, related_name='training_manage')
    # ユーザー
    # user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='training_manage_user')
    user = models.CharField('ユーザー', max_length=255, blank=True, null=True)
    # ゲストユーザー
    guest_user_manage = models.ForeignKey(GuestUserManagement, blank=True, null=True, on_delete=models.CASCADE, related_name='guest_user_manage')
    # ステータス
    status = models.IntegerField(choices=STATUS_CHOICE, default=1)
    # 受講日時
    done_date = models.DateTimeField(_('受講日時'), blank=True, null=True)
    # コース
    # subject_manage = models.ForeignKey(SubjectManagement, blank=True, null=True, on_delete=models.CASCADE, related_name='subject_manage')
    subject_manage = models.ForeignKey(SubjectManagement, blank=True, null=True, on_delete=models.SET_DEFAULT, default=get_default_subject, related_name='subject_manage')

    # PartsManage
    parts_manage = models.ManyToManyField(PartsManage, verbose_name = _("Parts"), blank=True, related_name='parts_manage')




"""
受講履歴一覧テーブル
"""
class TrainingHistory(models.Model):
    # トレーニング ※参照先のトレーニングが削除されても受講履歴は残す
    # training = models.ForeignKey(Training, on_delete=models.CASCADE, null=True, related_name='training_history')
    training = models.ForeignKey(Training, on_delete=models.SET_NULL, null=True, related_name='training_history')
    # トレーニングタイトル
    title = models.CharField('トレーニングタイトル', max_length=255)
    # 説明
    description = models.CharField('説明', max_length=255, blank=True)
    # 投稿者
    # reg_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='training_reg_user')
    reg_user = models.CharField('投稿者', max_length=255, blank=True, null=True)
    # 投稿者(表示用)
    # reg_user_for_display = models.CharField('発信者', max_length=255)
    # 開始日
    start_date = models.DateTimeField(_('start_time'), blank=True, null=True, default=timezone.now)
    # 終了日
    end_date = models.DateTimeField(_('end_date'), blank=True, null=True)
    # 完了日
    # done_date = models.DateTimeField(_('done date'), default=timezone.now)
    done_date = models.DateTimeField(_('done date'), blank=True, null=True)
    # ユーザー
    # user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name='training_history_user')
    user = models.CharField('ユーザー', max_length=255, blank=True, null=True)
    # ゲストユーザー
    guest_user_history = models.ForeignKey(GuestUserManagement, blank=True, null=True, on_delete=models.CASCADE, related_name='guest_user_history')
    # ステータス
    status = models.IntegerField(choices=STATUS_CHOICE, default=1)
    # 削除済みフラグ
    del_flg = models.BooleanField(_('削除済みフラグ'), default=False)

    def __str__(self):
        return self.title


# """
# コース管理テーブル
# """
# class SubjectManagement(models.Model):
#     # ID
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

#     # コース名
#     subject_name = models.CharField('コース名', max_length=30, blank=True, null=True)

#     # 登録者
#     subject_reg_user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL, related_name='subject_reg_user')

#     # 登録トレーニング
#     subject_reg_training = models.ManyToManyField(Training, blank=True, null=True, related_name='subject_reg_training')

#     def __str__(self):
#         return self.subject_name