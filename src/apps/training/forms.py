from django import forms
from django.forms import RadioSelect
from django.forms import BaseFormSet
from django.forms import Select
# from .models import Test, Question, Choice, QuestionnaireQuestion
from .models import Question, Choice, QuestionnaireQuestion, Training, File, FileManage, QuestionnaireResult, QuestionnaireQuestion, QuestionnaireChoice, CustomGroup, Parts, Question, Choice, Image, ControlConditions
from .models import UserCustomGroupRelation, TrainingRelation
from .models import CoAdminUserManagement, CoAdminUserManagementRelation, GuestUserManagement, SubjectManagement
from accounts.models import User

from django.conf import settings
import bootstrap_datepicker_plus as datetimepicker

from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, PasswordChangeForm
)

from django.contrib.auth.hashers import check_password


# 逆参照のテーブルをフィルタやソートする
from django.db.models import Prefetch
from django.db.models import Q
from django.db.models import CharField, Value

# メールアドレスの形式✔
import re

# 日付
import datetime

import pytz

# バリデーション
from django.core.validators import MaxValueValidator, MinValueValidator

# クエリセットの結合
from itertools import chain

# MultiModelForm
from betterforms.multiform import MultiModelForm





class MultipleForm(forms.Form):
    action = forms.CharField(max_length=60, widget=forms.HiddenInput())


"""
コース登録用
"""
class Training_Checkbox(forms.CheckboxSelectMultiple):
    input_type = 'checkbox'
    template_name = 'tasks/forms/widget/training_checkbox.html'


"""
宛先ユーザーのチェックボックスの見た目をカスタマイズするためのウィジェット
"""
class User_Checkbox(forms.CheckboxSelectMultiple):
    input_type = 'checkbox'
    template_name = 'tasks/forms/widget/user_checkbox.html'


"""
宛先ユーザーのチェックボックスの見た目をカスタマイズするためのウィジェット
"""
class User_Group_Checkbox(forms.CheckboxSelectMultiple):
    input_type = 'checkbox'
    template_name = 'tasks/forms/widget/user_group_checkbox.html'


"""
テストの設問作成画面、回答タイプの選択をラジオボタンに変更
"""
class Test_Radio(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'training/forms/widget/test_radio.html'


"""
アンケートの設問作成画面、回答タイプの選択をラジオボタンに変更
"""
class Questionnaire_Radio(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'training/forms/widget/questionnaire_radio.html'


"""
テストの選択肢　※実際は使用していない
"""
class Test_Choice(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'training/forms/widget/test_choice.html'

    def get_context(self, name, value, attrs):
        context = super(Test_Choice, self).get_context(name, value, attrs)

        choices = Choice.objects.all()
        questions = Question.objects.all().prefetch_related(Prefetch("choice_set", queryset=Choice.objects.filter()))

        context['questions'] = questions
        context['choices'] = choices

        return context


"""
テスト　※実際は使用していない
"""
class TestQuestionForm(forms.ModelForm):

    class Meta:
        model = Choice
        fields = ('text',)

    def __init__(self, *args, **kwargs):
        choices = Choice.objects.all()

        super(TestQuestionForm, self).__init__(*args, **kwargs)

        self.fields['text'] = forms.ModelChoiceField(
            required=False,
            widget=Test_Choice,
            # widget=forms.RadioSelect,
            label='',
            empty_label=None,
            queryset=choices,
        )


"""
アプリケーション
"""
class _QuestionnaireQuestionForm(forms.ModelForm):

    class Meta:
        model = QuestionnaireQuestion
        fields = ('text',)



"""
リマインダー通知用
"""
class ReminderForm(forms.Form):
    message = forms.CharField(label='message', widget=forms.Textarea())

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        self.days = kwargs.pop('days', None)
        days = str(self.days)

        # PKを使ってDBから対象のトレーニングを取得
        training = Training.objects.filter(pk=self.pk).first()

        super(ReminderForm, self).__init__(*args, **kwargs)

        # textareaにメッセージを表示
        self.fields['message'].initial = training.title + 'は、あと' + days + '日で終了です。早めに受講してください。'


class CSVUploadForm(forms.Form):
    file = forms.FileField(label='CSVファイル', help_text='※拡張子csvのファイルをアップロードしてください。')
    # pass_change = forms.BooleanField(label='パスワード変更', required=False, widget=forms.CheckboxInput(attrs={'class': 'check'},))

    def clean_file(self):
        file = self.cleaned_data['file']
        # 拡張子チェック
        if file.name.endswith('.csv'):
            return file
        else:
            raise forms.ValidationError('拡張子はcsvのみです')


"""
トレーニング作成画面
"""
# class CreateTrainingForm(forms.ModelForm):
class CreateTrainingForm(forms.Form):

    # class Meta:
    #     model = Training
    #     fields = ('title', 'start_date', 'end_date', 'description', 'subject', 'destination_group', 'expired_training_flg')

    # views.pyから送られてきたログインユーザーをpopで受け取る
    def __init__(self, *args, **kwargs):
        self.login_user = kwargs.pop('login_user', None)
        super(CreateTrainingForm, self).__init__(*args, **kwargs)

        # 逆参照してコースに紐づいているトレーニングを取得する
        subject_lists = []

        subjects = SubjectManagement.objects.filter(Q(subject_reg_company=self.login_user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')

        for subject in subjects:

            subjecte_count = Training.objects.filter(subject=subject, reg_company=self.login_user.company.id).count()

            if subjecte_count >= 10 and subject.subject_name != "デフォルト":
                print("------------------- 超えています")
                subject_lists.append(subject.id)

            queryset = SubjectManagement.objects.filter(Q(subject_reg_company=self.login_user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date').exclude(id__in=subject_lists)


        # コース
        self.fields['subject'] = forms.ModelChoiceField(
            label="コース",
            required=False,
            # empty_label='デフォルト',
            empty_label=None,
            # queryset=SubjectManagement.objects.filter(Q(subject_reg_company=self.login_user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')
            queryset=queryset
        )

        # グループ
        self.fields['destination_group'] = forms.ModelMultipleChoiceField(
            required=True,
            label="グループ",
            # queryset=CustomGroup.objects.filter(group_reg_user=self.login_user.id, tempo_flg=False),
            queryset=CustomGroup.objects.filter(group_reg_user=self.login_user.id),
            widget = User_Group_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple
        )

        self.fields['destination_group'].error_messages.update({
            'required': 'グループの選択は必須です。',
        })


    def clean(self):

        cleaned_data = super().clean()

        # formに入力された値を取得
        sub_start_date = self.cleaned_data['start_date']
        print("---------- sub_start_date ---------", sub_start_date)
        print(type(sub_start_date))# <class 'datetime.datetime'>

        # 開始時刻が未設定(=None)の場合
        if sub_start_date is None:
            print("Noneだったよ")

            # 現在の時刻を代入
            sub_start_date = datetime.datetime.now(pytz.timezone('UTC'))
            print(type(sub_start_date))


        sub_end_date = self.cleaned_data['end_date']
        print("---------- sub_end_date ---------", sub_end_date)
        print(type(sub_end_date))# <class 'datetime.datetime'>

        dt2 = sub_end_date + datetime.timedelta(hours=12)
        print("---------- dt2 ---------", dt2)

        # 日付確認
        if sub_start_date > sub_end_date:
            raise forms.ValidationError('開始日時が終了日時よりも後に設定されています。')

        # 終了時間が開始日+12時間より小さければNG
        if sub_end_date < sub_start_date + datetime.timedelta(hours=12):
            raise forms.ValidationError('終了時間は開始日から12時間以上の時刻で設定してください。')

        return self.cleaned_data


    title = forms.CharField(
        required=True,
        label='タイトル',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'タイトルを入力してください',
                'class':'require_label'
                # 'maxlength': 10
                }
        )
    )

    start_date = forms.DateTimeField(
        required=False,
        label="開始日",
        widget=datetimepicker.DateTimePickerInput(

            format='%Y/%m/%d %H:%M:%S', options={
                'locale': 'ja',
                'dayViewHeaderFormat': 'YYYY年 MMMM',
                'tooltips': {
                            'close': '閉じる',

                            'selectMonth': '月を選択',

                            'prevMonth': '前の月',

                            'nextMonth': '次の月',

                            'selectYear': '年を選択',

                            'prevYear': '前の年',

                            'nextYear': '次の年',

                            'selectTime': '時間を選択',

                            'selectDate': '日付を選択',

                            'prevDecade': '前の期間',

                            'nextDecade': '次の期間',

                            'selectDecade': '期間を選択',

                            'prevCentury': '前世紀',

                            'nextCentury': '次世紀',

                            'today':'今日の日付',

                            'clear':'削除'

                            }

            }
        ),
        input_formats=['%Y/%m/%d %H:%M:%S']
    )

    end_date = forms.DateTimeField(
        required=True,
        label="終了日",
        widget=datetimepicker.DateTimePickerInput(

            format='%Y/%m/%d %H:%M:%S', options={
                'locale': 'ja',
                'dayViewHeaderFormat': 'YYYY年 MMMM',

                'tooltips': {
                            'close': '閉じる',

                            'selectMonth': '月を選択',

                            'prevMonth': '前の月',

                            'nextMonth': '次の月',

                            'selectYear': '年を選択',

                            'prevYear': '前の年',

                            'nextYear': '次の年',

                            'selectTime': '時間を選択',

                            'selectDate': '日付を選択',

                            'prevDecade': '前の期間',

                            'nextDecade': '次の期間',

                            'selectDecade': '期間を選択',

                            'prevCentury': '前世紀',

                            'nextCentury': '次世紀',

                            'today':'今日の日付',

                            'clear':'削除'

                            }
            }
        ),
        input_formats=['%Y/%m/%d %H:%M:%S']
    )


    description = forms.CharField(
        required=True,
        label="説明文",

        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'id': 'training_description',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # destination_group = forms.ModelMultipleChoiceField(

    #     required=True,
    #     label="グループ",

    #     # queryset=CustomGroup.objects.all(),
    #     queryset=CustomGroup.objects.filter(tempo_flg=False),

    #     # widget=forms.CheckboxSelectMultiple
    #     widget = User_Group_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple

    # )

    expired_training_flg = forms.BooleanField(
        required=False,
        label='期限切れトレーニングの有効化・無効化切り替え',
    )

    # グループの編集が行われたかを識別するためのフラグ
    group_edit_check_flg = forms.BooleanField(
        required=False,
    )









    # def clean_title(self):
    #     """ タイトルの文字数チェック """
    #     title = self.cleaned_data['title']

    #     # 文字数確認
    #     if len(title) > 45:
    #         raise forms.ValidationError('文字数上限を超えています。45文字以内にしてください。'.format(title))

    #     return title

    # def clean_description(self):
    #     """ 説明文の文字数チェック """
    #     description = self.cleaned_data['description']

    #     # 文字数確認
    #     if len(description) > 100:
    #         raise forms.ValidationError('文字数上限を超えています。100文字以内にしてください。'.format(description))

    #     return description






"""
テストパーツ作成
"""
class AdminTestForm(forms.ModelForm):

    class Meta:
        model = Parts
        fields = ('order','type','title','description', 'title_detail',
                'description_detail', 'pass_line', 'pass_text1', 'pass_text2', 'unpass_text1', 'unpass_text2',
                'is_required', 'is_question_random', 'answer_content_show')


    # 初期値を設定
    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super(AdminTestForm, self).__init__(*args, **kwargs)
        self.fields['type'].initial = 3 # テスト
        self.fields['type'].widget.attrs['readonly'] = 'readonly' # 編集不可



    # 順番
    order = forms.IntegerField(
        required=False,
        label='順番',
    )

    # タイプ
    type = forms.IntegerField(
        required=False,
        label='タイプ',
    )

    # タイトル
    title = forms.CharField(
        required=True,
        label='タイトル',
    )

    # 説明
    description = forms.CharField(
        required=True,
        label='説明',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # パーツ内に表示するタイトル
    title_detail = forms.CharField(
        required=True,
        label='パーツ内に表示するタイトル',
    )

    # パーツ内に表示する説明
    description_detail = forms.CharField(
        required=True,
        label='パーツ内に表示する説明',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 合格ライン
    pass_line = forms.IntegerField(
        required=False,
        label='合格ライン',
    )

    # 合格文1
    pass_text1 = forms.CharField(
        required=True,
        label='合格文1',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 合格文2
    pass_text2 = forms.CharField(
        required=False,
        label='合格文2',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 不合格文1
    unpass_text1 = forms.CharField(
        required=True,
        label='不合格文1',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 不合格文2
    unpass_text2 = forms.CharField(
        required=False,
        label='不合格文2',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須ラベル',
    )

    # ランダムソートON / OFF
    is_question_random = forms.BooleanField(
        required=False,
        label='ランダムソート',
    )

    # テスト結果の〇✖表記の表示有無
    answer_content_show = forms.BooleanField(
        required=False,
        label='テスト結果の〇✖表記の表示有無',
    )

    def clean_title(self):
        title = self.cleaned_data['title']

        # 存在確認
        if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
            raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))

        return title











"""
アンケートパーツ作成
"""
class AdminQuestionnaireForm(forms.ModelForm):

    class Meta:
        model = Parts
        fields = ('order','type','title','description', 'title_detail', 'description_detail', 'is_required')

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super(AdminQuestionnaireForm, self).__init__(*args, **kwargs)
        self.fields['type'].initial = 4 # アンケート
        self.fields['type'].widget.attrs['readonly'] = 'readonly' # 編集不可


    # 順番
    order = forms.IntegerField(
        required=False,
        label='順番',
    )

    # タイプ
    type = forms.IntegerField(
        required=True,
        label='タイプ',
    )

    # タイトル
    title = forms.CharField(
        label='タイトル',
        required=True,
    )

    # 説明
    description = forms.CharField(
        label='説明',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # パーツ内に表示するタイトル
    title_detail = forms.CharField(
        required=True,
        label='パーツ内に表示するタイトル',
    )

    # パーツ内に表示する説明
    description_detail = forms.CharField(
        label='パーツ内に表示する説明',
        required=True,
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須ラベル',
    )


    def clean_title(self):
        title = self.cleaned_data['title']

        # 存在確認
        if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
            raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))

        return title






"""
動画パーツ作成
"""
class AdminMovieForm(forms.ModelForm):

    class Meta:
        model = Parts
        # fields = ('order', 'type' ,'movie', 'title', 'description', 'poster', 'file_id', 'duration', 'is_required')
        fields = ('order', 'type' , 'title', 'description', 'is_required', 'duration')

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super(AdminMovieForm, self).__init__(*args, **kwargs)
        self.fields['type'].initial = 2 # 動画
        self.fields['type'].widget.attrs['readonly'] = 'readonly' # 編集不可



    # 順番
    order = forms.IntegerField(
        required=False,
        label='順番',
    )

    # タイプ
    type = forms.IntegerField(
        # required=True,
        label='タイプ',
    )

    # タイトル
    title = forms.CharField(
        # required=True,
        label='タイトル',
    )

    # 説明
    description = forms.CharField(
        # required=True,
        label="説明文",

        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'id': 'training_description',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )


    # ファイルID
    # file_id = forms.CharField(
    #     required=False,
    #     label='ファイルID',
    # )

    # 視聴時間
    duration = forms.CharField(# datatime 時間だけ
        required=False,
        label='視聴時間',
    )

    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須',
    )


    def clean_title(self):
        title = self.cleaned_data['title']

        # 存在確認
        if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
            raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))

        return title




"""
ファイルパーツ作成
"""
class AdminFileForm(forms.ModelForm):

    class Meta:
        model = Parts
        fields = ('order', 'type' , 'title', 'description', 'is_required')

    def __init__(self, *args, **kwargs):

        self.user = kwargs.pop('user', None)

        super(AdminFileForm, self).__init__(*args, **kwargs)
        self.fields['type'].initial = 1 # テスト
        self.fields['type'].widget.attrs['readonly'] = 'readonly' # 編集不可


    # 順番
    order = forms.IntegerField(
        label='順番',
        required=False,
    )

    # タイプ
    type = forms.IntegerField(
        label='タイプ',
    )

    # タイトル
    title = forms.CharField(
        label='タイトル',
    )

    # 説明
    description = forms.CharField(
        label="説明文",

        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # ファイルID
    # file_id = forms.CharField(
    #     required=False,
    #     label='ファイルID',
    # )

    # ファイル
    # file = forms.FileField(
    #     required=False,
    #     label='ファイル',
    # )

    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須',
    )



    def clean_title(self):
        title = self.cleaned_data['title']

        # 存在確認
        if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
            raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))

        return title






# 追加 親フォームに子フォームを埋め込み、これらの処理を一括して行えるようにする
class ModelFormWithFormSetMixin:

    def __init__(self, *args, **kwargs):
        super(ModelFormWithFormSetMixin, self).__init__(*args, **kwargs)
        self.formset = self.formset_class(
            instance=self.instance,
            data=self.data if self.is_bound else None,
        )

    # フォームに入力された値にエラーがないかをバリデートする
    # def is_valid(self):

    #     # parts_pk = self.kwargs['pk']
    #     # print("------------ parts_pk ----------------", parts_pk)

    #     print("------------ self ----------------", self)

    #     return super(ModelFormWithFormSetMixin, self).is_valid() and self.formset.is_valid()


    # def save(self, commit=True):
    #     saved_instance = super(ModelFormWithFormSetMixin, self).save(commit)
    #     self.formset.save(commit)
    #     return saved_instance








"""
法人区分の見た目をカスタマイズするためのウィジェット

"""
class Corp_Class_Radio(forms.RadioSelect):

    input_type = 'radio'
    template_name = 'training/forms/widget/corp_class_radio.html'



"""
テストの選択肢（子供）
"""

CHOICES = (
    (1, 'true'),
    (2, 'false'),
)

class ChoiceForm(forms.ModelForm):

    class Meta:
        model = Choice
        fields = ('question','text','is_correct',)

        # error_messages = {
        #     'text': {
        #         'maxlength': "設問内容は150文字以内で入力してください。",
        #     },
        # }

        widgets = {
            'text': forms.TextInput(
                                attrs={
                                    'autofocus': 'autofocus',
                                    'autocomplete': 'off',
                                    'size': '110',
                                    'maxlength': '120',
                                    'placeholder' : "120文字以内で入力してください。"
                                },
            ),

            # 'is_correct_radio': forms.RadioSelect(),

            'is_correct': forms.CheckboxInput(),
        }


    def __init__(self, *args, **kwargs):

        # choices = Choice.objects.all()

        super(ChoiceForm, self).__init__(*args, **kwargs)
        # textフィールドにクラスを与える
        self.fields['text'].widget.attrs["class"] = "searchTerm"
        self.fields['text'].widget.attrs["data-target"] = "hoge"

        self.fields['is_correct'].widget.attrs["class"] = "icon_correct"
        self.fields['is_correct'].widget.attrs["data-target"] = "fuga"

        # エラーメッセージをカスタマイズ
        # self.fields['is_correct'].error_messages = {'required': '正解の選択肢にチェックを入れてください。'}

    # def clean_text(self):
    #     text = self.cleaned_data['text']
    #     print("text", text)

    #     if text == '':
    #         print("textaaaaaaaaaaaa")
    #         raise forms.ValidationError("選択項目の入力は必須です。")

    #     return text

    # def clean_is_correct(self):
    #     is_correct = self.cleaned_data['is_correct']

    #     if is_correct == '':
    #         raise forms.ValidationError("正解の選択肢にチェックを入れてください。")

    #     return is_correct


# class RequiredFormSet(BaseFormSet):
#     def clean(self):
#         """Checks that no two articles have the same title."""
#         if any(self.errors):
#             # Don't bother validating the formset unless each form is valid on its own
#             return

#         titles = []

#         for form in self.forms:
#             if self.can_delete and self._should_delete_form(form):
#                 continue

#             title = form.cleaned_data.get('title')

#             if title in titles:
#                 raise forms.ValidationError("Articles in a set must have distinct titles.")
#             titles.append(title)



"""
FormSet
"""
ChoiceFormSet  = forms.inlineformset_factory(
    parent_model=Question,# 親となるモデルを指定
    model=Choice,# 自身のモデルを指定
    # fields='__all__',
    form=ChoiceForm,
    extra=3,# 新規作成用フォームの数
    max_num=5,# フォームの最大件数
    # max_num=4,# フォームの最大件数
    can_delete=False, # 削除用チェックボックスの表示

)




"""
テストの設問（親）
"""
class QuestionForm(ModelFormWithFormSetMixin, forms.ModelForm):
# class QuestionForm(forms.ModelForm):

    # 追加
    formset_class = ChoiceFormSet

    class Meta:
        model = Question
        fields = ('parts','text','order','is_multiple')

        widgets = {
            'text': forms.Textarea(attrs={
                'rows':4,
                'cols':15
            }),

            # 回答タイプの選択をラジオボタンに変更
            'is_multiple':Test_Radio,
        }

        # パーツ
        parts = forms.CharField(
            label='parts',
        )

    # views.pyから送られてきたログインユーザーをpopで受け取る
    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super(QuestionForm, self).__init__(*args, **kwargs)

        self.fields['parts'].initial = 'self.pk' # パーツのID

        # 初期表示の「--------」を消す
        self.fields['is_multiple'].choices = self.fields['is_multiple'].choices[1:]



"""
アンケートの選択肢（子供）
"""
class QuestionnaireChoiceForm(forms.ModelForm):

    class Meta:
        model = QuestionnaireChoice
        fields = ('question','text',)

        # error_messages = {
        #     'text': {
        #         'maxlength': "設問内容は150文字以内で入力してください。",
        #     },
        # }

        widgets = {
            'text': forms.TextInput(
                attrs={
                    'autofocus': 'autofocus',
                    'autocomplete': 'off',
                    'size': '120',
                    'maxlength': '120',
                    'placeholder' : "120文字以内で入力してください。"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super(QuestionnaireChoiceForm, self).__init__(*args, **kwargs)
        # textフィールドにクラスを与える
        self.fields['text'].widget.attrs["class"] = "searchTerm"
        self.fields['text'].widget.attrs["data-target"] = "hoge"






"""
FormSet
"""
QuestionnaireChoiceFormSet  = forms.inlineformset_factory(
    parent_model=QuestionnaireQuestion,# 親となるモデルを指定
    model=QuestionnaireChoice,# 自身のモデルを指定
    # fields='__all__',
    form=QuestionnaireChoiceForm,
    extra=3,# 新規作成用フォームの数
    max_num=5,# フォームの最大件数
    can_delete=False# 削除用チェックボックスの表示
)


"""
アンケートの設問（親）
"""
class QuestionnaireQuestionForm(ModelFormWithFormSetMixin, forms.ModelForm):
# class QuestionForm(forms.ModelForm):
    # 追加
    formset_class = QuestionnaireChoiceFormSet

    class Meta:
        model = QuestionnaireQuestion
        fields = ('text','is_multiple_questionnaire',)

        widgets = {
            'text': forms.Textarea(attrs={
                'rows':4, 'cols':15
            }),

            # 回答タイプの選択をラジオボタンに変更
            'is_multiple_questionnaire':Questionnaire_Radio,
        }

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        super(QuestionnaireQuestionForm, self).__init__(*args, **kwargs)

        # 初期表示の「--------」を消す
        self.fields['is_multiple_questionnaire'].choices = self.fields['is_multiple_questionnaire'].choices[1:]



"""
テストパーツの変更
"""
class TestUpdateForm(forms.ModelForm):

    # 初期値を設定
    def __init__(self, *args, **kwargs):
        super(AdminTestForm, self).__init__(*args, **kwargs)

        self.fields['type'].initial = 3 # テスト
        self.fields['type'].widget.attrs['readonly'] = 'readonly' # 編集不可

    class Meta:
        model = Parts
        fields = ('order','type','title','description', 'title_detail',
                'description_detail', 'pass_line', 'pass_text1', 'pass_text2', 'unpass_text1', 'unpass_text2', 'is_required', 'is_question_random',)

        # 順番
        order = forms.IntegerField(
            # required=True,
            label='順番',
        )

        # タイプ
        type = forms.IntegerField(
            # required=True,
            label='タイプ',
        )

        # タイトル
        title = forms.CharField(
            required=True,
            label='タイトル',
        )

        # 説明
        description = forms.CharField(
            required=True,
            label='説明',
        )

        # パーツ内に表示するタイトル
        title_detail = forms.CharField(
            required=True,
            label='パーツ内に表示するタイトル',
        )

        # パーツ内に表示する説明
        description_detail = forms.CharField(
            required=True,
            label='パーツ内に表示する説明',
        )

        # 合格ライン
        pass_line = forms.IntegerField(
            required=True,
            label='合格ライン',
        )

        # 合格文1
        pass_text1 = forms.CharField(
            required=True,
            label='合格文1',
        )

        # 合格文2
        pass_text2 = forms.CharField(
            # required=True,
            label='合格文2',
        )

        # 不合格文1
        unpass_text1 = forms.CharField(
            required=True,
            label='不合格文1',
        )

        # 不合格文2
        unpass_text2 = forms.CharField(
            # required=True,
            label='不合格文2',
        )

        # is_required
        is_required = forms.BooleanField(
            # required=True,
            label='必須',
        )

        # ランダムソートON / OFF
        is_question_random = forms.BooleanField(
            # required=True,
            label='ランダム出題',
        )







"""
カスタムグループの中間テーブル
"""
class UserCustomGroupRelationForm(forms.ModelForm):

    class Meta:
        model = UserCustomGroupRelation
        fields = ('group_id','group_user',)
            # 紐づけるグループユーザーを☑で表示する

        # views.pyから送られてきたログインユーザーをpopで受け取る
        # def __init__(self, user, *args, **kwargs):
        #     super(UserCustomGroupRelationForm, self).__init__(*args, **kwargs)

        #     self.fields['group_user'] = forms.ModelMultipleChoiceField(
        #         required=True,
        #         label="グループユーザー",
        #         queryset=User.objects.filter(is_rogical_deleted=False, company=self.login_user.company.pk).exclude(pk=self.login_user.pk),# ログインユーザーはリストから除外
        #         widget = User_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple
        #     )



"""
カスタムグループ作成, 変更
"""
# class CustomGroupForm(forms.ModelForm):
class CustomGroupForm(forms.Form):

    # class Meta:
    #     model = CustomGroup
    #     fields = ('name','group_user',)
        # fields = ('name',)

    # views.pyから送られてきたログインユーザーをpopで受け取る
    # def __init__(self, user, *args, **kwargs):
    def __init__(self, *args, **kwargs):
        # ログインユーザー取得
        # self.login_user = user
        self.login_user = kwargs.pop('user', None)
        self.url = kwargs.pop('url_name', None)
        self.pk = kwargs.pop('pk', None)

        super(CustomGroupForm, self).__init__(*args, **kwargs)

        # エラーメッセージをカスタマイズ
        # self.fields['group_user'].error_messages = {'required': 'グループユーザーの選択は必須です。'}

        # 紐づけるグループユーザーを☑で表示する
        self.fields['group_user'] = forms.ModelMultipleChoiceField(

            required=True,
            label="グループユーザー",
            # queryset=User.objects.filter(is_rogical_deleted=False, company=self.login_user.company.pk).exclude(pk=self.login_user.pk),# ログインユーザーはリストから除外
            queryset=User.objects.filter(is_rogical_deleted=False, company=self.login_user.company.pk),
            widget = User_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple

        )

        self.fields['name'] = forms.CharField(
            required=True,
            label='グループ名',
        )


    # 存在確認
    def clean_name(self):
        # フォームに入力された値を取得
        name = self.cleaned_data.get('name')
        # print("------- name ------", name)# 変更後の名前
        # print("------- pk ------", self.pk)# 2046c559-c5bf-4c0f-88a3-a722e2606e00
        # print("------- URL ------", self.url)# customgroup_group_update / input_customgroup ※URL名が取れる

        # URL名がinput_customgroup（CustomGroupCreateView）の場合
        if self.url == 'input_customgroup':
            # print("------ input_customgroupだよ -------")

            # グループ名が既に存在している場合
            if CustomGroup.objects.filter(group_reg_user=self.login_user, name__iexact=name).exists():
                raise forms.ValidationError('「{0}」は既に存在するグループ名です。別のグループ名を入力してください。'.format(name))
            return name

        # URL名がicustomgroup_group_update（CustomGroupUpdateView）の場合
        else:
            # print("------- customgroup_group_updateだよ ------")

            # PKを使ってDBから対象グループのオブジェトを取得
            customgroup_objects = CustomGroup.objects.filter(pk=self.pk).first()
            # print("------- customgroup_objects 1 ------", customgroup_objects)

            customgroup_object_name = customgroup_objects.name
            # print("------- customgroup_object_name 2 ------", customgroup_object_name)


            # オブジェクトの名前(=DBに登録されていたグループ名)とname(=変更後のグループ名)を比較、メンバーorグループ名の変更なのか判断する
            # メンバーのみの変更の場合
            if customgroup_object_name == name:
                # print("---------- 同じだよ")# 同じ場合は許可。
                return name

            # グループ名の変更の場合
            else:
                # print("---------- 違うよ")

                # NGの場合は、変更後の名前で存在確認をして存在する場合はNG
                if CustomGroup.objects.filter(group_reg_user=self.login_user, name__iexact=name).exists():
                    raise forms.ValidationError('「{0}」は既に存在するグループ名です。別のグループ名を入力してください。'.format(name))
                return name



"""
カスタムグループとカスタムグループの中間テーブルのフォーム
(MultiModelForm)
"""
class UserCustomGroupMultiForm(MultiModelForm):
    form_classes = {
        'custom_group': CustomGroup,# グループ名はCustomGroupモデル
        'user_id': UserCustomGroupRelationForm,
    }



"""
グループを登録する画面のフォーム(メールアドレス)
"""

# class CustomGroupBulkCreationForm(forms.ModelForm):
class CustomGroupBulkCreationForm(forms.Form):

    # class Meta:
    #     model = CustomGroup
    #     # fields = ('name','group_user',)
    #     fields = ('name',)

    # グループ名
    name = forms.CharField(
        label='グループ名',
        required=True,
    )

    # グルーピングユーザー
    group_user = forms.CharField(
        label='登録したいメールアドレス',
        required=True,
        widget=forms.Textarea()
    )


    # views.pyから送られてきたログインユーザーをpopで受け取る
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CustomGroupBulkCreationForm, self).__init__(*args, **kwargs)


    def clean_name(self):
        name = self.cleaned_data['name']
        # 存在確認
        if CustomGroup.objects.filter(group_reg_user=self.user, name__iexact=name).exists():
            raise forms.ValidationError('「{0}」は既に存在するグループ名です。別のグループ名を入力してください。'.format(name))
        return name


    def clean_group_user(self):
        group_user = self.cleaned_data['group_user']

        # リストに変換
        reg_user_list = group_user.splitlines()

        i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為

        # iは、現在の行番号。エラーの際に補足情報として使う
        for i, row in enumerate(reg_user_list, 1):

            print("----- row ----", row)# aaa@aaa.com

            # 存在確認　※論理削除済みのユーザーは除外
            user = User.objects.filter(email=row).exclude(is_rogical_deleted=True)
            print("----- user ----", user)

            # print("----- re.match ----", re.match('^[0-9a-z_./?-]+@([0-9a-z-]+.)+[0-9a-z-]+$', row))
            print("----- re.match ----", re.match('^[0-9a-zA-Z_./?-]+@([0-9a-zA-Z-]+.)+[0-9a-zA-Z-]+$', row))

            # if not re.match('^[0-9a-z_./?-]+@([0-9a-z-]+.)+[0-9a-z-]+$', row):
            if not re.match('^[0-9a-zA-Z_./?-]+@([0-9a-zA-Z-]+.)+[0-9a-zA-Z-]+$', row):
                raise forms.ValidationError('{0}行目のメールアドレスの形式が違います。正しいメールアドレスを入力してください。'.format(i))

            if user.count() == 0:
                raise forms.ValidationError('{0}行目のメールアドレスが存在しません。正しいメールアドレスを入力してください。'.format(i))



        return group_user




"""
トレーニングの変更
"""
# class TrainingUpdateForm(forms.ModelForm):
class TrainingUpdateForm(forms.Form):

    # class Meta:
    #     model = Training
    #     fields = ('title','description', 'start_date', 'end_date', 'destination_group', 'subject', 'expired_training_flg')

    # views.pyから送られてきたログインユーザーをpopで受け取る
    def __init__(self, *args, **kwargs):
        self.login_user = kwargs.pop('login_user', None)

        # コースに紐づいているトレーニング数が10以上の場合は一覧に表示させない
        subject_lists = []

        subjects = SubjectManagement.objects.filter(Q(subject_reg_company=self.login_user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')

        for subject in subjects:

            subjecte_count = Training.objects.filter(subject=subject, reg_company=self.login_user.company.id).count()

            if subjecte_count >= 10 and subject.subject_name != "デフォルト":
                print("------------------- 超えています")
                subject_lists.append(subject.id)

            queryset = SubjectManagement.objects.filter(Q(subject_reg_company=self.login_user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date').exclude(id__in=subject_lists)


        super(TrainingUpdateForm, self).__init__(*args, **kwargs)

        # コース
        self.fields['subject'] = forms.ModelChoiceField(
            label="コース",
            required=False,
            # empty_label='デフォルト',
            empty_label=None,
            # queryset=SubjectManagement.objects.filter(Q(subject_reg_company=self.user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')
            queryset=queryset
        )

        # グループ
        self.fields['destination_group'] = forms.ModelMultipleChoiceField(
            required=True,
            label="グループ",
            # queryset=CustomGroup.objects.filter(group_reg_user=self.login_user.id, tempo_flg=False),
            queryset=CustomGroup.objects.filter(group_reg_user=self.login_user.id),
            widget = User_Group_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple
        )

        self.fields['destination_group'].error_messages.update({
            'required': 'グループの選択は必須です。',
        })

    title = forms.CharField(
        required=True,
        label='タイトル',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'タイトルを入力してください',

                }
        )
    )

    description = forms.CharField(
        required=True,
        label="説明文",

        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                }
        )
    )


    start_date = forms.DateTimeField(
        required=False,
        label="開始日",
        widget=datetimepicker.DateTimePickerInput(

            format='%Y/%m/%d %H:%M:%S', options={
                'locale': 'ja',
                'dayViewHeaderFormat': 'YYYY年 MMMM',
                'tooltips': {
                            'close': '閉じる',

                            'selectMonth': '月を選択',

                            'prevMonth': '前の月',

                            'nextMonth': '次の月',

                            'selectYear': '年を選択',

                            'prevYear': '前の年',

                            'nextYear': '次の年',

                            'selectTime': '時間を選択',

                            'selectDate': '日付を選択',

                            'prevDecade': '前の期間',

                            'nextDecade': '次の期間',

                            'selectDecade': '期間を選択',

                            'prevCentury': '前世紀',

                            'nextCentury': '次世紀',

                            'today':'今日の日付',

                            'clear':'削除'

                            }

            }
        ),
        input_formats=['%Y/%m/%d %H:%M:%S']
    )

    end_date = forms.DateTimeField(
        required=True,
        label="終了日",
        widget=datetimepicker.DateTimePickerInput(

            format='%Y/%m/%d %H:%M:%S', options={
                'locale': 'ja',
                'dayViewHeaderFormat': 'YYYY年 MMMM',
                'tooltips': {
                            'close': '閉じる',

                            'selectMonth': '月を選択',

                            'prevMonth': '前の月',

                            'nextMonth': '次の月',

                            'selectYear': '年を選択',

                            'prevYear': '前の年',

                            'nextYear': '次の年',

                            'selectTime': '時間を選択',

                            'selectDate': '日付を選択',

                            'prevDecade': '前の期間',

                            'nextDecade': '次の期間',

                            'selectDecade': '期間を選択',

                            'prevCentury': '前世紀',

                            'nextCentury': '次世紀',

                            'today':'今日の日付',

                            'clear':'削除'

                            }

            }
        ),
        input_formats=['%Y/%m/%d %H:%M:%S']
    )



    # destination_group = forms.ModelMultipleChoiceField(
    #     required=True,
    #     label="グループ",
    #     queryset=CustomGroup.objects.filter(tempo_flg=False),
    #     widget = User_Group_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple
    # )

    expired_training_flg = forms.BooleanField(
        required=False,
        label='期限切れトレーニングの有効化・無効化切り替え',
    )

    # グループの編集が行われたかを識別するためのフラグ
    group_edit_check_flg = forms.BooleanField(
        required=False,
    )


    # 紐づけるグループユーザーを☑で表示する
    # group_user = forms.ModelMultipleChoiceField(

    #     required=True,
    #     label="グループユーザー",

    #     queryset=User.objects.filter(is_superuser=False, is_activate=True, is_active=True, is_staff=False),
    #     widget = User_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple

    # )


    # views.pyから送られてきたログインユーザーをpopで受け取る
    # def __init__(self, *args, **kwargs):
    #     self.user = kwargs.pop('user', None)
    #     super(TrainingUpdateForm, self).__init__(*args, **kwargs)

    #     # エラーメッセージをカスタマイズ
    #     self.fields['destination_group'].error_messages = {'required': 'グループの選択は必須です。'}


    def clean(self):

        cleaned_data = super().clean()

        # formに入力された値を取得
        sub_start_date = self.cleaned_data['start_date']
        print("---------- sub_start_date ---------", sub_start_date)
        print(type(sub_start_date))# <class 'datetime.datetime'>

        # 開始時刻が未設定(=None)の場合
        if sub_start_date is None:
            print("Noneだったよ")

            # 現在の時刻を代入
            sub_start_date = datetime.datetime.now(pytz.timezone('UTC'))
            print(type(sub_start_date))
        else:
            print("Noneじゃなかったよ")

        sub_end_date = self.cleaned_data['end_date']
        print("---------- sub_end_date ---------", sub_end_date)
        print(type(sub_end_date))# <class 'datetime.datetime'>

        dt2 = sub_end_date + datetime.timedelta(hours=12)
        print("---------- dt2 ---------", dt2)

        # 日付確認
        if sub_start_date > sub_end_date:
            raise forms.ValidationError('開始日時が終了日時よりも後に設定されています。')

        if sub_end_date < sub_start_date + datetime.timedelta(hours=12):
            raise forms.ValidationError('終了時間は開始日から12時間以上の時刻で設定してください。')

        return self.cleaned_data





"""
テストパーツの変更
"""
class PartsUpdateForm(forms.ModelForm):

    class Meta:
        model = Parts
        fields = ('title','description', 'title_detail', 'description_detail', 'pass_line', 'pass_text1', 'pass_text2', 'unpass_text1', 'unpass_text2',
                'is_required', 'is_question_random', 'answer_content_show')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.pk = kwargs.pop('pk', None)
        super(PartsUpdateForm, self).__init__(*args, **kwargs)


    title = forms.CharField(
        required=True,
        label='タイトル',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'タイトルを入力してください',

                }
        )
    )

    # 説明
    description = forms.CharField(
        required=True,
        label='説明',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # パーツ内に表示するタイトル
    title_detail = forms.CharField(
        required=True,
        label='パーツ内に表示するタイトル',
    )


    # パーツ内に表示する説明
    description_detail = forms.CharField(
        required=True,
        label='パーツ内に表示する説明',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 合格ライン
    pass_line = forms.IntegerField(
        required=False,
        label='合格ライン',
    )

    # 合格文1
    pass_text1 = forms.CharField(
        required=True,
        label='合格文1',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 合格文2
    pass_text2 = forms.CharField(
        required=False,
        label='合格文2',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 不合格文1
    unpass_text1 = forms.CharField(
        required=True,
        label='不合格文1',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # 不合格文2
    unpass_text2 = forms.CharField(
        required=False,
        label='不合格文2',
        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須ラベル',
    )

    # is_question_random
    is_question_random = forms.BooleanField(
        required=False,
        label='ランダム出題',
    )

    # テスト結果の〇✖表記の表示有無
    answer_content_show = forms.BooleanField(
        required=False,
        label='テスト結果の〇✖表記の表示有無',
    )




    def clean_title(self):
        title = self.cleaned_data['title']

        # PKを使ってDBから対象グループのオブジェトを取得
        parts_objects = Parts.objects.filter(pk=self.pk).first()

        parts_object_title = parts_objects.title

        # オブジェクトの名前(=DBに登録されていたタイトル)とname(=変更後のタイトル)を比較
        if parts_object_title == title:
            print("---------- 同じだよ")# 同じ場合は許可。
            return title

        else:
            # NGの場合は、変更後のタイトルで存在確認をして存在する場合はNG
            if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
                raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))
            return title



"""
アンケートパーツの変更
"""
class PartsQuestionnaireUpdateForm(forms.ModelForm):

    class Meta:
        model = Parts
        fields = ('title','description', 'title_detail', 'description_detail', 'is_required')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.pk = kwargs.pop('pk', None)
        super(PartsQuestionnaireUpdateForm, self).__init__(*args, **kwargs)


    title = forms.CharField(
        required=True,
        label='タイトル',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'タイトルを入力してください',

                }
        )
    )

    description = forms.CharField(
        required=True,
        label="説明文",

        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                }
        )
    )


    title_detail = forms.CharField(
        required=True,
        label="設問内のタイトル",

        widget=forms.Textarea(
            attrs={
                'class':'form-control',
                'rows': 5
                }
        )
    )


    description_detail = forms.CharField(
        required=True,
        label="設問内の説明文",

        widget=forms.Textarea(
            attrs={
                'class':'form-control',
                'rows': 5
                }
        )
    )

    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須ラベル',
    )


    def clean_title(self):
        title = self.cleaned_data['title']

        # PKを使ってDBから対象グループのオブジェトを取得
        parts_objects = Parts.objects.filter(pk=self.pk).first()

        parts_object_title = parts_objects.title

        # オブジェクトの名前(=DBに登録されていたタイトル)とname(=変更後のタイトル)を比較
        if parts_object_title == title:
            print("---------- 同じだよ")# 同じ場合は許可。
            return title

        else:
            # NGの場合は、変更後のタイトルで存在確認をして存在する場合はNG
            if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
                raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))
            return title


"""
動画パーツの変更
"""
class PartsMovieUpdateForm(forms.ModelForm):

    class Meta:
        model = Parts
        fields = ('title','description','is_required', 'duration')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.pk = kwargs.pop('pk', None)
        super(PartsMovieUpdateForm, self).__init__(*args, **kwargs)


    title = forms.CharField(
        required=True,
        label='タイトル',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'タイトルを入力してください',

                }
        )
    )

    description = forms.CharField(
        required=True,
        label="説明文",

        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                }
        )
    )

    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須ラベル',
    )

    # 視聴時間
    duration = forms.CharField(# datatime 時間だけ
        required=False,
        label='視聴時間',
    )


    def clean_title(self):
        title = self.cleaned_data['title']

        # PKを使ってDBから対象グループのオブジェトを取得
        parts_objects = Parts.objects.filter(pk=self.pk).first()

        parts_object_title = parts_objects.title

        # オブジェクトの名前(=DBに登録されていたタイトル)とname(=変更後のタイトル)を比較
        if parts_object_title == title:
            print("---------- 同じだよ")# 同じ場合は許可。
            return title

        else:
            # NGの場合は、変更後のタイトルで存在確認をして存在する場合はNG
            if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
                raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))
            return title



"""
ファイルパーツの変更
"""
class PartsFileUpdateForm(forms.ModelForm):

    class Meta:
        model = Parts
        fields = ('title','description','is_required',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.pk = kwargs.pop('pk', None)
        super(PartsFileUpdateForm, self).__init__(*args, **kwargs)


    title = forms.CharField(
        required=True,
        label='タイトル',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'タイトルを入力してください',

                }
        )
    )

    description = forms.CharField(
        required=True,
        label="説明文",

        widget=forms.Textarea(
            attrs={
                'placeholder': '説明文を入力してください',
                'class':'form-control',
                'rows': 5
                }
        )
    )


    # is_required
    is_required = forms.BooleanField(
        required=False,
        label='必須ラベル',
    )

    # 視聴時間
    duration = forms.CharField(# datatime 時間だけ
        required=False,
        label='視聴時間',
    )


    def clean_title(self):
        title = self.cleaned_data['title']

        # PKを使ってDBから対象グループのオブジェトを取得
        parts_objects = Parts.objects.filter(pk=self.pk).first()

        parts_object_title = parts_objects.title

        # オブジェクトの名前(=DBに登録されていたタイトル)とname(=変更後のタイトル)を比較
        if parts_object_title == title:
            print("---------- 同じだよ")# 同じ場合は許可。
            return title

        else:
            # NGの場合は、変更後のタイトルで存在確認をして存在する場合はNG
            if Parts.objects.filter(parts_user=self.user, title__iexact=title).exists():
                raise forms.ValidationError('「{0}」は既に存在するタイトルです。別のタイトルを入力してください。'.format(title))
            return title


"""
有効化制御変更
"""
class  ControlConditionsForm(forms.ModelForm):

    class Meta:
        model = ControlConditions
        fields = ('parts_origin','parts_destination')

    # views.pyから送られてきたトレーニングIDをpopで受け取る
    def __init__(self, *args, **kwargs):
        self.pk = kwargs.pop('pk', None)
        # print("------------- training_id ---------------", self.pk)

        super(ControlConditionsForm, self).__init__(*args, **kwargs)

        trainings = Training.objects.filter(pk=self.pk).first()

        # 依存元
        self.fields['parts_origin'] = forms.ModelChoiceField(label="依存元",
            queryset=trainings.parts.all(),
            required=False,
        )

        # 依存先
        self.fields['parts_destination'] = forms.ModelChoiceField(label="依存先",
            queryset=trainings.parts.all(),
            required=False,
        )


"""
管理者権限付与
"""
class IsStaffGiveForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.co_admin_user_lists = kwargs.pop('co_admin_user_lists', None)

        # 管理者と共同管理者を除外したユーザーのクエリーセットを作成
        queryset = User.objects.filter(is_superuser=False, is_staff=False, is_rogical_deleted=False).exclude(Q(service_admin__name="まなもあ")|Q(id__in=self.co_admin_user_lists))
        # print("--------- queryset", queryset)

        super(IsStaffGiveForm, self).__init__(*args, **kwargs)

    # ユーザー管理者権限
        # self.fields['co_admin_user'] = forms.ModelChoiceField(
        self.fields['is_staff'] = forms.ModelChoiceField(
            required=True,
            empty_label=None,#初期表示の「--------」を消す
            label="管理者",
            # queryset=User.objects.filter(is_superuser=False, is_staff=False, is_rogical_deleted=False).exclude(service_admin__name="まなもあ"),
            queryset=queryset,
            widget=forms.Select(
                attrs={
                    'class':'form-control',
                    'multiple':'multiple',
                    'size':'20',
                    'title':'is_staff[]'
                    }
                )
        )


"""
共同管理者権限付与
"""
class IsCoAdminGiveForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.co_admin_user_lists = kwargs.pop('co_admin_user_lists', None)
        self.admin_user_company = kwargs.pop('admin_user_company', None)

        # print("--------- self.admin_user_company", self.admin_user_company)

        # queryset = User.objects.filter(is_superuser=False, is_staff=False, is_rogical_deleted=False).exclude(Q(service_admin__name="まなもあ")|Q(id__in=self.co_admin_user_lists))
        queryset = User.objects.filter(company=self.admin_user_company, is_superuser=False, is_staff=False, is_rogical_deleted=False).exclude(Q(service_admin__name="まなもあ")|Q(id__in=self.co_admin_user_lists))
        print("--------- queryset", queryset)# <QuerySet [<User: 比嘉 連 / 69523HIGA@test.jp>]>

        super(IsCoAdminGiveForm, self).__init__(*args, **kwargs)

        # ユーザー管理者権限
        self.fields['co_admin_user'] = forms.ModelChoiceField(
            required=True,
            empty_label=None,#初期表示の「--------」を消す
            label="共同管理者",
            queryset=queryset,
            widget=forms.Select(
                attrs={
                    'class':'form-control',
                    'multiple':'multiple',
                    'size':'20',
                    'title':'is_staff[]'
                    }
                )
        )


"""
ゲストユーザー登録フォーム(使ってない)
"""
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        # fields = ["display_name", "email", "password1", "password1", "company"]
        fields = ["display_name", "email", "company"]

"""
ゲストユーザー登録フォーム
"""
class RegisterGuestUserForm(forms.ModelForm):

        guest_user_password = forms.CharField(
            label='パスワード',
            required=True,
            widget=forms.PasswordInput(),
        )

        # モデルに定義していない「確認用パスワード」フィールドを追加
        guest_user_password_2 = forms.CharField(
            label='確認用パスワード',
            required=True,
            widget=forms.PasswordInput(),
        )

        class Meta:
            model = GuestUserManagement
            fields = ('guest_user_name', 'email', 'company_name', 'guest_user_password',)
            # widgets = {
            #     'guest_user_password' : forms.PasswordInput(attrs={'placeholder': 'パスワード'})
            # }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['guest_user_name'].widget.attrs = {'placeholder': '山田太郎'}
            self.fields['email'].required = True
            self.fields['email'].widget.attrs = {'placeholder': 'mail@example.com'}
            self.fields['company_name'].widget.attrs = {'placeholder': '例) ○○○株式会社'}

        # パスワードの一致
        def clean(self):
            super().clean()
            guest_user_password = self.cleaned_data['guest_user_password']
            guest_user_password_2 = self.cleaned_data['guest_user_password_2']

            if guest_user_password != guest_user_password_2:
                raise forms.ValidationError('パスワードと確認用パスワードが合致しません。')


"""
ゲストユーザー変更フォーム
"""
class UpdateGuestUserForm(forms.ModelForm):

        class Meta:
            model = GuestUserManagement
            fields = ('guest_user_name', 'email', 'company_name',)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['guest_user_name'].widget.attrs = {'placeholder': '山田太郎'}
            self.fields['email'].required = True
            self.fields['email'].widget.attrs = {'placeholder': 'mail@example.com'}
            self.fields['company_name'].widget.attrs = {'placeholder': '例) ○○○株式会社'}


"""
パスワード変更フォーム
"""
# class PasswordUpdateForm(PasswordChangeForm):
class PasswordUpdateForm(forms.ModelForm):

    guest_user_password = forms.CharField(
        label='現在のパスワード',
        required=True,
        widget=forms.PasswordInput(),
    )

    # モデルに定義していないフィールドを追加
    new_password1 = forms.CharField(
        label='新しいパスワード',
        required=True,
        widget=forms.PasswordInput(),
    )

    new_password2 = forms.CharField(
        label='新しいパスワード(確認用)',
        required=True,
        widget=forms.PasswordInput(),
    )

    class Meta:
        model = GuestUserManagement
        fields = ('guest_user_password',)

    # views.pyから送られてきた情報をpopで受け取る
    def __init__(self, *args, **kwargs):
        self.guest_user_id = kwargs.pop('guest_user_id', None)
        print("------------- guest_user_id", self.guest_user_id)
        super(PasswordUpdateForm, self).__init__(*args, **kwargs)

    # 入力したパスワードが現在のパスワードと一致しているかチェック
    def clean(self):
        super().clean()

        # 現在のパスワード(formに入力したもの)
        current_password = self.cleaned_data['guest_user_password']
        print("------------- current_password ", current_password)

        # ゲストユーザーの情報
        guest_user = GuestUserManagement.objects.filter(id=self.guest_user_id).first()
        print("------------- guest_user_password", guest_user.guest_user_password)

        if not check_password(current_password, guest_user.guest_user_password):
        # if not guest_user.check_password(current_password):
            print("パスワードが一致しない")
            raise forms.ValidationError('現在のパスワードが間違っています。')


"""
ゲストユーザーをトレーニングに紐づける用のフォーム
"""
class GuestUserLinkForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.guest_user_lists = kwargs.pop('guest_user_lists', None)
        print("--------- self.guest_user_lists", self.guest_user_lists)

        self.admin_user = kwargs.pop('admin_user', None)
        print("--------- self.admin_user", self.admin_user)

        queryset = GuestUserManagement.objects.filter(resister_user=self.admin_user, is_active=True, is_rogical_deleted=False)
        print("--------- queryset", queryset)

        super(GuestUserLinkForm, self).__init__(*args, **kwargs)

    # ゲストユーザー
        self.fields['guest_user_name'] = forms.ModelChoiceField(
            required=True,
            empty_label=None,#初期表示の「--------」を消す
            label="ゲストユーザー",
            queryset=queryset,
            widget=forms.Select(
                attrs={
                    'class':'form-control',
                    'multiple':'multiple',
                    'size':'20',
                    'title':'guest_user[]'
                    }
                )
        )


"""
コース登録、変更
"""
class SubjectManagementForm(forms.ModelForm):

    class Meta:
        model = SubjectManagement
        # fields = ('subject_name', 'subject_reg_training')
        fields = ('subject_name', 'target', 'objective', 'duration')

    # views.pyから送られてきたログインユーザーをpopで受け取る
    def __init__(self, *args, **kwargs):
        self.login_user = kwargs.pop('login_user', None)
        self.url = kwargs.pop('url_name', None)
        self.pk = kwargs.pop('pk', None)
        super(SubjectManagementForm, self).__init__(*args, **kwargs)

        # コース名
        # self.fields['subject_name'] = forms.CharField(
        #     label='コース名',
        # )

        # # 対象者
        # self.fields['target'] = forms.CharField(
        #     label='対象者',
        # )

        # # 目的
        # self.fields['objective'] = forms.CharField(
        #     label='目的',
        # )

        # # 所要時間
        # self.fields['duration'] = forms.CharField(
        #     label='所要時間',
        # )

        # 紐づけるトレーニングを☑で表示する
        # self.fields['subject_reg_training'] = forms.ModelMultipleChoiceField(
        #     required=True,
        #     label="トレーニング",
        #     queryset=Training.objects.filter(reg_user=self.login_user),# ログインユーザーはリストから除外
        #     widget = Training_Checkbox # 複数選択チェックボックスへ変更。デフォルトはSelectMultiple
        # )

        # エラーメッセージをカスタマイズ
        # self.fields['subject_reg_training'].error_messages = {'required': 'トレーニングの選択は必須です。'}


    def clean_subject_name(self):
        subject_name = self.cleaned_data['subject_name']

        # URL名がsubject_management_create（SubjectManagementCreateView）の場合
        if self.url == 'subject_management_create':
            print("------ コース作成 -------")

            # コース名の存在確認
            if SubjectManagement.objects.filter(subject_reg_user=self.login_user, subject_name=subject_name).exists():
                raise forms.ValidationError('「{0}」は既に存在するコース名です。別のコース名を入力してください。'.format(subject_name))
            return subject_name

        # URL名がsubject_management_update（subject_management_update）の場合
        else:
            print("------ コース変更 -------")

            # PKを使ってDBから対象グループのオブジェトを取得
            subject_objects = SubjectManagement.objects.filter(pk=self.pk).first()
            subject_objects_name = subject_objects.subject_name

            # オブジェクトの名前(=DBに登録されていたコース名)とsubject_name(=変更後のコース名)を比較
            if subject_objects_name == subject_name:
                # 同じ場合は許可。
                return subject_name
            else:
                # 同じじゃない場合は変更後のコース名で存在確認。すでに存在する場合はエラーを返す
                if SubjectManagement.objects.filter(subject_reg_user=self.login_user, subject_name=subject_name).exists():
                    raise forms.ValidationError('「{0}」は既に存在するコース名です。別のコース名を入力してください。'.format(subject_name))
                return subject_name


    subject_name = forms.CharField(
        required=True,
        label='コース名',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'コース名を入力してください',
                'class':'require_label'
                # 'maxlength': 10
            }
        )
    )

    target = forms.CharField(
        required=False,
        label='対象者',
        widget=forms.TextInput(
            attrs={
                'placeholder': '対象者を入力してください 例)新卒入社後、総務課に配属された全従業員',
                'class':'require_label'
                # 'maxlength': 10
            }
        )
    )

    objective = forms.CharField(
        required=False,
        label='目的',
        widget=forms.Textarea(
            attrs={
                'placeholder': '目的を入力してください 例)配属後、必須業務の独り立ち',
                'class':'form-control',
                # 'id': 'training_description',
                'rows': 5
                # 'maxlength': 10
                }
        )
    )

    duration = forms.CharField(
        required=False,
        label='所要時間',
        widget=forms.TextInput(
            attrs={
                'placeholder': '所要時間を入力してください 例)約一週間',
                'class':'require_label'
                # 'maxlength': 10
                }
        )
    )

