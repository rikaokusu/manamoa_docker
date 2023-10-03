from django.shortcuts import render

from django.views.generic import View, ListView, DetailView, TemplateView, FormView, CreateView, UpdateView, DeleteView
from django.views.generic.base import ContextMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

# settings情報の取得
from django.conf import settings

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.hashers import make_password, check_password

from accounts.models import User, Service
from accounts.models import Company
from training.models import Training, TrainingRelation, Question, Choice
from training.models import FileManage
from training.models import QuestionnaireQuestion, QuestionnaireChoice
from training.models import QuestionnaireResult
from training.models import QuestionResult
from training.models import Parts, PartsManage
from training.models import TrainingManage
# from training.models import Notification
from training.models import Test
from training.models import File
from training.models import Movie
from training.models import Poster
from training.models import Image
from training.models import CustomGroup
from training.models import ControlConditions
from training.models import TrainingHistory
from training.models import ResourceManagement
from training.models import FolderIsOpen
from training.models import CoAdminUserManagement, CoAdminUserManagementRelation
from training.models import GuestUserManagement
from training.models import SubjectManagement
from training.models import SubjectImage
from training.models import TrainingDoneChg
from training.models import TrainingDone
from training.models import UserCustomGroupRelation


from .forms import TestQuestionForm, _QuestionnaireQuestionForm, CreateTrainingForm, AdminTestForm, AdminQuestionnaireForm, AdminMovieForm, AdminFileForm, TestUpdateForm
from .forms import CSVUploadForm, QuestionForm, ChoiceFormSet, QuestionnaireQuestionForm, QuestionnaireChoice, QuestionnaireChoiceFormSet, CustomGroupForm, CustomGroupBulkCreationForm
from .forms import TrainingUpdateForm, PartsUpdateForm, PartsQuestionnaireUpdateForm, PartsMovieUpdateForm, PartsFileUpdateForm, ControlConditionsForm, IsStaffGiveForm
from .forms import IsCoAdminGiveForm
from .forms import RegisterGuestUserForm, UpdateGuestUserForm, PasswordUpdateForm, GuestUserLinkForm, SignUpForm

from training.forms import ReminderForm, SubjectManagementForm, UserCustomGroupMultiForm, UserCustomGroupRelationForm

# 逆参照のテーブルをフィルタやソートする
from django.db.models import Prefetch, Exists

# AjaxでJSONを返す
from django.http import JsonResponse
import json

# 時刻取得
from datetime import datetime, timedelta
# import datetime
import pytz


# 一括ダウンロード
from django.http import HttpResponse
import zipfile

# 一括ダウンロードでデータを扱う
import io

# URLデコードするためのライブラリ
import urllib.parse

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect

# シリアライズ
from django.core import serializers

# CSV
import csv
import io
import uuid
from django.db import IntegrityError
from django.db import transaction

# OR検索
from django.db.models import Q

# フロントへメッセージ送信
from django.contrib import messages

# メール並列処理
import threading
from django.core.mail import send_mail

# テンプレートの読み込み
from django.template.loader import get_template
# サイトの取得
from django.contrib.sites.shortcuts import get_current_site

import traceback

# 多言語化
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

# rest_framework
from rest_framework.views import APIView
# from rest_framework import status
# from rest_framework.response import Response

# method_decorator
from django.utils.decorators import method_decorator

# login_required
from django.contrib.auth.decorators import login_required

from django.urls import reverse_lazy

from django.urls.resolvers import get_resolver

import logging

from django.db.models import Q

logger = logging.getLogger(__name__)

import uuid

# ランダムな文字列を生成
import random, string
from django.utils.crypto import get_random_string

import os
from json import loads

# テスト結果保存モデル
from django.db.models import Case, When

# 日付(=year, month, week)の加算、減算
# ※日にち単位の計算の場合はtimedeltaを使う
from dateutil.relativedelta import relativedelta

# シリアライザー
# from .serializers import *

# from rest_framework.generics import RetrieveAPIView, ListAPIView
# from rest_framework import status
from rest_framework.response import Response

# テンポラリ
import tempfile

# 小数点以下を切り捨て
import math




# 全てで実行させるView
class CommonView(ContextMixin):

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):

        print("----------------- CommonView")
        print("----------------- self.request.user", self.request)

        context = super().get_context_data(**kwargs)

        # current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        current_user = User.objects.filter(pk=self.request.user.id).first()
        print("----------------- current_user CommonView", current_user)

        # ゲストユーザー
        # current_guest_user = GuestUserManagement.objects.filter(pk=self.request.user.id).select_related().get()
        current_guest_user = GuestUserManagement.objects.filter(email='tanaka@test.com').first()
        print("----------------- current_guest_user CommonView", current_guest_user)

        context["current_user"] = current_user
        context["current_guest_user"] = current_guest_user

        if current_user:
            # メールアドレスをユーザ名とドメインに分割
            email_list = current_user.email.rsplit('@', 1)
            email_domain = email_list[1]

            context["current_user"] = current_user
            context["email_domain"] = email_domain


            # アクセスしているURLとAPPを取得
            url_name = self.request.resolver_match.url_name
            app_name = self.request.resolver_match.app_name

            context["url_name"] = url_name
            context["app_name"] = app_name

            is_app_admin = current_user.service_admin.filter(name=settings.TRAINING).exists()
            print("システム管理者", is_app_admin)

            context["is_app_admin"] = is_app_admin

        elif current_guest_user:
            # メールアドレスをユーザ名とドメインに分割
            email_list = current_guest_user.email.rsplit('@', 1)
            email_domain = email_list[1]
            print("email_domain", email_domain)# test.com

            context["current_user"] = current_guest_user
            context["email_domain"] = email_domain

            # アクセスしているURLとAPPを取得
            url_name = self.request.resolver_match.url_name
            app_name = self.request.resolver_match.app_name
            print("url_name", url_name)# guest_training
            print("app_name", app_name)# training

            context["url_name"] = url_name
            context["app_name"] = app_name

        return context


# トレーニングの対応完了をチェックする
class TraningStatusCheckView(ContextMixin):

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):

        print("----------------- TraningStatusCheckView")

        context = super().get_context_data(**kwargs)

        # 一般ユーザー
        current_user = User.objects.filter(pk=self.request.user.id).first()

        # ログインしているユーザーが所属しているグループを取得
        groups = UserCustomGroupRelation.objects.filter(group_user__in=[current_user.id])

        group_lists = []

        # グループのIDを取得
        group_lists_raw = list(groups.values_list('group_id', flat=True))

        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_lists.append(group_uuid_string)

        # グループリストに一致するグループが紐づくトレーニングを取得
        trainings = TrainingRelation.objects.filter(group_id__in=group_lists)

        training_list = []
        training_lists_raw = list(trainings.values_list('training_id', flat=True))
        # IDをstrに直してリストに追加
        for training_uuid in training_lists_raw:
            training_uuid_string = str(training_uuid)
            training_list.append(training_uuid_string)

        trainings = Training.objects.filter(id__in=training_list).order_by('status','end_date') \
        .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

        if current_user:
            for training in trainings:

                # 初期化
                parts_status = []
                parts_count = ""

                # 受講必須のパーツ用
                parts_is_required_status = []
                parts_is_required_count = ""

                # パーツの数を取得
                parts_count = training.parts.all().count()

                # is_requiredがtrueになっているパーツの数を取得
                qs = training.parts.all()
                parts_is_required_count = qs.filter(is_required=True).count()

                for parts in training.parts.all():
                    # ユーザーのPartsManageを取得
                    parts_manage = parts.parts_manage.filter(user=current_user.id).first()

                    if parts_manage:
                        # PartsManageのステータスを追加
                        parts_status.append(parts_manage.status)
                    else:
                        parts_status.append(1)

                    if parts_manage.is_parts_required:
                        parts_is_required_status.append(parts_manage.status)

                # トレーニングごとのユーザーのTrainingManageを取得
                training_manage = training.training_manage.filter(user=current_user.id).first()

                # ユーザーのTrainingHistoryを取得
                training_history = training.training_history.filter(user=current_user.id).first()

                # training_manageのチェック
                if training_manage:

                    if parts_is_required_count:
                        # print("is_required_count")

                        # パーツの数とparts_manageのstatusの数を比較
                        if (parts_is_required_count == parts_is_required_status.count(0)):
                            # print("----------------- 未対応 aaa")

                            training_manage.status = 1 #未対応
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 1 #未対応
                                training_history.save()

                        # パーツの数とparts_manageのstatusの数を比較
                        elif (parts_is_required_count == parts_is_required_status.count(3)):
                            # print("----------------- 完了")

                            training_manage.status = 3 #完了
                            training_manage.done_date = datetime.now()
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 3 #完了
                                training_history.done_date = datetime.now()
                                training_history.save()

                        # 全パーツの数と未対応パーツ数が同じ場合は未対応
                        elif (parts_is_required_count == parts_is_required_status.count(1)):
                            # print("----------------- 未対応")

                            training_manage.status = 1 #未対応
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 1 #未対応
                                training_history.done_date = datetime.now()
                                training_history.save()

                        # それ以外は対応中
                        else:
                            # print("------------ それ以外は対応中")

                            training_manage.status = 2 #対応中
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 2 #対応中
                                training_history.done_date = datetime.now()
                                training_history.save()

                        training_manage.save()

                        if training_history:
                            # print("------------ training_historyがあったよ")
                            training_history.save()


                    else:
                        # print("not is_required_count")

                        # パーツの数とparts_manageのstatusの数を比較
                        if (parts_count == parts_status.count(0)):

                            training_manage.status = 1 #未対応
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 1 #未対応
                                training_history.save()

                        # パーツの数とparts_manageのstatusの数を比較
                        elif (parts_count == parts_status.count(3)):

                            training_manage.status = 3 #完了
                            training_manage.done_date = datetime.now()
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 3 #完了
                                training_history.done_date = datetime.now()
                                training_history.save()

                        # 全パーツの数と未対応パーツ数が同じ場合は未対応
                        elif (parts_count == parts_status.count(1)):

                            training_manage.status = 1 #未対応
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 1 #未対応
                                training_history.done_date = datetime.now()
                                training_history.save()

                        # それ以外は対応中
                        else:
                            training_manage.status = 2 #対応中
                            training_manage.save()

                            if training_history:
                                # TrainingHistoryを更新
                                training_history.status = 2 #対応中
                                training_history.done_date = datetime.now()
                                training_history.save()

                        training_manage.save()

                        if training_history:
                            training_history.save()

        return context


"""
ホーム画面 トレーニングの一覧が表示される
"""
# class TrainingTemplateView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
#     model = Training
#     template_name = 'training/training.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         print("----------------- TrainingTemplateView")

#         # 一般ユーザー
#         current_user = User.objects.filter(pk=self.request.user.id).first()
#         print("------------ current_user", current_user)

#         # ゲストユーザー
#         # guest_user = GuestUserManagement.objects.filter(pk=self.request.user.id).first()
#         # guest_user = GuestUserManagement.objects.filter(email='tanaka@test.com').first()
#         # print("------------ guest_user", guest_user)

#         # 開閉ボタンの状態を取得
#         folder_is_opens = FolderIsOpen.objects.filter(user_id=self.request.user.id)
#         print("------------ folder_is_opens", folder_is_opens)
#         context["folder_is_opens"] = folder_is_opens

#         # サマリで表示する用にトレーニングの各ステータス数を取得
#         # if current_user:
#         print("------------ current_userです")
#         # 一般ユーザー
#         training_manages_mitaiou = TrainingManage.objects.filter(user=current_user, status=1).count()
#         training_manages_taiou = TrainingManage.objects.filter(user=current_user, status=2).count()

#         context["training_manages_mitaiou"] = training_manages_mitaiou# 未対応
#         context["training_manages_taiou"] = training_manages_taiou# 対応中

#         # elif guest_user:
#         #     print("------------ guest_userです")
#         #     # ゲストユーザー
#         #     training_manages_mitaiou = TrainingManage.objects.filter(guest_user_manage=guest_user, status=1).count()
#         #     training_manages_taiou = TrainingManage.objects.filter(guest_user_manage=guest_user, status=2).count()

#         #     context["training_manages_mitaiou"] = training_manages_mitaiou# 未対応
#         #     context["training_manages_taiou"] = training_manages_taiou# 対応中

#         # 今日の日付を取得
#         today = datetime.now()

#         # 今日から1ヵ月後の日付を取得
#         today_after_1month = datetime.now() + relativedelta(months=1)

#         # 今月を取得
#         cm_st = today.replace(day=1)
#         nm_st = (today + relativedelta(months=1)).replace(day=1)
#         cm_ed = nm_st - timedelta(days=1)

#         # 先月
#         pm_st = (today - relativedelta(months=1)).replace(day=1)
#         pm_ed = cm_st - timedelta(days=1)

#         # 今日から1か月以内に完了したトレーニングを抽出
#         # if current_user:
#         # 一般ユーザー
#         training_manages_done_within_two_month  = TrainingManage.objects.filter(user=current_user, status=3, training__end_date__range=[today,today_after_1month]).count()
#         context["training_manages_done_within_two_month"] = training_manages_done_within_two_month

#         # elif guest_user:
#         #     # ゲストユーザー
#         #     training_manages_done_within_two_month  = TrainingManage.objects.filter(guest_user_manage=guest_user, status=3, training__end_date__range=[today,today_after_1month]).count()
#         #     context["training_manages_done_within_two_month"] = training_manages_done_within_two_month

#         # 完了済みのトレーニングを除いた対応期限が今日から1ヵ月後の日付以下のトレーニングを取得
#         # if current_user:
#         # 一般ユーザー
#         task_plan_3month = TrainingManage.objects.filter(user=current_user, training__end_date__range=[today,today_after_1month]).exclude(status="3")
#         context['task_plan_3month'] = task_plan_3month.count()
#         context['statement_end_date'] = task_plan_3month.order_by('training__end_date').first()

#         # elif guest_user:
#         #     # ゲストユーザー
#         #     task_plan_3month = TrainingManage.objects.filter(guest_user_manage=guest_user, training__end_date__range=[today,today_after_1month]).exclude(status="3")
#         #     context['task_plan_3month'] = task_plan_3month.count()
#         #     context['statement_end_date'] = task_plan_3month.order_by('training__end_date').first()

#         # トレーニングに紐づくグループの中にログインしているユーザーが存在するかチェック
#         # ログインしているユーザーが所属しているグループを取得
#         # if current_user:
#         # 一般ユーザー
#         groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

#         # グループをリスト化
#         group_lists = []

#         group_lists_raw = list(groups.values_list('pk', flat=True))

#         for group_uuid in group_lists_raw:
#             group_uuid_string = str(group_uuid)
#             group_lists.append(group_uuid_string)

#         # ユーザーに紐づいているトレーニングの数を抽出
#         user_trainings = Training.objects.filter(destination_group__in=group_lists, training_manage__user=current_user).order_by('status','end_date').distinct().count()
#         context["user_trainings"] = user_trainings

#         # elif guest_user:
#         #     # ユーザーに紐づいているトレーニングの数を抽出
#         #     user_trainings = Training.objects.filter(destination_guest_user=guest_user, training_manage__guest_user_manage=guest_user).order_by('status','end_date').distinct().count()
#         #     context["user_trainings"] = user_trainings

#         # if current_user:
#             # ユーザーのトレーニングの表示の切り替えフラグがTrueの場合、完了済みのトレーニングを非表示
#         if current_user.is_training_done_chg:

#             trainings = Training.objects.filter(destination_group__in=group_lists, training_manage__user=current_user, training_manage__status__in=[1,2]).order_by('status','end_date').distinct() \
#             .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
#             print("--------------- if trainings", trainings)

#             context["trainings"] = trainings

#         # 完了済みのトレーニングを表示
#         else:
#             trainings = Training.objects.filter(destination_group__in=group_lists, training_manage__user=current_user).order_by('status','end_date').distinct() \
#             .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

#             context["trainings"] = trainings

#         # if guest_user:
#         #     # ゲストユーザーのトレーニングの表示の切り替えフラグがTrueの場合、完了済みのトレーニングを非表示
#         #     if guest_user.is_training_done_chg:

#         #         trainings = Training.objects.filter(destination_guest_user=guest_user, training_manage__guest_user_namage=guest_user, training_manage__status__in=[1,2]).order_by('status','end_date').distinct() \
#         #         .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
#         #         print("--------------- if trainings", trainings)

#         #         context["trainings"] = trainings

#         #     # 完了済みのトレーニングを表示
#         #     else:
#         #         trainings = Training.objects.filter(destination_guest_user=guest_user, training_manage__guest_user_namage=guest_user).order_by('status','end_date').distinct() \
#         #         .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

#         #         context["trainings"] = trainings

#         for key in list(self.request.session.keys()):
#             if not key.startswith("_"):
#                 del self.request.session[key]

#         return context


"""
ホーム画面 コースの一覧が表示される
"""
class SubjectTemplateView(LoginRequiredMixin, ListView, CommonView):
    model = SubjectManagement
    template_name = 'training/subject.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        print("----------------- SubjectTemplateView")

        # 一般ユーザー
        current_user = User.objects.filter(pk=self.request.user.id).first()
        print("------------ current_user 名前", current_user)
        print("------------ current_user 会社", current_user.company)

        user_service_admins = User.objects.filter(company=current_user.company, service_admin__name="まなもあ").first()
        # print("------------ 管理者", user_service_admins)

        # subjectes = SubjectManagement.objects.filter(Q(subject_reg_user=self.request.user.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')
        subjectes = SubjectManagement.objects.filter(Q(subject_reg_company=self.request.user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')
        print("---------- subjectes", subjectes)
        context["subjectes"] = subjectes

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context


"""
コースに紐づいているトレーニングの一覧が表示される
"""
class SubjectTrainingTemplateView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/subject_training.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 一般ユーザー
        current_user = User.objects.filter(pk=self.request.user.id).first()
        # print("---------- current_user aaaaaaaaaaaaa", current_user) # 矢崎 花子 / 6595@test.jp
        # print("---------- current_user id", current_user.id) # 矢崎 花子 / 6595@test.jp
        # print("---------- self.kwargs['pk']", self.kwargs['pk']) # f06c043f-ec92-424e-9c3e-ec8b9f4a071a

        # コースを取得
        subject = SubjectManagement.objects.filter(id=self.kwargs['pk']).first()
        context["subject_id"] = subject.id

        # 開閉ボタンの状態を取得
        folder_is_opens = FolderIsOpen.objects.filter(user_id=self.request.user.id)
        context["folder_is_opens"] = folder_is_opens

        # サマリ表示　未対応
        training_manages_mitaiou = TrainingManage.objects.filter(subject_manage=self.kwargs['pk'], user=current_user.id, status=1).count()
        context["training_manages_mitaiou"] = training_manages_mitaiou

        # サマリ表示　対応中
        training_manages_taiou = TrainingManage.objects.filter(subject_manage=self.kwargs['pk'], user=current_user.id, status=2).count()
        context["training_manages_taiou"] = training_manages_taiou

        # 今日の日付を取得
        today = datetime.now()

        # 今日から1ヵ月後の日付を取得
        today_after_1month = datetime.now() + relativedelta(months=1)

        # 今月を取得
        # cm_st = today.replace(day=1)
        # nm_st = (today + relativedelta(months=1)).replace(day=1)
        # cm_ed = nm_st - timedelta(days=1)

        # 先月
        # pm_st = (today - relativedelta(months=1)).replace(day=1)
        # pm_ed = cm_st - timedelta(days=1)

        # 完了済み
        training_manages_done_within_two_month  = TrainingManage.objects.filter(subject_manage=self.kwargs['pk'], user=current_user.id, status=3, training__end_date__range=[today,today_after_1month]).count()
        context["training_manages_done_within_two_month"] = training_manages_done_within_two_month

        # 期限が近いトレーニング
        task_plan_3month = TrainingManage.objects.filter(subject_manage=self.kwargs['pk'], user=current_user.id, training__end_date__range=[today,today_after_1month]).exclude(status="3")

        # 件数
        context['task_plan_3month'] = task_plan_3month.count()

        # ○○日まで
        context['statement_end_date'] = task_plan_3month.order_by('training__end_date').first()

        groups = UserCustomGroupRelation.objects.filter(group_user__in=[current_user.id])
        print("------------------------ groups", groups)# <QuerySet [<CustomGroup: グループA>, <CustomGroup: グループE(女子のみ)>, <CustomGroup: グループB>]>

        # グループをリスト化
        group_lists = []
        group_lists_raw = list(groups.values_list('group_id', flat=True))
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_lists.append(group_uuid_string)

        training_relation = TrainingRelation.objects.filter(group_id__in=group_lists)
        print("------------------------ training_relation", training_relation)

        training_list = []
        training_lists_raw = list(training_relation.values_list('training_id', flat=True))
        for training_uuid in training_lists_raw:
            training_uuid_string = str(training_uuid)
            training_list.append(training_uuid_string)

        # コースごとにユーザーに紐づいているトレーニングの数を抽出
        user_training_count = TrainingManage.objects.filter(subject_manage=self.kwargs['pk'], user=current_user.id).count()
        print("------------------------ user_training_count", user_training_count)
        context["user_training_count"] = user_training_count

        # トレーニングの表示の切り替えを取得
        training_done_chg = TrainingDoneChg.objects.filter(user_id=current_user.pk, subject=subject).first()
        print("------------------------ training_done_chg", training_done_chg)

        # コースに登録されているトレーニングが0、かつトレーニングの表示の切り替えが登録されている場合は削除
        if user_training_count == 0:
            print("----- user_training_countが0")
            if training_done_chg:
                print("----- training_done_chgがある")
                training_done_chg.delete()

        # トレーニングの表示の切り替えが登録されている場合
        if training_done_chg:
            # ステータスが完了済みのトレーニングを除いたトレーニングを表示
            if training_done_chg.is_training_done_chg:
                print("--------------- if training_done_chg", training_done_chg)

                trainings = Training.objects.filter(subject=self.kwargs['pk'], id__in=training_list, training_manage__user=current_user.id, training_manage__status__in=[1,2]).order_by('status','end_date').distinct() \
                .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
                print("--------------- if trainings", trainings)

                context["trainings"] = trainings
                context["is_training_done_chg"] = training_done_chg.is_training_done_chg

            # ステータスが完了済みのトレーニングも含めた全てのトレーニングを表示
            else:
                print("--------------- else training_done_chg", training_done_chg)

                trainings = Training.objects.filter(subject=self.kwargs['pk'], id__in=training_list, training_manage__user=current_user.id).order_by('status','end_date').distinct() \
                .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
                print("--------------- else trainings", trainings)

                context["trainings"] = trainings

        else:
            print("--------------- else training_done_chg", training_done_chg)

            trainings = Training.objects.filter(subject=self.kwargs['pk'], id__in=training_list, training_manage__user=current_user.id).order_by('status','end_date').distinct() \
            .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
            print("--------------- else trainings", trainings)

            context["trainings"] = trainings


        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context




"""
ゲストユーザーホーム画面
"""
class GuestTemplateView(ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/training.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        print("----------------- GuestTemplateView")
        print("------------ self.request.user.id", self.request.user.id)# None

        # ゲストユーザー
        # guest_user = GuestUserManagement.objects.filter(pk=self.request.user.id).first()
        guest_user = GuestUserManagement.objects.filter(email='tanaka@test.com').first()
        print("------------ guest_user", guest_user)
        context["guest_user_id"] = guest_user.pk


        # 開閉ボタンの状態を取得
        folder_is_opens = FolderIsOpen.objects.filter(user_id=self.request.user.id)
        print("------------ folder_is_opens", folder_is_opens)
        context["folder_is_opens"] = folder_is_opens

        # サマリで表示する用にトレーニングの各ステータス数を取得
        training_manages_mitaiou = TrainingManage.objects.filter(guest_user_manage=guest_user, status=1).count()
        training_manages_taiou = TrainingManage.objects.filter(guest_user_manage=guest_user, status=2).count()
        context["training_manages_mitaiou"] = training_manages_mitaiou# 未対応
        context["training_manages_taiou"] = training_manages_taiou# 対応中

        # 今日の日付を取得
        today = datetime.now()

        # 今日から1ヵ月後の日付を取得
        today_after_1month = datetime.now() + relativedelta(months=1)

        # 今日から1か月以内に完了したトレーニングを抽出
        training_manages_done_within_two_month  = TrainingManage.objects.filter(guest_user_manage=guest_user, status=3, training__end_date__range=[today,today_after_1month]).count()
        context["training_manages_done_within_two_month"] = training_manages_done_within_two_month

        # 完了済みのトレーニングを除いた対応期限が今日から1ヵ月後の日付以下のトレーニングを取得
        task_plan_3month = TrainingManage.objects.filter(guest_user_manage=guest_user, training__end_date__range=[today,today_after_1month]).exclude(status="3")
        context['task_plan_3month'] = task_plan_3month.count()
        context['statement_end_date'] = task_plan_3month.order_by('training__end_date').first()

        # ゲストユーザーに紐づいているトレーニングの数を抽出
        # user_trainings = Training.objects.filter(destination_guest_user=guest_user, training_manage__guest_user_manage=guest_user).order_by('status','end_date').distinct().count()
        # print("------------ user_trainings", user_trainings)
        # context["user_trainings"] = user_trainings

        # ゲストユーザーのトレーニングの表示の切り替えフラグがTrueの場合、完了済みのトレーニングを非表示
        # if guest_user.is_training_done_chg:

        #     trainings = Training.objects.filter(destination_guest_user=guest_user, training_manage__guest_user_manage=guest_user, training_manage__status__in=[1,2]).order_by('status','end_date').distinct() \
        #     .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        #     print("--------------- if trainingsゲストユーザー", trainings)

        #     context["trainings"] = trainings

        # # 完了済みのトレーニングを表示
        # else:
        #     trainings = Training.objects.filter(destination_guest_user=guest_user, training_manage__guest_user_manage=guest_user).order_by('status','end_date').distinct() \
        #     .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        #     print("--------------- else trainingsゲストユーザー", trainings)

        #     context["trainings"] = trainings

        trainings = Training.objects.filter(destination_guest_user=guest_user, training_manage__guest_user_manage=guest_user).order_by('status','end_date').distinct() \
        .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        print("--------------- trainingsゲストユーザー", trainings)

        context["trainings"] = trainings

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context































"""
トレーニングの非表示(Ajax)
"""
class TrainingDoneChgAjaxView(View):

    def post(self, request):

        # URLパラメータから送られたきた相性IDを取得
        print("----------- トレーニングの非表示(Ajax)")

        # training_id = request.POST.get('training_id')
        # print("----------- training_id", training_id)# c5532fec-77f2-475c-bd76-197ff775693f

        done_disp_bool = request.POST.get('done_disp_bool')
        # print("----------- done_disp_bool", done_disp_bool)

        subject_id = request.POST.get('subject_id')
        print("----------- subject_id", subject_id)

        # ログインしているユーザーを取得
        user = User.objects.filter(pk=self.request.user.id).first()
        print("----------- user", user)# テストユーザー / user@user.com

        #コースを取得
        subject = SubjectManagement.objects.filter(id=subject_id).first()
        print("---------- subject", subject)# 研修コース1

        # TrainingDoneChgモデルからユーザーの
        training_done_chg = TrainingDoneChg.objects.filter(user_id=self.request.user.id, subject=subject).first()
        # training_done_chg = TrainingDoneChg.objects.filter(user_id=self.request.user.id, subject=subject_id).first()
        print("------------------------ training_done_chg", training_done_chg)

        if not training_done_chg:
            print("------------------------ training_done_chgないよ")
            # FolderIsOpenテーブルにオブジェクトを作成
            training_done_chg, created = TrainingDoneChg.objects.get_or_create(
                user_id = user.id,
                subject = subject,
                is_training_done_chg = False
            )

        # ゲストユーザーのID取得　※ゲストユーザーのログイン認証が未完成のため、実際には送られてきていない
        # guest_user_id = request.POST.get('guest_user_id')

        # ゲストユーザーを取得
        # if guest_user_id:
        #     guest_user = GuestUserManagement.objects.filter(pk=guest_user_id).first()

        # フラグがtrueの場合
        if done_disp_bool == "true":
            try:
                # if user:
                # インシデント非表示フラグをON
                training_done_chg.is_training_done_chg = True
                training_done_chg.save()

                # elif guest_user:
                #     # インシデント非表示フラグをON
                #     training_done_chg.is_training_done_chg = True
                #     training_done_chg.save()

                message = f'完了したトレーニングを非表示にします。'
                messages.success(self.request, message)

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "完了したトレーニングを非表示にします",
                                    # "training_id": training_id,
                                    "subject_id": subject_id,
                                    })

            except Exception as e:
                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })
        else:
            try:
                # if user:
                # インシデント非表示フラグをOFF
                training_done_chg.is_training_done_chg = False
                training_done_chg.save()

                # elif guest_user:
                    # インシデント非表示フラグをON
                    # training_done_chg.is_training_done_chg = False
                    # training_done_chg.save()

                message = f'完了したトレーニングを表示します。'
                messages.success(self.request, message)

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "完了したトレーニングを表示します",
                                    # "training_id": training_id,
                                    "subject_id": subject_id,
                                    })

            except Exception as e:
                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })


"""
トグルボタンの展開縮小ON/OFF(Ajax)
"""
class FolderIsOpenChangeAjaxView(View):

    def post(self, request):

        print("----------------FolderIsOpenChangeAjaxView")

        # POSTで送られてきたチェックの有無、トレーニングのIDを取得
        is_checked = request.POST.get('is_checked')
        training_id = request.POST.get('training_id')
        # guest_user_id = request.POST.get('guest_user_id')
        # print("----------------FolderIsOpenChangeAjaxView guest_user_id", guest_user_id)
        print("----------------FolderIsOpenChangeAjaxView is_checked", is_checked)
        print("----------------FolderIsOpenChangeAjaxView training_id", training_id)

        # ユーザーを取得
        # user = User.objects.filter(pk=self.request.user.id).select_related().get()
        user = User.objects.filter(pk=self.request.user.id).first()

        # ゲストユーザーを取得
        # guest_user = GuestUserManagement.objects.filter(pk=guest_user_id).first()
        # print("----------------FolderIsOpenChangeAjaxView guest_user", guest_user)
        # print("----------------FolderIsOpenChangeAjaxView guest_user.id", guest_user.id)

        # training_idと一致するトレーニングを取得
        training = Training.objects.filter(pk=training_id).first()

        if user:
            # FolderIsOpenテーブルにオブジェクトを作成
            folder_is_open, created = FolderIsOpen.objects.get_or_create(
                user_id = user.id,
                training = training,
            )
        # elif guest_user:
        #     folder_is_open, created = FolderIsOpen.objects.get_or_create(
        #         user_id = guest_user.id,
        #         training = training,
        #     )

        # チェックが付いてる場合(＋ボタン、展開)
        if is_checked == "true":
            try:
                # 完了フラグをON
                folder_is_open.is_open = True
                folder_is_open.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "フォルダを展開しました",
                                    "is_open":folder_is_open.is_open,
                                    })

            except Exception as e:

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })

        # チェックが付いていない場合(－ボタン、縮小)
        else:
            try:
                # 完了フラグをOFF
                folder_is_open.is_open = False
                folder_is_open.save()

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ok",
                                    "message": "フォルダを縮小しました",
                                    "is_open":folder_is_open.is_open,
                                    })

            except Exception as e:

                # メッセージを生成してJSONで返す
                return JsonResponse({"status": "ng",
                                    "message": str(e),
                                    })


"""
動画画面
"""
class MovieTemplateView(LoginRequiredMixin, DetailView, CommonView):
    model = Parts
    template_name = 'training/movie.html'
    context_object_name = "movie"


    def get_context_data(self, **kwargs):
        # print("------------------ 動画再生")

        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()# テストユーザー / user@user.com
        # print("------------------ current_user", current_user)

        parts_id = self.kwargs['pk']
        context["parts_id"] = parts_id

        parts = Parts.objects.filter(id=parts_id).first()

        # parts_manage = parts.parts_manage.filter(user=current_user, type=2).first() #2は動画
        parts_manage = parts.parts_manage.filter(user=current_user.id, type=2).first()
        # print("------------------ parts_manage", parts_manage)

        context["parts_manage"] = parts_manage

        return context


"""
テスト画面
"""
class TestView(LoginRequiredMixin, FormView, CommonView):
    model = Parts
    template_name = 'training/test_form.html'
    form_class = TestQuestionForm
    #Formは質問と回答の描画をwidgetで表現できなかったため実際にはつかっていない。

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        parts_id = self.kwargs['pk']

        parts = Parts.objects.filter(pk=parts_id).first()

        # ランダムソートさせる
        if parts.is_question_random:
            test = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("question_parts", queryset=Question.objects.order_by('?'))).first()

        # IDの順番通りにソートする
        else:
            test = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("question_parts", queryset=Question.objects.all().order_by('order'))).first()

        context["test"] = test

        choice_num = ["ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ"]
        context["choice_num"] = choice_num

        if 'answer_dict_json' in self.request.session:
            answer_dict_json = self.request.session['answer_dict_json']
            context["answer_dict_json"] = answer_dict_json

        return context



    def post(self, request, *args, **kwargs):

        # QuerydictをPythondictに変換、※answer_dict(=ユーザー側から送られてきた答え)
        answer_dict = dict(request.POST)

        # CSRFのキーと値を削除
        answer_dict.pop("csrfmiddlewaretoken")

        self.answer_dict = answer_dict

        return super().post(request, *args, **kwargs)


    def form_valid(self, form):

        answer_dict = {}
        for key, values in self.answer_dict.items():
            answer_dict[key] = [value for value in values]

        # POST送信された情報をセッションへ保存
        answer_dict_json = json.dumps(answer_dict,ensure_ascii=False)
        self.request.session['answer_dict_json'] = answer_dict_json

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('training:test_confirm', kwargs={'pk': self.kwargs['pk']}))


"""
テスト確認画面
"""
class TestConfirmView(LoginRequiredMixin, FormView, CommonView):
    model = Parts
    template_name = 'training/test_form_confirm.html'
    form_class = TestQuestionForm
    #Formは質問と回答の描画をwidgetで表現できなかったため実際にはつかっていない。

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # テスト画面で入力した内容をanswer_dict_jsonにセッションで一時的に保持
        answer_dict_json = self.request.session['answer_dict_json']
        context["answer_dict_json"] = answer_dict_json

        parts_id = self.kwargs['pk']

        json_dict = json.loads(answer_dict_json)

        # 出題文の並びをランダムにする
        key_list = list(json_dict.keys())

        key_list = [int(k) for k in key_list]

        # TestDoneViewのnumber_of_answersをランダム順に対応させるために渡す
        self.request.session['key_list'] = key_list

        parts = Parts.objects.filter(pk=parts_id).first()

        # ランダムソートさせる
        if parts.is_question_random:

            # Caseを使ってクエリーセットを取得
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(key_list)])
            q_querysets = Question.objects.filter(pk__in=key_list).order_by(preserved)

        # IDの順番通りにソートする
        else:
            q_querysets = Question.objects.filter(pk__in=key_list).order_by('order')

        context["q_querysets"] = q_querysets

        test = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("question_parts", queryset=Question.objects.all().order_by('order'))).first()
        context["test"] = test

        choice_num = ["ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ"]
        context["choice_num"] = choice_num

        return context

    def form_valid(self, form):
        print("---------- テスト確認画面 ---------")

        parts = Parts.objects.filter(pk = self.kwargs['pk']).first()
        print("--------------------", parts)

        answer_dict = {}

        # value_list = []

        a_dict = {}

        check_list = []

        # 今回生成される回答(=result)を保存するquerysetを宣言
        tmp_question_result = set()

        answer_dict_json = self.request.session['answer_dict_json']

        json_dict = json.loads(answer_dict_json)

        # number_of_answersをランダム順に対応させるためにTestDoneViewにkey_listをセッションで渡す
        key_list = list(json_dict.keys())
        key_list = [int(k) for k in key_list]

        self.request.session['key_list'] = key_list

        # 文字列の辞書型、リスト型を数値に変更
        for key, values in json_dict.items():

            # answer_dict[int(key)] = [int(value) for value in values]
            answer_dict[int(key)] = [str(value) for value in values]

            question = Question.objects.filter(pk=key).first()

            # テストの結果を保存するテーブルをquestion_resultに指定
            question_result = QuestionResult.objects.create(
                question = key, # テスト番号
                answer = values, # ユーザーの回答
                question_relation = question # 設問
            )

            # is_typeの形式をquestion_resultに格納
            question_result.is_type = question.is_multiple

            question_result.save()

            tmp_question_result.add(question_result)

            # 回答のチェック
            question = Question.objects.filter(parts=parts, pk=int(key)).prefetch_related(Prefetch("choice_set", queryset=Choice.objects.filter(is_correct=True))).first()

            choices = question.choice_set.all()

            # is_typeがtextareaの場合
            if question.is_multiple == 3 or question.is_multiple == 4:
                a_dict[question.id] = list(choices.values_list('text', flat=True))

                # DB上の回答とユーザーの回答を照合したものをresultに代入
                result = list(choices.values_list('text', flat=True)) == values
                check_list.append(result)

            # ラジオボタン＆チェックボックスの場合
            else:
                a_dict_db = []
                for choice in choices.values_list('pk', flat=True):
                    a_dict_db.append(choice)

                    for c in range(len(a_dict_db)):
                        a_dict_db[c] = str(a_dict_db[c])

                a_dict[question.id] = a_dict_db

                result = a_dict_db == values

                check_list.append(result)

        # ユーザーを取得
        current_user = User.objects.filter(pk=self.request.user.id).select_related().first()

        # ユーザーのPartsManageを取得
        user_parts_manage = PartsManage.objects.filter(user=current_user.id, parts=parts).first()
        print("---------- user_part_manage ---------", user_parts_manage)

        # if not PartsManage.objects.filter(user=current_user, parts=parts):
        if user_parts_manage:
            # print("---------- PartsManageがあったよ ---------")
            user_parts_manage.delete()

        # トレーニングのステータスを作成する
        question_manage = PartsManage.objects.create(
            order = parts.order,
            type = parts.type,
            parts = parts,
            user = self.request.user.id,
            # user = current_user,
        )

        # querysetを管理テーブルと紐付ける
        question_manage.question_result.set(tmp_question_result)
        question_manage.save()

        # セッションに「_(アンダースコア)以外のセッション情報があった場合削除
        self.request.session['check_list'] = check_list
        check_list = self.request.session['check_list']

        # pass_lineがNoneだった場合
        if parts.pass_line is None:
            parts.pass_line = 0

        # ユーザーのPartsManageを取得
        current_user_testmanage = PartsManage.objects.filter(user=current_user.id, parts=parts).first()
        # print("---------- current_user_testmanage ---------", current_user_testmanage)

        # ユーザーのPartsManageとTrainingManageを紐づける
        training = Training.objects.filter(parts=parts).first()
        # print("---------- training ---------", training)
        user_training_manage = TrainingManage.objects.filter(training=training, user=self.request.user.id).first()
        # print("---------- user_training_manage ---------", user_training_manage)
        # print("---------- parts_manage ---------", user_training_manage.parts_manage.all())

        user_training_manage.parts_manage.add(current_user_testmanage)
        # print("---------- parts_manage.all ---------", current_user_testmanage.parts_manage.all())


        # check_listのTrueの数がpass_line以上で合格
        if check_list.count(True) >= int(parts.pass_line):
            print("---------- 合格だったよ ---------")

            # 合格の場合はステータスを完了に更新
            current_user_testmanage.status = 3
            current_user_testmanage.save()

            self.request.session['test_result'] = "pass"

        # 不合格
        else:
            print("---------- 不合格だったよ ---------")

            # 不合格の場合はステータスを対応中に更新
            current_user_testmanage.status = 2
            current_user_testmanage.save()

            self.request.session['test_result'] = "unpass"

        return HttpResponseRedirect(reverse('training:test_done', kwargs={'pk': parts.id}))



"""
テスト完了画面
"""
class TestDoneView(LoginRequiredMixin, TemplateView, CommonView):
    model = Parts
    template_name = 'training/test_done.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # セッションから作成中の課題行を取得
        test_result = self.request.session['test_result']
        context["test_result"] = test_result

        parts_id = self.kwargs['pk']

        test = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("question_parts", queryset=Question.objects.all().order_by('order'))).first()
        context["test"] = test

        answer_dict_json = self.request.session['answer_dict_json']
        context['answer_dict_json'] = answer_dict_json



    # ランダムソートに対応したnumber_of_answersを取得

        key_list = self.request.session['key_list']

        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(key_list)])
        q_querysets = Question.objects.filter(pk__in=key_list).order_by(preserved)

        # q_querysetsに紐づくnumber_of_answersの値をリストにして変数に格納
        number_of_answers = [q['number_of_answers'] for q in q_querysets.values('number_of_answers')]

        # テンプレートに渡す
        context['number_of_answers'] = number_of_answers

        json_dict = json.loads(answer_dict_json)

        ansewer_text_dict = {}

        c_list = []

        a_list = []


        # 出題文とユーザーの回答をテキストの状態で辞書形式にする
        for key, value in json_dict.items():

            querysets = Question.objects.filter(pk=int(key))
            print("---------------- querysets", querysets)

            for q in querysets:
                print("---------------- q", q)# 龍潭池にいる鴨っぽい生き物の名前は？
                print("---------------- is_multiple", q.is_multiple)# 3
                print("---------------- value", value[0])# 竜

                # # リストの一つ目の値が2文字以上( ex. ["11"])だった場合　※この方法だと記述式問題で一文字で解答したときにエラーになる
                # if len(value[0]) >= 2:
                #     print("---------------- value if", value[0])
                #     # 記述式問題
                #     if q.is_multiple == 3 or q.is_multiple == 4:
                #         ansewer_text_dict[q.text] = value

                #     # ラジオボタン、チェックボックス
                #     else:
                #         choices = Choice.objects.filter(pk__in=value)
                #         a_list = list(choices.values_list('text', flat=True))
                #         ansewer_text_dict[q.text] = a_list

                # # ラジオボタン、チェックボックス
                # else:
                #     print("---------------- value else", value[0])
                #     choices = Choice.objects.filter(pk__in=value)
                #     c_list = list(choices.values_list('text', flat=True))
                #     ansewer_text_dict[q.text] = c_list



                # 記述式問題
                if q.is_multiple == 3 or q.is_multiple == 4:
                    ansewer_text_dict[q.text] = value

                # ラジオボタン、チェックボックス
                else:
                    choices = Choice.objects.filter(pk__in=value)
                    c_list = list(choices.values_list('text', flat=True))
                    ansewer_text_dict[q.text] = c_list

        context["ansewer_text_dict"] = ansewer_text_dict

        # True / falseのリスト
        check_list = self.request.session['check_list']
        context["check_list"] = check_list

        # セッションに保持されている値をクリアする(→更新するとセッションの中身がないためエラーがでる)
        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context


"""
ファイルダウンロードのチェック
"""
# @method_decorator(login_required, name = 'dispatch')
class FileDownloadStatus(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):
        print("---------- ファイルダウンロードのチェック ---------")

        is_type = request.POST.get('is_type')

        parts_id = request.POST.get('parts_id')

        parts = Parts.objects.filter(id=parts_id).prefetch_related('file').first()

        # トレーニングに紐づくコースを取得
        training = Training.objects.filter(parts=parts).first()
        subject = training.subject

        file_ids = []
        if is_type == "single":
            file_ids.append(request.POST.get('file_id'))
        elif is_type == "multiple":
            for file in parts.file.all():
                file_ids.append(file.file_id)
        else:
            print("なにもない")

        # print("------ file_ids", file_ids)

        current_user = User.objects.filter(pk=self.request.user.id).select_related().first()

        try:
            for file_id in file_ids:
                # ダウンロードフラグをONにする
                file_manage, created = FileManage.objects.get_or_create(
                    is_done = True,
                    file_id = file_id
                )

                # ダウンロード時間を保持して保存する
                file_manage.download_date = datetime.now()
                file_manage.save()

                # パーツのステータスを更新する
                # parts_manage, created = PartsManage.objects.get_or_create(
                #     order = parts.order,
                #     type = parts.type,
                #     parts = parts,
                #     # user = current_user,
                #     user = self.request.user.id,
                # )

                parts_manage = PartsManage.objects.filter(user=self.request.user.id, parts=parts).first()
                # print("---------- ファイルパーツのパーツマネージ ---------", parts_manage)

                # ダウンロードファイル管理オブジェクトを追加する
                parts_manage.file_manage.add(file_manage)

                # ユーザーのPartsManageとTrainingManageを紐づける
                training = Training.objects.filter(parts=parts).first()
                # print("---------- training ---------", training)
                user_training_manage = TrainingManage.objects.filter(training=training, user=self.request.user.id).first()
                # print("---------- user_training_manage ---------", user_training_manage)
                user_training_manage.parts_manage.add(parts_manage)
                # print("---------- parts_manage.all ---------", user_training_manage.parts_manage.all())


            # 全てのファイルがダウンロード済みか確認
            all_file_count = parts.file.all().count()
            downloaded_file_count = parts_manage.file_manage.all().count()
            # print("------ all_file_count", all_file_count)
            # print("------ downloaded_file_count", downloaded_file_count)

            if all_file_count == downloaded_file_count:

                parts_manage.status = 3 #対応完了

            elif downloaded_file_count >= 1:

                parts_manage.status = 2 #対応中

            elif downloaded_file_count == 0:

                parts_manage.status = 1 #未応中

            parts_manage.save()

            message = f'ダウンロードしました'
            messages.success(self.request, message)

        except Exception as e:
            logger.error(e)
            return JsonResponse({"status": "ng",
                                "message": str(e),
                                })

        return JsonResponse({"status": "ok",
                            "message": "ダウンロードしました",
                            "subject_pk": subject.pk
                            })




"""
動画再生のチェック
"""
# @method_decorator(login_required, name = 'dispatch')
class MoviePlayStatus(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):
        print("---------- 動画再生のチェック ---------")

        duration_str = request.POST.get('duration')
        current_time_str = request.POST.get('current_time')

        is_end = request.POST.get('is_end')

        parts_id = request.POST.get('parts_id')

        file_id = request.POST.get('file_id')

        parts = Parts.objects.filter(id=parts_id).first()

        current_user = User.objects.filter(pk=self.request.user.id).select_related().first()

        event_type = request.POST.get('event_type')

        if duration_str:
            duration_float = float(duration_str)
        else:
            duration_float = parts.movie_duration

        duration = duration_float * 1000000 #マイクロ秒


        current_time_float = float(current_time_str)
        current_time = current_time_float * 1000000 #マイクロ秒

        is_alert = None


        try:
            # パーツのステータスを更新する
            # movie_play_manage, created = PartsManage.objects.get_or_create(
            #     order = parts.order,
            #     type = parts.type,
            #     parts = parts,
            #     # user = current_user,
            #     user = self.request.user.id,
            #     movie_duration = duration,
            #     movie_file_id = file_id,
            # )
            # print("---------- movie_play_manage ---------", movie_play_manage)

            movie_play_manage = PartsManage.objects.filter(user=self.request.user.id, parts=parts).first()
            print("---------- 動画パーツのパーツマネージ ---------", movie_play_manage)

            # ユーザーのPartsManageとTrainingManageを紐づける
            training = Training.objects.filter(parts=parts).first()
            # print("---------- training ---------", training)
            user_training_manage = TrainingManage.objects.filter(training=training, user=self.request.user.id).first()
            # print("---------- user_training_manage ---------", user_training_manage)
            # print("---------- parts_manage ---------", user_training_manage.parts_manage.all())
            user_training_manage.parts_manage.add(movie_play_manage)
            # print("---------- parts_manage.all ---------", movie_play_manage.parts_manage.all())

            # 再生開始時の時間
            movie_play_manage.play_start_date = datetime.now()

            # 予想終了時間を取得
            # old_movie_play_manage = parts.parts_manage.filter(user=current_user, type=2).first() #2は動画
            old_movie_play_manage = parts.parts_manage.filter(user=current_user.id, type=2).first() #2は動画

            if is_end == "True" and event_type == "ended":

                if not event_type == "close":
                    # カレントタイムのリセット
                    movie_play_manage.current_time = 0

                # 予想終了時間と現在時間 + 1秒を比較して現在時間が未来時間かを確認(ミリ秒を切り捨てしているので1秒プラス)
                if old_movie_play_manage.expected_end_date:
                    expected_end_date = old_movie_play_manage.expected_end_date
                else:
                    expected_end_date = 0


                if datetime.now(pytz.timezone('UTC')) + timedelta(seconds=15) > expected_end_date:
                    movie_play_manage.status = 3 #対応完了

                    # カレントタイムのリセット
                    movie_play_manage.current_time = 0


                else:
                    is_alert = True

                    if old_movie_play_manage.status != 3:
                        movie_play_manage.status = 2 #対応中

                    # カレントタイムのリセット
                    movie_play_manage.current_time = 0


            elif event_type == "close":

                if old_movie_play_manage.status != 3:
                    movie_play_manage.status = 2 #対応中

                # カレント(再生時間)と再生そう時間が一緒の場合0にリセット
                if int(current_time_float) == int(duration_float):
                    movie_play_manage.current_time = 0
                else:
                    movie_play_manage.current_time = int(current_time_float)


            elif event_type == "pause":

                movie_play_manage.current_time = int(current_time_float)

            else:

                # 予想終了時間を保存
                movie_play_manage.expected_end_date = datetime.now() + timedelta(microseconds=duration) - timedelta(microseconds=current_time)


            movie_play_manage.save()


        except Exception as e:
            return JsonResponse({"status": "ng",
                                "message": str(e),
                                })

        return JsonResponse({"status": "ok",
                            "message": "ダウンロードしました",
                            "is_alert": is_alert,
                            })





"""
アンケート画面
"""
class QuestionnaireTemplateView(LoginRequiredMixin, FormView, CommonView):
    model = Parts
    template_name = 'training/questionnaire_form.html'
    form_class = _QuestionnaireQuestionForm
    #Formは質問と回答の描画をwidgetで表現できなかったため実際にはつかっていない。

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        parts_id = self.kwargs['pk']

        questionnaire = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("questionnairequestion_set", queryset=QuestionnaireQuestion.objects.all().order_by('order'))).first()

        context["questionnaire"] = questionnaire

        if 'questionnaire_dict_json' in self.request.session:
            questionnaire_dict_json = self.request.session['questionnaire_dict_json']
            context["questionnaire_dict_json"] = questionnaire_dict_json

        choice_num = ["ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ"]
        context["choice_num"] = choice_num

        return context



    def post(self, request, *args, **kwargs):

        form = self.get_form()

        # QuerydictをPythondictに変換
        questionnaire_dict = dict(request.POST)

        # CSRFのキーと値を削除
        questionnaire_dict.pop("csrfmiddlewaretoken")

        self.questionnaire_dict = questionnaire_dict

        return super().post(request, *args, **kwargs)


    def form_valid(self, form):

        questionnaire_dict = {}
        for key, values in self.questionnaire_dict.items():

            # print("------------------2", values)
            # print("------------------2", key)

            # comma_in = [s for s in values if ',' in s]
            # print('カンマが含まれている解答', comma_in)

            # if comma_in:
            #     print('カンマあるよ')
            #     for comma_in_text in comma_in:
            #         re_text = comma_in_text.replace(",", "、")# 承、太郎
            #     print('書きかえ', re_text)
            # else:
            #     print('カンマないよ')

            questionnaire_dict[key] = [value for value in values]
        print("------------------1", questionnaire_dict)





        # for value in questionnaire_dict.values():
        # for key, values in questionnaire_dict.items():
        #     # print("------------------2", values)
        #     # print("------------------2", key)

        #     for value in values:

        #         # カンマが含まれているか判定
        #         comma_in = [s for s in value if ',' in s]
        #         print('カンマが含まれている解答111111', comma_in)

        #         print('カンマが含まれているキー1', questionnaire_dict.get(comma_in))
        #         print('カンマが含まれているキー2', value.get(comma_in))

        #         if comma_in:
        #             print('カンマあるよ')
        #             for comma_in_text in comma_in:
        #                 re_text = comma_in_text.replace(",", "、")# 承、太郎
        #             print('書きかえ', re_text)
        #         else:
        #             print('カンマないよ')




        # POST送信された情報をセッションへ保存
        questionnaire_dict_json = json.dumps(questionnaire_dict,ensure_ascii=False)

        self.request.session['questionnaire_dict_json'] = questionnaire_dict_json

        # ステップ2へ遷移
        return HttpResponseRedirect(reverse('training:questionnaire_confirm', kwargs={'pk': self.kwargs['pk']}))


"""
アンケート確認画面
"""
class QuestionnaireConfirmView(LoginRequiredMixin, FormView, CommonView):
    model = Parts
    template_name = 'training/questionnaire_form_confirm.html'
    form_class = _QuestionnaireQuestionForm
    #Formは質問と回答の描画をwidgetで表現できなかったため実際にはつかっていない。


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # セッションから作成中の課題行を取得
        questionnaire_dict_json = self.request.session['questionnaire_dict_json']
        context["questionnaire_dict_json"] = questionnaire_dict_json

        parts_id = self.kwargs['pk']

        questionnaire = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("questionnairequestion_set", queryset=QuestionnaireQuestion.objects.all().order_by('order'))).first()

        context["questionnaire"] = questionnaire

        return context


    def form_valid(self, form):
        print("---------- アンケート確認画面 ---------")

        parts = Parts.objects.filter(pk = self.kwargs['pk']).first()

        questionnaire_dict_json = self.request.session['questionnaire_dict_json']

        questionnaire_dict = json.loads(questionnaire_dict_json)

        questionnaire_dict.pop("questionnaire_id")

        # 今回生成される回答(result)を保存するquerysetを宣言
        tmp_questionnaire_result = set()

        for key, value in questionnaire_dict.items():

            # テキストエリアが空の場合は未記入という値を代入する
            # ※バリデーションで未回答はできなくなっている
            if value[0] != "":
                value_valid = value
            else:
                value_valid ="未記入"

            questionnairequestion = QuestionnaireQuestion.objects.filter(pk=key).first()

            questionnaire_result = QuestionnaireResult.objects.create(
                question = key, # アンケート番号
                answer = value_valid, # ユーザーの回答
                questionnairequestion_relation = questionnairequestion # 設問
            )

            questionnaire_result.is_type = questionnairequestion.is_multiple_questionnaire

            questionnaire_result.save()

            # 生成された回答をquerysetに追加
            tmp_questionnaire_result.add(questionnaire_result)

        current_user = User.objects.filter(pk=self.request.user.id).select_related().first()

        # questionnaire_manage, created = PartsManage.objects.get_or_create(
        #     order = parts.order,
        #     type = parts.type,
        #     parts = parts,
        #     user = self.request.user.id,
        #     # user = current_user,
        #     status = 3
        # )

        questionnaire_manage = PartsManage.objects.filter(user=self.request.user.id, parts=parts).first()
        # print("---------- アンケートパーツのパーツマネージ ---------", questionnaire_manage)

        # PartsManageのステータスを更新
        questionnaire_manage.status = 3

        # ユーザーのPartsManageとTrainingManageを紐づける
        training = Training.objects.filter(parts=parts).first()
        # print("---------- training ---------", training)
        user_training_manage = TrainingManage.objects.filter(training=training, user=self.request.user.id).first()
        # print("---------- user_training_manage ---------", user_training_manage)
        user_training_manage.parts_manage.add(questionnaire_manage)
        # print("---------- parts_manage.all ---------", user_training_manage.parts_manage.all())


        # querysetを管理テーブルに紐付ける
        questionnaire_manage.questionnaire_result.set(tmp_questionnaire_result)
        questionnaire_manage.save()

        return HttpResponseRedirect(reverse('training:questionnaire_done'))



"""
アンケート完了画面
"""
class QuestionnaireDoneView(LoginRequiredMixin, TemplateView, CommonView):
    model = Parts
    template_name = 'training/questionnaire_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context





"""
一括(Zip)ダウンロード機能
"""
class FileDownloadZipView(View):

    def get(self, request, *args, **kwargs):
        # 対象課題のIDを取得
        pk = self.kwargs['pk']

        # ファイル情報を取得
        parts = Parts.objects.filter(pk = pk).prefetch_related('file').first()

        # レスポンスの生成
        response = HttpResponse(content_type='application/zip')
        # ダウンロードするファイル名を定義
        fn_on_space = "download"
        # 半角スペース削除
        fn = fn_on_space.replace(" ", "")
        response['Content-Disposition'] = 'filename="{fn}.zip"'.format(fn=urllib.parse.quote(fn))
        # メモリーに保存する
        buffer = io.BytesIO()

        # Zipファイルの生成
        zip = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)

        # Zipファイルに追加する
        for file in parts.file.all():
            zip.writestr(file.name, file.file.read())

        # Zipファイルをクローズ
        zip.close()

        # バッファのフラッシュ
        buffer.flush()

        # バッファの内容を書き出し
        ret_zip = buffer.getvalue()

        # バッファをクローズ
        buffer.close()

        # レスポンスに書き込み
        response.write(ret_zip)

        return response


"""
管理者権限設定画面
"""
class UserManagementView(LoginRequiredMixin, TemplateView, CommonView, FormView):
# class UserManagementView(LoginRequiredMixin, MultiFormsView):

    template_name = 'training/user_management.html'
    form_class = IsStaffGiveForm
    # form_classes = {'is_staff_give_form': IsStaffGiveForm,
    #                 'is_co_admin_give_form': IsCoAdminGiveForm,
    #                 }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ログインユーザーを取得
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user

        # 管理者のユーザーを取得
        user_service_admins = User.objects.filter(service_admin__name="まなもあ").order_by('created_date')
        context["user_service_admins"] = user_service_admins

        return context


    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(UserManagementView, self).get_form_kwargs()

        co_admin_user_lists = []

        # 共同管理者テーブルの全レコードを取得
        co_admins = CoAdminUserManagement.objects.all()
        print("--------- co_admins 管理者権限設定画面", co_admins)

        for co_admin in co_admins:

            # 共同管理者に指定されているユーザーを取り出す
            for co_admin_user in co_admin.co_admin_user.all():
                # リストにユーザーのIDを追加
                co_admin_user_lists.append(co_admin_user.pk)

        # formにリストを渡す
        kwargs.update({'co_admin_user_lists': co_admin_user_lists})
        return kwargs


    # 権限付与
    def post(self, request, *args, **kwargs):

        # POSTで送られてきた値を取得
        user_id_list = request.POST.getlist('is_staff')

        # pkと一致するユーザーを取得
        users = User.objects.filter(pk__in=user_id_list)

        # Online学習支援システムのサービスを取得
        service = Service.objects.filter(name="まなもあ")

        for user in users:
            # サービスと紐づける
            user.service_admin.set(service)
            # 保存
            user.save()

        message = f'ユーザーに権限を付与しました'
        messages.success(self.request, message)

        return HttpResponseRedirect(reverse('training:user_management'))


"""
管理者権限の削除(個別)
"""
class IsStaffDeleteView(View):

    def post(self, request, *args, **kwargs):

        user_id = self.kwargs['pk']

        user_obj = User.objects.filter(pk=user_id).first()

        service = Service.objects.filter(name="まなもあ").first()

        # service_adminを削除する
        user_obj.service_admin.remove(service)

        user_obj.save()

        # メッセージを返す
        messages.success(self.request, "管理者権限を取り消しました")

        return HttpResponseRedirect(reverse('training:user_management'))


"""
共同管理者権限設定画面
"""
class CoAdminManagementView(LoginRequiredMixin, TemplateView, CommonView, FormView):

    template_name = 'training/co_admin_management.html'
    form_class = IsCoAdminGiveForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ログインユーザーを取得
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user

        # 管理者のユーザーを取得
        # user_service_admins = User.objects.filter(service_admin__name="まなもあ")
        co_admin_user = CoAdminUserManagement.objects.filter(admin_user=current_user.id).first()
        # print("-------------- co_admin_user CoAdminManagementView", co_admin_user)# CoAdminUserManagement object (5)
        # print("-------------- co_admin_user.admin_user CoAdminManagementView", co_admin_user.admin_user)# 28caa177-ce84-411f-9775-bffc81d22075

        if co_admin_user:
            co_admin_users = CoAdminUserManagementRelation.objects.filter(admin_user_id=co_admin_user.admin_user)
            # print("-------------- co_admin_users CoAdminManagementView", co_admin_users)# <QuerySet [<CoAdminUserManagementRelation: CoAdminUserManagementRelation object (15)>]>

            # リスト化
            co_admin_users_list = []
            co_admin_users_list_raw_1 = list(co_admin_users.values_list('co_admin_user_id', flat=True))

            # IDをstrに直してリストに追加
            for co_admin_user_uuid_1 in co_admin_users_list_raw_1:
                co_admin_user_uuid_string_1 = str(co_admin_user_uuid_1)
                co_admin_users_list.append(co_admin_user_uuid_string_1)
            # print("---------- co_admin_users_list ---------", co_admin_users_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c']

            co_admin_users_qs = User.objects.filter(id__in=co_admin_users_list)
            # print("---------- co_admin_users_qs ---------", co_admin_users_qs)# <QuerySet [<User: 比嘉 太郎 / 69523@test.jp>]>

            # context["co_admin_users"] = co_admin_user.co_admin_user.all()
            context["co_admin_users"] = co_admin_users_qs

            # context["co_admin_user_count"] = co_admin_user.co_admin_user.count()
            context["co_admin_user_count"] = co_admin_users_qs.count()

        else:
            context["co_admin_user_count"] = 0

        return context

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(CoAdminManagementView, self).get_form_kwargs()

        co_admin_user_lists = []

        co_admin = CoAdminUserManagement.objects.filter(admin_user=self.request.user.id).first()
        # print("-------------- co_admin CoAdminManagementView", co_admin)
        # print("-------------- co_admin.admin_user CoAdminManagementView", co_admin.admin_user)# 28caa177-ce84-411f-9775-bffc81d22075

        # 共同管理者に指定されているユーザーを取り出す ここ
        if co_admin:
            co_admin_users = CoAdminUserManagementRelation.objects.filter(admin_user_id=co_admin.admin_user)
            # print("-------------- co_admin_users CoAdminManagementView", co_admin_users)# <QuerySet [<CoAdminUserManagementRelation: CoAdminUserManagementRelation object (15)>]>

            # for co_admin_user in co_admin.co_admin_user.all():
            for co_admin_user in co_admin_users:
                # print("-------------- co_admin_user CoAdminManagementView", co_admin_user)#  CoAdminUserManagementRelation object (15)
                # print("-------------- co_admin_user.co_admin_user_id CoAdminManagementView", co_admin_user.co_admin_user_id)# 6a9faafb-3fd8-4a2e-a096-9d1327b4397c

                # リストにユーザーのIDを追加
                # co_admin_user_lists.append(co_admin_user.pk)
                co_admin_user_lists.append(co_admin_user.co_admin_user_id)

        # formにリストを渡す
        kwargs.update({'co_admin_user_lists': co_admin_user_lists})

        # ログインしている管理者が所属する会社を取得
        kwargs.update({'admin_user_company': self.request.user.company})

        return kwargs


    # 共同権限付与
    # def form_valid(self, form):
    def post(self, request, *args, **kwargs):

        # ログインしている管理者の共同管理者のレコードを取得
        co_admin = CoAdminUserManagement.objects.filter(admin_user=self.request.user.id).first()
        print("----------- co_admin", co_admin)

        # ログインしている管理者を取得
        login_admin_user = User.objects.filter(pk=self.request.user.id).first()
        print("----------- login_admin_user", login_admin_user.id)

        # POSTで送られてきた値を取得
        user_id_list = request.POST.getlist('co_admin_user')
        print("----------- user_id_list", user_id_list)# ['5a2db03b-36a9-47ac-a525-976de599cf03'] 玉城 悠真 / 65961TAMA@test.jp

        # pkと一致するユーザーを取得
        users = User.objects.filter(pk__in=user_id_list)
        print("----------- users", users)# <QuerySet [<User: 玉城 悠真 / 65961TAMA@test.jp>]>

        # 共同管理者のレコードが存在しない場合
        if co_admin is None:
            print("----------- co_adminがNoneだよ")

            # ログインしている管理者のレコードを新しく作成する
            co_admin = CoAdminUserManagement.objects.create(
                admin_user = login_admin_user.id
            )

            # 保存
            co_admin.save()

            # 共同管理者として紐づける
            # co_admin.co_admin_user.set(users)

            # 共同管理者を追加する
            for user in users:
                print("--------- user 共同管理者", user)
                co_admin_relation = CoAdminUserManagementRelation.objects.create(
                    admin_user_id = login_admin_user.id,
                    co_admin_user_id = user.id
                )
                co_admin_relation.save()
        else:
            print("----------- co_adminがいるよ")

            # 共同管理者を追加する
            for user in users:
                # co_admin.co_admin_user.add(user)
                print("--------- user 共同管理者", user)

                co_admin_relation = CoAdminUserManagementRelation.objects.create(
                    admin_user_id = login_admin_user.id,
                    co_admin_user_id = user.id
                )
                co_admin_relation.save()

                # 保存
                # co_admin.save()

        message = f'ユーザーに共同管理者権限を付与しました'
        messages.success(self.request, message)

        return HttpResponseRedirect(reverse('training:co_admin_management'))


"""
管理者権限の削除(個別)
"""
class CoAdminUserDeleteView(View):

    def post(self, request, *args, **kwargs):

        user_id = self.kwargs['pk']
        print("----------- user_id", user_id)# 6a9faafb-3fd8-4a2e-a096-9d1327b4397c

        user_obj = User.objects.filter(pk=user_id).first()
        print("----------- user_obj", user_obj)# 比嘉 太郎 / 69523@test.jp
        print("----------- self.request.user.id", self.request.user.id)# 28caa177-ce84-411f-9775-bffc81d22075

        # ログインしている管理者の共同管理者のレコードを取得
        co_admin = CoAdminUserManagement.objects.filter(admin_user=self.request.user.id).first()
        print("----------- co_admin", co_admin)# CoAdminUserManagement object (5)
        print("----------- co_admin.admin_user", co_admin.admin_user)# 28caa177-ce84-411f-9775-bffc81d22075

        del_co_admin_user = CoAdminUserManagementRelation.objects.filter(admin_user_id=co_admin.admin_user, co_admin_user_id=user_id).first()
        print("----------- del_co_admin_user", del_co_admin_user)

        del_co_admin_user.delete()

        # co_admin.co_admin_user.remove(user_obj)
        # print("----------- co_admin.co_admin_user.all()",  co_admin.co_admin_user.all())
        # co_admin.save()

        # メッセージを返す
        messages.success(self.request, "共同管理者権限を取り消しました")

        return HttpResponseRedirect(reverse('training:co_admin_management'))


"""
ゲストユーザー設定ページ
"""
class GuestUserManagementView(LoginRequiredMixin, TemplateView, CommonView):
    # model = GuestUserManagement
    template_name = 'training/guest_user_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ログインユーザーを取得
        current_user = User.objects.filter(pk=self.request.user.id).first()
        context["current_user"] = current_user

        # guest_users = GuestUserManagement.objects.filter(resister_user=self.request.user).exclude(is_rogical_deleted=True)
        guest_users = GuestUserManagement.objects.filter(resister_user=self.request.user.id).exclude(is_rogical_deleted=True)

        context["guest_users"] = guest_users

        return context


"""
ゲストユーザー登録
"""
class GuestUserCreateView(LoginRequiredMixin, CommonView, CreateView):

    # フォームを変数にセット
    model = GuestUserManagement
    # model = User
    template_name = "training/guest_user_create.html"
    form_class = RegisterGuestUserForm
    # form_class = SignUpForm

    def form_valid(self, form):

        print("------------- ゲストユーザー登録")

        # フォームからDBオブジェクトを仮生成
        guest_user = form.save(commit=False)
        print("------------- guest_user", guest_user)

        # 登録ユーザーを保存
        # guest_user.resister_user = self.request.user
        guest_user.resister_user = self.request.user.id

        # 登録ユーザーの会社を保存
        guest_user.resister_user_company = self.request.user.company.id

        # 登録日に今日の日付を代入
        guest_user.resister_date = datetime.now()

        # パスワードをハッシュ化 set_password
        password = make_password(form.cleaned_data['guest_user_password'])

        guest_user.guest_user_password = password

        guest_user.save()

        # メッセージを返す
        messages.success(self.request, "ゲストユーザーを登録しました。")

        return redirect('training:guest_user_management')


"""
ゲストユーザー変更
"""
class GuestUserUpdateView(LoginRequiredMixin, CommonView, UpdateView):
    model = GuestUserManagement
    template_name = 'training/guest_user_update.html'
    form_class = UpdateGuestUserForm

    # def get_form_kwargs(self):
    #     # formにログインユーザーを渡す
    #     kwargs = super(GuestUserUpdateView, self).get_form_kwargs()
    #     kwargs['user'] = self.request.user
    #     kwargs['pk'] = self.kwargs['pk']
    #     return kwargs

    def form_valid(self, form):

        # フォームからDBオブジェクトを仮生成
        guest_user_update = form.save(commit=False)

        # 保存
        guest_user_update.save()

        # メッセージを返す
        messages.success(self.request, "ゲストユーザーを編集しました。")

        return redirect('training:guest_user_management')


"""
ゲストユーザーのパスワード変更
"""
# class PasswordUpdate(PasswordChangeView):
class PasswordUpdate(LoginRequiredMixin, CommonView, UpdateView):
    model = GuestUserManagement
    template_name = 'training/guest_user_password_update.html'
    form_class = PasswordUpdateForm

    def get_form_kwargs(self):
        # formにログインユーザーを渡す
        kwargs = super(PasswordUpdate, self).get_form_kwargs()
        kwargs['guest_user_id'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):

        # フォームからDBオブジェクトを仮生成
        password_update = form.save(commit=False)

        # パスワードをハッシュ化 set_password
        password = make_password(form.cleaned_data['new_password1'])

        password_update.guest_user_password = password

        # 保存
        password_update.save()

        # メッセージを返す
        messages.success(self.request, "パスワードを変更しました。")

        return redirect('training:guest_user_management')


"""
ゲストユーザーの削除(個別)
"""
class GuestUserDeleteView(View):

    def post(self, request, *args, **kwargs):

        guest_user_id = self.kwargs['pk']
        print("----------- guest_user_id", guest_user_id)

        guest_user = GuestUserManagement.objects.filter(pk=guest_user_id).first()
        print("----------- guest_user", guest_user)

        # 論理削除
        guest_user.is_rogical_deleted = True

        # ログインできなくする
        guest_user.is_active = False
        guest_user.save()

        # guest_user_qs.delete()

        # メッセージを返す
        messages.success(self.request, "ゲストユーザーを削除しました")

        return HttpResponseRedirect(reverse('training:guest_user_management'))


"""
ゲストユーザーの削除(一括)
"""
class AllGuestUserDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            # 削除にチェックをしたグループIDを取得
            checks = request.POST.getlist('checks[]')

            # IDと一致するゲストユーザーを取得
            del_guest_users = GuestUserManagement.objects.filter(pk__in=checks)
            print("---------- del_guest_users ---------", del_guest_users)

            for del_guest_user in del_guest_users:

                # 論理削除
                del_guest_user.is_rogical_deleted = True

                # ログインできなくする
                del_guest_user.is_active = False
                del_guest_user.save()

            # ゲストユーザーを削除
            # GuestUserManagement.objects.filter(pk__in=checks).delete()

            message = f'ゲストユーザーを削除しました。'
            messages.success(self.request, message)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "ゲストユーザーを削除しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'ゲストユーザーの削除に失敗しました'
            return JsonResponse(data)


"""
ゲストユーザーに紐づいているトレーニングの一覧
"""
class TrainingLinkView(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'training/training_link.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        print("----------- TrainingLinkView")

        guest_user_id = self.kwargs['pk']
        print("----------- guest_user_id", guest_user_id)

        context["guest_user_id"] = guest_user_id

        guest_user = GuestUserManagement.objects.filter(pk=guest_user_id).first()
        print("----------- guest_user", guest_user)

        # トレーニング取得 ※ここでエラー
        guest_user_trainings = Training.objects.filter(destination_guest_user=guest_user).order_by('status','end_date')
        print("----------- guest_user_trainings", guest_user_trainings)

        context["guest_user_trainings"] = guest_user_trainings

        return context


"""
ゲストユーザーに紐づいているトレーニングの取り消し(個別)
"""
class TrainingLinkDeleteView(View):

    def post(self, request, *args, **kwargs):

        # POSTで送られてきた値を取得
        guest_user_id = request.POST.get('submit')
        print("------------ submit", request.POST.get('submit'))

        # pkと一致するゲストユーザーを取得
        guest_user = GuestUserManagement.objects.filter(pk=guest_user_id).first()
        print("------------ guest_user", guest_user)# <QuerySet [<GuestUserManagement: 田中幹敏>]>

        training_id = self.kwargs['pk']
        print("----------- training_id", training_id)# トレーニングのID

        # トレーニングを取得
        training = Training.objects.filter(pk=training_id).first()
        print("----------- training", training)

        # ゲストユーザーとトレーニングの紐づけを解除
        training.destination_guest_user.remove(guest_user)

        # ゲストユーザーのTrainingMnageを削除
        training_manage = TrainingManage.objects.filter(training=training_id, guest_user_manage=guest_user)
        print("------------ training_manage", training_manage)

        training_manage.delete()

        # 受講履歴を残す
        training_history = TrainingHistory.objects.filter(training=training_id, guest_user_history=guest_user).first()
        print("------------ training_history", training_history)

        training_history.title = training.title
        training_history.description = training.description
        training_history.reg_user = training.reg_user
        training_history.start_date = training.start_date
        training_history.end_date = training.end_date
        # 削除フラグをtrueにする
        # training_history.del_flg = True

        # 保存
        training_history.save()

        # メッセージを返す
        messages.success(self.request, "トレーニングの紐づけを取り消しました。")

        # return HttpResponseRedirect(reverse('training:guest_user_management'))
        return HttpResponseRedirect(reverse('training:training_link', kwargs={'pk': guest_user_id}))

"""
ゲストユーザーに紐づいているトレーニングの取り消し(一括)
"""
class TrainingAllDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            # POSTで送られてきた値を取得
            guest_user_id = request.POST.get('guest_user_id')
            print("--------------- guest_user_id", guest_user_id)

            # pkと一致するゲストユーザーを取得
            guest_user = GuestUserManagement.objects.filter(pk=guest_user_id).first()
            print("------------ guest_user aaa", guest_user)# <QuerySet [<GuestUserManagement: 田中幹敏>]>

            # 削除にチェックをしたトレーニングのIDを取得
            checks = request.POST.getlist('checks[]')

            # IDと一致するトレーニングを取得
            trainings = Training.objects.filter(pk__in=checks)
            print("----------- trainings aaa", trainings)

            for training in trainings:

                print("----------- training aaa", training)

                # ゲストユーザーとトレーニングの紐づけを解除
                training.destination_guest_user.remove(guest_user)
                training.save()

                # ゲストユーザーのTrainingMnageを削除
                training_manage = TrainingManage.objects.filter(training=training, guest_user_manage=guest_user)
                print("------------ training_manage aaa", training_manage)

                training_manage.delete()

            # 受講履歴を残す
            training_historys = TrainingHistory.objects.filter(training__in=checks, guest_user_history=guest_user)
            print("------------ training_historys", training_historys)

            for training_history in training_historys:
                print("------------ training_history", training_history)

                training_history.title = training.title
                training_history.description = training.description
                training_history.reg_user = training.reg_user
                training_history.start_date = training.start_date
                training_history.end_date = training.end_date
                # 削除フラグをtrueにする
                training_history.del_flg = True

                # 保存
                training_history.save()

            message = f'トレーニングの紐づけを取り消しました。'
            messages.success(self.request, message)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "トレーニングの紐づけを取り消しました。",
                                })

        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'トレーニングの紐づけの取り消しに失敗しました'
            return JsonResponse(data)





"""
受講履歴
"""
class TrainingHistoryView(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'training/training_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ログインユーザーを取得
        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user

        # トレーニング取得
        trainings = TrainingHistory.objects.filter(user=self.request.user.id).order_by('status','end_date')
        context["trainings"] = trainings

        return context


"""
アプリ管理者画面
"""
class AppAdminView(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'training/app_admin.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()

        # groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

        # グループをリスト化
        # group_lists = []

        # group_lists_raw = list(groups.values_list('pk', flat=True))

        # for group_uuid in group_lists_raw:
        #     group_uuid_string = str(group_uuid)
        #     group_lists.append(group_uuid_string)

        # ログインしているユーザーが作成したトレーニングを取得する
        trainings = Training.objects.filter(reg_user=current_user.id)
        # trainings = Training.objects.filter(reg_company=current_user_company)
        context["trainings"] = trainings

        # trainings = Training.objects.filter(destination_group__in=group_lists, training_manage__user=current_user).order_by('status','end_date') \
        # .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        # context["trainings"] = trainings

        training_manages = TrainingManage.objects.filter(user=current_user).order_by('status','training__end_date')
        context["training_manages"] = training_manages

        questionnaires_results = QuestionnaireResult.objects.all()
        context["questionnaires_results"] = questionnaires_results

        return context


"""
円グラフに値を返す
"""
class GetPieDataAjaxView(APIView):

    def get(self, request, *args, **kwargs):

        training_id = request.GET.get('training_id')

        training = Training.objects.filter(pk=training_id).first()

        # トレーニングに紐づいているグループを取得
        # groups = training.destination_group.all()
        groups = TrainingRelation.objects.filter(training_id=training.id)
        print("------------ groups", groups)

        # グループをリスト化
        group_list = []
        group_lists_raw = list(groups.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_list.append(group_uuid_string)
        print("---------- group_list ---------", group_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

        group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
        print("---------- group_users ---------", group_users)

        # グループに所属するユーザーをリスト化
        group_user_list = []
        group_user_lists_raw = list(group_users.values_list('group_user', flat=True))
        # IDをstrに直してリストに追加
        for group_user_uuid in group_user_lists_raw:
            group_user_uuid_string = str(group_user_uuid)
            group_user_list.append(group_user_uuid_string)
        print("---------- group_user_list ---------", group_user_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']


        # for group in groups:
        #     # グループに所属しているユーザーを取り出す
        #     for group_user in group.group_user.all():
        #         # リストにユーザーのIDを追加
        #         group_lists.append(group_user.pk)


        # set()で重複しているユーザーをリストから除外する
        # group_list = list(set(group_lists))
        group_user_list = list(set(group_user_list))
        print("--------------- group_user_list --------------", group_user_list)

        # リスト内のIDをUUIDの文字列表現に変更
        # user_id_list = [str(o) for o in group_list]
        user_id_list = [str(o) for o in group_user_list]

        # リスト内のメンバーを数える
        # training_user_count = len(set(group_lists))
        training_user_count = len(set(user_id_list))

        # トレーニングの各ステータス数を取得 ※使ってない、テンプレートタグで各ステータス数を取得している
        training_manages_mitaiou = training.training_manage.filter(status="1", user__in=user_id_list).count()
        training_manages_taiou = training.training_manage.filter(status="2", user__in=user_id_list).count()
        training_manages_done = training.training_manage.filter(status="3", user__in=user_id_list).count()

        # data = [未対応(waiting), 対応中(working), 完了(done)]　※使ってない
        data = [training_manages_mitaiou, training_manages_taiou, training_manages_done]

        return JsonResponse({'data': data,
                            'training_user_count':training_user_count,
                            })


"""
CSVモーダル(Training)
"""
class GetCsvTrainingAjaxView(View):

    def get(self, request, *args, **kwargs):

        # ajaxでtraining_objを取得
        training_id = request.GET.get('training_id')

        trainings = Training.objects.filter(pk=training_id) \
        .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

        training_obj = serializers.serialize("json", trainings)

        return JsonResponse({"groupname": "XXXX",
                            "groups": "",
                            'training_obj':training_obj,
                            })


"""
ユーザー状況エクスポート
"""
class UserStatusView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_status.csv"'
        # HttpResponseオブジェクトはファイルっぽいオブジェクトなので、csv.writerにそのまま渡せます。
        # 文字化けを直す
        sio = io.StringIO()
        writer = csv.writer(sio)
        response.write(sio.getvalue().encode('utf_8_sig'))
        writer = csv.writer(response)

        training_id = self.kwargs['pk']

        training = Training.objects.filter(pk=training_id).first()

        users = []

        # groups = training.destination_group.all()
        groups = TrainingRelation.objects.filter(training_id=training.id)

        # グループをリスト化
        group_list = []
        group_lists_raw = list(groups.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_list.append(group_uuid_string)
        # print("---------- group_list ---------", group_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

        group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
        # print("---------- group_users ---------", group_users)

        group_user_lists_raw = list(group_users.values_list('group_user', flat=True))
        # IDをstrに直してリストに追加
        for group_user_uuid in group_user_lists_raw:
            group_user_uuid_string = str(group_user_uuid)
            users.append(group_user_uuid_string)
        # print("---------- users ---------", users)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']




        # for group in groups:
        #     for group_user in group.group_user.all():
        #         users.append(group_user)



        for index, user in enumerate(set(users)):

            # print("--------- user", user)

            user_obj = User.objects.filter(id=user).first()
            # print("--------- user_obj", user_obj)

            # トレーニングに紐づくパーツ数を出力
            parts_count = training.parts.all().count()
            partss = training.parts.all()

            # パーツステータスを出力
            parts_manage_tmp = PartsManage.objects.none()
            for parts in partss:
                parts_manage = PartsManage.objects.filter(parts=parts, user=user)
                # parts_manage = user.parts_manage_user.filter(parts=parts)
                # print("--------- parts_manage", parts_manage)
                parts_manage_tmp |= parts_manage

            # user_status = parts_manage_tmp.all().order_by("order").values_list('status', flat=True)
            user_status = parts_manage_tmp.all().order_by("parts__order").values_list('status', flat=True)
            # print("--------- user_status", user_status)

            # トレーニングステータスを出力
            user_training_manage = TrainingManage.objects.filter(training=training, user=user).first()
            # user_training_manage = user.training_manage_user.filter(training=training).first()
            # print("--------- user_training_manage", user_training_manage)

            if user_training_manage:
                training_status = user_training_manage.status
            else:
                training_status = 1

            # 上限10に足りない数を算出
            lack_count = 10 - parts_count

            # 不足分のリストを生成
            lack_list = []
            for i in range(lack_count):
                lack_list.append("")

            # パーツマネージの不足数を算出
            # parts_lack_count = parts_count -len(user_status)

            # parts_lack_list = []
            # for i in range(parts_lack_count):
            #     parts_lack_list.append(1)

            user_status_list = list(user_status)

            # リストを結合
            # user_status_list2 = user_status_list + parts_lack_list + lack_list
            user_status_list2 = user_status_list + lack_list
            print("--------- user_status_list2", user_status_list2)


            if index == 0:
                writer.writerow([
                                # "社員番号",
                                "氏名",
                                "メールアドレス",
                                "組織",
                                "所属",
                                "Status",
                                "Parts1",
                                "Parts2",
                                "Parts3",
                                "Parts4",
                                "Parts5",
                                "Parts6",
                                "Parts7",
                                "Parts8",
                                "Parts9",
                                "Parts10",

                ])

            writer.writerow([
                            # user.user_num,
                            # user.display_name,
                            # user.email,
                            # user.company.pic_company_name,
                            # user.company.pic_dept_name,
                            user_obj.display_name,
                            user_obj.email,
                            user_obj.company.pic_company_name,
                            user_obj.company.pic_dept_name,
                            training_status,
                            user_status_list2[0],
                            user_status_list2[1],
                            user_status_list2[2],
                            user_status_list2[3],
                            user_status_list2[4],
                            user_status_list2[5],
                            user_status_list2[6],
                            user_status_list2[7],
                            user_status_list2[8],
                            user_status_list2[9],
                            ])

        return response



"""
アンケートエクスポート
"""
class UserQuestionnaireView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        parts_id = self.kwargs['pk']
        parts = Parts.objects.filter(pk=parts_id).first()

        training = parts.parts.all().first()

        # groups = training.destination_group.all()
        groups = TrainingRelation.objects.filter(training_id=training.id)
        print("------------ アンケートエクスポート groups", groups)# <QuerySet [<TrainingRelation: TrainingRelation object (172)>]>

        for group in groups:
            print("------------ アンケートエクスポート group", group)# TrainingRelation object (172)

            group_users = UserCustomGroupRelation.objects.filter(group_id=group.group_id)
            print("---------------- group_users", group_users)# QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (320)>, <UserCustomGroupRelation: UserCustomGroupRelation object (322)>, <UserCustomGroupRelation: UserCustomGroupRelation object (441)>]>

            # users = group.group_user.all()
            users = group_users
            users_all = users | users

        response = HttpResponse(content_type='text/csv')

        if parts.title == "レポート":
            response['Content-Disposition'] = 'attachment; filename="report.csv"'
        else:
            response['Content-Disposition'] = 'attachment; filename="questionnaire.csv"'

        # HttpResponseオブジェクトはファイルっぽいオブジェクトなので、csv.writerにそのまま渡せます。
        # 文字化けを直す
        sio = io.StringIO()
        writer = csv.writer(sio)
        response.write(sio.getvalue().encode('utf_8_sig'))
        writer = csv.writer(response)

        for index, user in enumerate(users_all):
            print("---------------- user", user)# UserCustomGroupRelation object (320)
            print("---------------- user.group_user", user.group_user)

            user_obj = User.objects.filter(id=user.group_user).first()
            print("--------- user_obj", user_obj)# 比嘉 太郎 / 69523@test.jp

            # 空のQuerysetを生成
            # user_questionnaire_tmp = PartsManage.objects.none()
            # ユーザーにひも付き、かつ選択中のパーツの管理オブジェクトを取得
            # parts_manage = user.parts_manage_user.filter(parts=parts, type=4)
            parts_manage = PartsManage.objects.filter(parts=parts, type=4, user=user.group_user)
            print("--------- parts_manage", parts_manage)

            user_questionnaire = parts_manage.first()

            if index == 0:
                writer.writerow([
                                # "社員番号",
                                "氏名",
                                "メールアドレス",
                                "組織",
                                "所属",
                                "Q1",
                                "Q2",
                                "Q3",
                                "Q4",
                                "Q5",
                                "Q6",
                                "Q7",
                                "Q8",
                                "Q9",
                                "Q10",
                                "Q11",
                                "Q12",
                                "Q13",
                                "Q14",
                                "Q15",

                ])


            if user_questionnaire:

                # 上限10に足りない数を算出
                lack_count = 15 - user_questionnaire.questionnaire_result.all().count()

                # 不足分のリストを生成
                lack_list = []
                for i in range(lack_count):
                    lack_list.append("")

                # questionnaire_result_qs = user_questionnaire.questionnaire_result.all()
                questionnaire_result_qs = user_questionnaire.questionnaire_result.all().order_by('questionnairequestion_relation__order')
                print("---------------- questionnaire_result_qs", questionnaire_result_qs)

                questionnaire_answer_list = []

                # for result in questionnaire_result_qs:

                #     # 記述式の場合
                #     if result.is_type == "textarea":
                #         choice = QuestionnaireChoice.objects.filter(pk=result.answer[0]).first()
                #         questionnaire_answer_list.append(choice.order)

                #     # ラジオボタン、チェックボックスの場合
                #     else:
                #         # [:]でインデックスの最初から最後までの要素を取得、[]を除去
                #         questionnaire_answer_list.append(','.join(result.answer[:]))


                for result in questionnaire_result_qs:

                    # print("result", result)
                    # print("result.is_type", result.is_type)

                    # ラジオボタン
                    if result.is_type == "1":
                        choice = QuestionnaireChoice.objects.filter(pk=result.answer[0]).first()
                        questionnaire_answer_list.append(choice.order)

                    # チェックボックスの場合
                    elif result.is_type == "2":
                        choices = QuestionnaireChoice.objects.filter(pk__in=result.answer)
                        print("choice", choices)
                        choice_result = ""
                        for choice in choices:
                            choice_result += str(choice.order) + ','
                        questionnaire_answer_list.append(choice_result[:-1])

                    # 記述式の場合
                    else:
                        # [:]でインデックスの最初から最後までの要素を取得、[]を除去
                        questionnaire_answer_list.append(','.join(result.answer[:]))


                # リストを結合
                questionnaire_answer_list2 = questionnaire_answer_list + lack_list
                print("---------------- questionnaire_answer_list2", questionnaire_answer_list2)

                writer.writerow([
                                # user.display_name,
                                # user.email,
                                # user.company.pic_company_name,
                                # user.company.pic_dept_name,
                                user_obj.display_name,
                                user_obj.email,
                                user_obj.company.pic_company_name,
                                user_obj.company.pic_dept_name,
                                questionnaire_answer_list2[0],
                                questionnaire_answer_list2[1],
                                questionnaire_answer_list2[2],
                                questionnaire_answer_list2[3],
                                questionnaire_answer_list2[4],
                                questionnaire_answer_list2[5],
                                questionnaire_answer_list2[6],
                                questionnaire_answer_list2[7],
                                questionnaire_answer_list2[8],
                                questionnaire_answer_list2[9],
                                questionnaire_answer_list2[10],
                                questionnaire_answer_list2[11],
                                questionnaire_answer_list2[12],
                                questionnaire_answer_list2[13],
                                questionnaire_answer_list2[14],
                                ])


        return response


"""
テストエクスポート
"""
class UserQuestioneView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        parts_id = self.kwargs['pk']
        parts = Parts.objects.filter(pk=parts_id).first()

        training = parts.parts.all().first()

        # groups = training.destination_group.all()
        groups = TrainingRelation.objects.filter(training_id=training.id)
        print("------------ テストエクスポート groups", groups)

        for group in groups:
            print("------------ テストエクスポート group", group)# TrainingRelation object (172)

            group_users = UserCustomGroupRelation.objects.filter(group_id=group.group_id)
            print("---------------- group_users", group_users)# QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (320)>, <UserCustomGroupRelation: UserCustomGroupRelation object (322)>, <UserCustomGroupRelation: UserCustomGroupRelation object (441)>]>

            # users = group.group_user.all()
            users = group_users
            users_all = users | users

        response = HttpResponse(content_type='text/csv')

        response['Content-Disposition'] = 'attachment; filename="question.csv"'

        # HttpResponseオブジェクトはファイルっぽいオブジェクトなので、csv.writerにそのまま渡せます。
        # 文字化けを直す
        sio = io.StringIO()
        writer = csv.writer(sio)
        response.write(sio.getvalue().encode('utf_8_sig'))
        writer = csv.writer(response)


        for index, user in enumerate(users_all):
            print("---------------- user", user)# UserCustomGroupRelation object (320)
            print("---------------- user.group_user", user.group_user)

            user_obj = User.objects.filter(id=user.group_user).first()
            print("--------- user_obj", user_obj)# 比嘉 太郎 / 69523@test.jp

            # ユーザーにひも付き、かつ選択中のパーツの管理オブジェクトを取得
            # parts_manage = user.parts_manage_user.filter(parts=parts, type=3)
            parts_manage = PartsManage.objects.filter(parts=parts, type=3, user=user.group_user)
            print("--------- parts_manage", parts_manage)

            user_question = parts_manage.first()
            print("--------- user_question", user_question)


            if index == 0:
                writer.writerow([
                                # "社員番号",
                                "氏名",
                                "メールアドレス",
                                "組織",
                                "所属",
                                "Q1",
                                "Q2",
                                "Q3",
                                "Q4",
                                "Q5",
                                "Q6",
                                "Q7",
                                "Q8",
                                "Q9",
                                "Q10",
                                "Q11",
                                "Q12",
                                "Q13",
                                "Q14",
                                "Q15",

                ])


            if user_question:

                # 上限10に足りない数を算出
                lack_count = 15 - user_question.question_result.all().count()

                # 不足分のリストを生成
                lack_list = []
                for i in range(lack_count):
                    lack_list.append("")

                # question_result_qs = user_question.question_result.all().order_by('question')
                question_result_qs = user_question.question_result.all().order_by('question_relation__order')
                print("---------------- question_result_qs", question_result_qs)

                question_answer_list = []

                for result in question_result_qs:

                    print("result", result)
                    print("result.is_type", result.is_type)
                    # ラジオボタン
                    if result.is_type == "1":
                        choice = Choice.objects.filter(pk=result.answer[0]).first()
                        question_answer_list.append(choice.order)

                    # チェックボックスの場合
                    elif result.is_type == "2":
                        choices = Choice.objects.filter(pk__in=result.answer)
                        print("choice", choices)
                        choice_result = ""
                        for choice in choices:
                            choice_result += str(choice.order) + ','
                        question_answer_list.append(choice_result[:-1])

                    # 記述式の場合
                    else:
                        # [:]でインデックスの最初から最後までの要素を取得、[]を除去
                        print("result.answer", result.answer)
                        question_answer_list.append(','.join(result.answer[:]))

                # リストを結合
                question_answer_list2 = question_answer_list + lack_list

                writer.writerow([
                                # user.display_name,
                                # user.email,
                                # user.company.pic_company_name,
                                # user.company.pic_dept_name,
                                user_obj.display_name,
                                user_obj.email,
                                user_obj.company.pic_company_name,
                                user_obj.company.pic_dept_name,
                                question_answer_list2[0],
                                question_answer_list2[1],
                                question_answer_list2[2],
                                question_answer_list2[3],
                                question_answer_list2[4],
                                question_answer_list2[5],
                                question_answer_list2[6],
                                question_answer_list2[7],
                                question_answer_list2[8],
                                question_answer_list2[9],
                                question_answer_list2[10],
                                question_answer_list2[11],
                                question_answer_list2[12],
                                question_answer_list2[13],
                                question_answer_list2[14],
                                ])


        return response


"""
未提出者リマインダー
"""
class ReminderView(LoginRequiredMixin, FormView, CommonView):
    model = TrainingManage
    template_name = 'training/reminder.html'
    form_class = ReminderForm

    def get_form_kwargs(self):
        # formにログインユーザーを渡す
        kwargs = super(ReminderView, self).get_form_kwargs()
        kwargs['pk'] = self.kwargs['pk']

        # 目標の日
        training = Training.objects.filter(pk=self.kwargs['pk']).first()
        end_date = training.end_date
        date_1 = end_date.strftime('%Y-%m-%d')# 2023-01-31

        # 年、月、日に分割
        output_date = date_1.split('-')
        end_day = datetime(int(output_date[0]), int(output_date[1]), int(output_date[2]))# 2020, 7, 24

        # 今日の日付を取得
        today = datetime.now()

        # 計算
        delta = end_day - today

        # キリの良い日数にするため"1"を足す
        days = delta.days + 1
        print("日にちの算出", days)# 26

        # kwargs['end_date'] = self.kwargs['end_date']
        # kwargs['days'] = self.kwargs['days']
        kwargs.update({'days': days})

        return kwargs


    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # URLパラメータから送られたきた相性IDを取得
        training_id = self.kwargs['pk']

        training = Training.objects.filter(pk=training_id).order_by('-end_date').first()

        # current_user = User.objects.filter(pk=self.request.user.id).select_related().get()

        # トレーニングが完了しているユーザーを除外したクエリセットを取得
        training_manages = training.training_manage.filter(training=training).exclude(status="3")
        # print("------------ training_manages", training_manages)

        context["training_manages"] = training_manages

        groups = TrainingRelation.objects.filter(training_id=training_id)

        # グループをリスト化
        group_list = []
        group_lists_raw = list(groups.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_list.append(group_uuid_string)
        # print("---------- group_list ---------", group_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

        group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
        # print("---------- group_users ---------", group_users)

        # グループに所属するユーザーをリスト化
        group_user_list = []
        group_user_lists_raw = list(group_users.values_list('group_user', flat=True))
        # IDをstrに直してリストに追加
        for group_user_uuid in group_user_lists_raw:
            group_user_uuid_string = str(group_user_uuid)
            group_user_list.append(group_user_uuid_string)
        # print("---------- group_user_list ---------", group_user_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

        users = User.objects.filter(id__in=group_user_list)
        # print("---------- users ---------", users)

        # context["users"] = training.destination_user.all()
        context["users"] = users

        context["training_id"] = training_id

        # # 目標の日
        # date = training.end_date
        # date_1 = date.strftime('%Y-%m-%d')# 2023-01-31
        # print("333333333333", date_1)

        # # 年、月、日に分割
        # output_date = date_1.split('-')
        # end_day = datetime(int(output_date[0]), int(output_date[1]), int(output_date[2]))# 2020, 7, 24

        # # 今日の日付を取得
        # today = datetime.now()

        # # 計算
        # delta = end_day - today

        # # キリの良い日数にするため"1"を足す
        # days = delta.days + 1
        # print("日にちの算出", days)# 26

        return context



    def form_valid(self, form):

        print("------------------- 未提出者リマインダー")

        # URLパラメータから送られたきた相性IDを取得
        training_id = self.kwargs['pk']

        # POSTで送られてきた値を取得
        message = form.cleaned_data['message']
        # print("------------------- message", message)

        training = Training.objects.filter(pk=training_id).first()
        # print("------------------- trainingtraining", training)

        # groups = training.destination_group.all()
        groups = TrainingRelation.objects.filter(training_id=training.id)
        # print("------------------- groupsgroups", groups)# <QuerySet [<TrainingRelation: TrainingRelation object (172)>]>

        for group in groups:
            # print("---------------- group", group)

            group_users = UserCustomGroupRelation.objects.filter(group_id=group.group_id)
            # print("---------------- group_users", group_users)

            # for user in group.group_user.all():
            for user in group_users:
                # print("------------------- useruser",user)# UserCustomGroupRelation object (320)

                user_obj = User.objects.filter(id=user.group_user).first()
                # print("------------------- user_obj", user_obj)
                # print("------------------- user_obj.email_user", user_obj.email_user)

                # training_manages = user.training_manage_user.filter(Q(training=training), Q(status=1) | Q(status=2))
                training_manages = TrainingManage.objects.filter(Q(training=training), Q(user=user_obj.id), Q(status=1) | Q(status=2))
                # print("------------------- training_manages", training_manages)

                for training_manage in training_manages:
                    # お知らせのDBを生成
                    # notice = Notification.objects.create(target_user = training_manage.user)

                    # リリース日をセット
                    # notice.release_date = datetime.now()

                    # メッセージをセット
                    # notice.title = message

                    # 保存
                    # notice.save()

                    current_site = get_current_site(self.request)

                    domain = current_site.domain

                    context = {
                        # 'user': training_manage.user,
                        'user': user_obj,
                        'message': message,
                        # 'training': training,
                        'subject': 'まなもあ'
                    }

                    # メールの送信
                    subject_template = get_template('training/mail_template/reminder/subject.txt')
                    subject_render = subject_template.render(context)

                    message_template = get_template('training/mail_template/reminder/message.txt')
                    message_render = message_template.render(context)

                    # メッセージを送信するためにデーモンモードで新しいスレッドを作成する
                    # t = threading.Thread(target=training_manage.user.email_user,
                    t = threading.Thread(target=user_obj.email_user,
                                        args=[subject_render, message_render],
                                        kwargs={'fail_silently': True})
                    t.setDaemon(True)
                    t.start()



        # 戻る先で表示するメッセージ
        messages.success(self.request, "リマインドを送信しました")

        return HttpResponseRedirect(reverse('training:app_admin'))


"""
リソース状況
"""
class ResourceManagementView(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'training/resource_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 会社のユーザー数を取得
        company_user_count = User.objects.filter(company=self.request.user.company.id).count()
        context["company_user_count"] = company_user_count

        # ゲストユーザー数を取得(登録者の会社で取得)
        # company_guest_user_count = GuestUserManagement.objects.filter(resister_user__company=self.request.user.company.id).count()
        company_guest_user_count = GuestUserManagement.objects.filter(resister_user_company=self.request.user.company.id).count()

        context["company_guest_user_count"] = company_guest_user_count

        # リソース管理テーブルからユーザーが所属する会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()

        # レコードがなかった場合
        if this_resource_manage is None:
            print("---------- this_resource_manageがなかったよ ---------")
            # Resource_Managementにトレーニングを作成した会社の管理テーブルを作成
            resource_manage, created = ResourceManagement.objects.get_or_create(
                reg_company_name = self.request.user.company.id,
                number_of_training = 0,
                number_of_file = 0, # 1トレーニング=20KB(=20480B)
                total_file_size = 0
            )
            resource_manage.save()

            context["number_of_training"] = resource_manage.number_of_training
            context["total_file_size"] = resource_manage.total_file_size
            context["remaining_capacity"] = 0
            context["usage_rate"] = 0


        else:
            # トレーニング数
            context["number_of_training"] = this_resource_manage.number_of_training
            # context["number_of_training"] = 0

            # BをMBに変換
            total_file_size = this_resource_manage.total_file_size / 1024 / 1024

            # 小数第2位を切り捨て
            total_file_size = round(total_file_size, 2)

            context["total_file_size"] = total_file_size
            # context["total_file_size"] = 0

            # 残容量
            remaining_capacity = 500 - total_file_size

            # # 残容量がマイナスの値なら0にする
            if remaining_capacity < 0:
                remaining_capacity = 0

            context["remaining_capacity"] = remaining_capacity
            # context["remaining_capacity"] = 0

            # 使用率
            usage_rate = total_file_size / 500 * 100

            # 小数第1位を切り捨てる
            usage_rate = round(usage_rate, 1)

            # 使用率が100以上なら100にする
            if usage_rate >= 100:
                usage_rate = 100

            context["usage_rate"] = usage_rate
            # context["usage_rate"] = 0

        return context


"""
動画再生のチェック
"""
class NotificationStatus(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):

        current_user = User.objects.filter(pk=self.request.user.id).select_related().first()

        # notifications = Notification.objects.filter(target_user = current_user)

        try:
            pass
            # # トレーニングのステータスを更新する
            # for notification in notifications:
            #     notification.is_read = True
            #     notification.save()

        except Exception as e:
            return JsonResponse({"status": "ng",
                                "message": str(e),
                                })

        return JsonResponse({"status": "ok",
                            "message": "更新しました",
                            })

class InvalidColumnsExcepion(Exception):
    """CSVの列が足りなかったり多かったりしたらこのエラー"""
    pass

class InvalidSourceExcepion(Exception):
    """CSVの読みとり中にUnicodeDecordErrorが出たらこのエラー"""
    pass

class InvalidMustColumnsExcepion(Exception):
    """必須カラムが漏れていたらエラー"""
    pass

class InvalidNonExistsExcepion(Exception):
    """ユーザーが存在しないエラー"""
    pass

"""
カラム名と数
1.メールアドレス(必須)※ドメイン不要
2.パスワード(必須),
3.会社名(必須)
4.部署名(必須)
5.姓
6.名
7.ふりがな(姓)
8.ふりがな(名)
9.利用サービス(スペースで区切る)
10.説明
11.ミドルネーム
"""
class PostImport(FormView, CommonView):
    template_name = 'training/import.html'
    form_class = CSVUploadForm
    number_of_columns = 12  # 列の数を定義しておく。各行の列がこれかどうかを判断する

    def save_csv(self, form):
            # アップロードされたファイル名を取得
            csv_file_name = str(form.cleaned_data['file'])
            # csv.readerに渡すため、TextIOWrapperでテキストモードなファイルに変換
            csvfile = io.TextIOWrapper(form.cleaned_data['file'])
            reader = csv.reader(csvfile)
            # ヘッダーを読み飛ばす
            header = next(reader)
            i = 1  # 1行目でのUnicodeDecodeError対策。for文の初回のnextでエラーになるとiの値がない為
            try:
                # iは、現在の行番号。エラーの際に補足情報として使う
                for i, row in enumerate(reader, 1):
                    # 列数が違う場合
                    if len(row) != self.number_of_columns:
                        raise InvalidColumnsExcepion(_('{0}行目 項目数エラー。本来の列数:) {1}, {0}行目の列数: {2} ファイル名:{3}').format(i, self.number_of_columns, len(row), csv_file_name))

                    # 必須カラムのチェック
                    for num in range(0, 3):
                        if not row[num]:
                            raise InvalidMustColumnsExcepion('{0}行目 {1}列目の必須項目がありません。ファイル名:{2}'.format(i, num+1, csv_file_name))

                    user = User.objects.create(email=row[0])
                    user.set_password(row[1])

                    company = Company.objects.filter(pic_company_name=row[2],pic_dept_name=row[3]).first()
                    if company:
                        user.company = company
                    else:
                        company,created = Company.objects.get_or_create(
                            pic_company_name = row[2],
                            pic_dept_name = row[3],
                            pic_prefectures = "47",
                            invoice_prefectures = "47",
                        )
                        user.company = company

                    user.last_name = row[4]
                    user.first_name = row[5]
                    user.display_name = row[4] + ' ' + row[5]
                    user.pLast_name = row[6]
                    user.pFirst_name = row[7]
                    user.pDisplay_name = row[6] + ' ' + row[7]
                    # 利用サービスの値をリストに変換
                    services = row[8].split()
                    user.description = row[9]
                    user.middle_name = row[10]
                    # user.user_num = row[11]
                    user.is_activate = 1
                    user.order = i
                    user.save()

            except UnicodeDecodeError:
                raise InvalidSourceExcepion('{0}行目でデコードに失敗しました。ファイル({1})のエンコーディングや、正しいCSVファイルか確認ください。'.format(i, csv_file_name))

            except IntegrityError:
                raise IntegrityError('{0}行目 エラー。{1}が重複しています。 ファイル名:{2}'.format(i, row[0], csv_file_name))

    def form_valid(self, form):
        try:
            # CSVの100行目でエラーがおきたら、前の99行分は保存されないようにする
            with transaction.atomic():
                self.save_csv(form)
        # 今のところは、この2つのエラーは同様に対処します。
        except InvalidSourceExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidColumnsExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except IntegrityError as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        except InvalidMustColumnsExcepion as e:
            data = {
                'messages': str(e)
            }
            return JsonResponse(data, status=500)
        else:
            data = {
                'messages': "SUCCESS"
            }
            return JsonResponse(data)




"""
トレーニング作成
"""
# class TrainingCreateView(LoginRequiredMixin, CommonView, CreateView):
class TrainingCreateView(LoginRequiredMixin, CommonView, FormView):
    # フォームを変数にセット
    model = Training
    template_name = "training/input_training.html"
    form_class = CreateTrainingForm

    # トレーニング作成画面からグループ編集を開いたかどうかをセッションで判断する
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # セッションにurl_nameを保存
        self.request.session['_url_name'] = self.request.resolver_match.url_name
        return context

    # ログインユーザーを返す
    def get_form_kwargs(self):
        kwargs = super(TrainingCreateView, self).get_form_kwargs()
        kwargs["login_user"] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        # print("------------------ form", form)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


    def form_valid(self, form):

        print("------------------ トレーニング作成画面始まり")

        # フォームからDBオブジェクトを仮生成
        # training = form.save(commit=False)# 使えない

        # 登録ユーザーを保存
        # training.reg_user = self.request.user.id

        # ログインしているユーザーの会社情報を保存
        # training.reg_company = self.request.user.company.id

        # CustomGroupモデルのnameフィールドにgroup_nameを保存
        training, created = Training.objects.get_or_create(
            title = form.cleaned_data['title'],
            description = form.cleaned_data['description'],
            reg_user = self.request.user.id,
            reg_company = self.request.user.company.id,
            start_date = form.cleaned_data['start_date'],
            end_date = form.cleaned_data['end_date'],
            expired_training_flg = form.cleaned_data['expired_training_flg'],
            subject = form.cleaned_data['subject']
        )
        training.save()

        create_training = Training.objects.filter(id=training.id).first()
        print("------------------ create_training", create_training)# トレーニング1

        # 選択したstart_dateを取得
        # start_date = form.cleaned_data['start_date']
        now1 = datetime.now()
        # 登録時刻との比較用
        now2 = datetime.now() - timedelta(hours=9)
        now3 = now2.strftime("%Y-%m-%d %H:%M:%S")
        if create_training.start_date:
            sd = create_training.start_date.strftime("%Y-%m-%d %H:%M:%S")
        fifteen = now1 + timedelta(minutes=15)
        # if training.start_date is None:
        if create_training.start_date is None:
            # start_dateが未入力の場合、15分後の時刻を代入する
            # now = datetime.now()
            # training.start_date = now.strftime("%Y-%m-%d %H:%M:%S")
            create_training.start_date = fifteen.strftime("%Y-%m-%d %H:%M:%S")
        elif sd < now3:
            create_training.start_date = fifteen.strftime("%Y-%m-%d %H:%M:%S")
        else:
            pass

        # Noneの場合、デフォルトのコースと紐づける
        if create_training.subject is None:
            default_subjecte = SubjectManagement.objects.filter(subject_name=settings.SUBJECT_NAME).first()
            # training.subject = default_subjecte
            create_training.subject = default_subjecte

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        # レコードがなかった場合
        if this_resource_manage is None:
            print("---------- this_resource_manageがなかったよ ---------")
            # Resource_Managementにトレーニングを作成した会社の管理テーブルを作成
            resource_manage, created = ResourceManagement.objects.get_or_create(
                reg_company_name = self.request.user.company.id,
                number_of_training = 1,
                number_of_file = settings.TRAINING_SIZE, # 1トレーニング=20KB(=20480B)
                total_file_size = settings.TRAINING_SIZE
            )
            resource_manage.save()
        else:
            print("---------- this_resource_manageがあったよ ---------")

            # 会社に紐づくトレーニング数に新規作成したトレーニングの数を足す
            this_resource_manage.number_of_training += 1

            # トレーニングの合計サイズ = 会社に紐づくトレーニング数 × 20KB(=20480B)
            this_resource_manage.number_of_file = this_resource_manage.number_of_training * settings.TRAINING_SIZE

            # 会社のディスク使用量(=トレーニングの合計サイズ+ファイルの合計サイズ)
            this_resource_manage.total_file_size += settings.TRAINING_SIZE

            this_resource_manage.save()

        # if training.start_date is None:
        #     # start_dateが未入力の場合、現在時刻を代入する
        #     now = datetime.now()
        #     training.start_date = now.strftime("%Y-%m-%d %H:%M:%S")

        # 保存 ※ set()の前でsaveしないとIDが作成されないためset()でリレーションが貼れなくなる
        # training.save()
        create_training.save()

        # 選択したグループを取得
        destination_group_qs = form.cleaned_data['destination_group']
        print("---------- 選択したグループを取得 1---------", destination_group_qs)# <QuerySet [<CustomGroup: グループ1>]>

        # トレーニングとグループの中間テーブルにレコードを作成
        for destination_group in destination_group_qs:
            print("---------- destination_group 1---------", destination_group.id)# 6d10fed6-14e8-4fc9-bed1-68efcc2b247a

            training_destination_group_group_relation, created = TrainingRelation.objects.get_or_create(
                group_id = destination_group.id,
                training_id = training.id,
            )
            training_destination_group_group_relation.save()


        # トレーニングにグループを紐づける
        # training.destination_group.set(destination_group_qs)

        # セッションの中にtempo_customgroupがあればテンポフラグの処理をする
        if 'create_tempo_group' in self.request.session:
            print("---------- create_tempo_groupあるよ ---------")

            destination_group_list = []

            # 選択グループのidのリストを作成
            # destination_group_list = list(destination_group_qs.values_list('name', flat=True))
            destination_group_list = list(destination_group_qs.values_list('id', flat=True))
            print("---------- destination_group_list if---------", destination_group_list)# [UUID('f500016e-b775-4d47-bbe0-2118f1b913c6')]

            # リスト内のIDをUUIDの文字列表現に変更
            destination_group_id_list = [str(o) for o in destination_group_list]
            print("---------- 文字変換1 if---------", destination_group_id_list)# ['f500016e-b775-4d47-bbe0-2118f1b913c6']

            # 既存のグループを取得
            group_qs = UserCustomGroupRelation.objects.filter(group_id__in=destination_group_list, tentative_group_flg=False)
            print("---------- 既存のグループ ---------", group_qs)# <QuerySet [<CustomGroup: メガネ☆セブンα>]>

            # 削除
            group_qs.delete()

            # 仮作成フラグが立っているグループを取得
            # tempo_groups_qs = CustomGroup.objects.filter(name__in=destination_group_id_list, tempo_flg=True)
            tentative_group_qs = UserCustomGroupRelation.objects.filter(group_id__in=destination_group_list, tentative_group_flg=True)
            print("---------- 仮作成フラグが立っているグループ ---------", tentative_group_qs)# <QuerySet [<CustomGroup: メガネ☆セブンα>]>

            # for tempo_group in tempo_groups_qs:
            for tentative_group in tentative_group_qs:
                print("---------- tempo_group ---------", tentative_group.group_id)# f500016e-b775-4d47-bbe0-2118f1b913c6

                # グループのユーザーを取得
                group_users = UserCustomGroupRelation.objects.filter(group_id=tentative_group.group_id)

                for user in group_users:
                    print("---------- user---------", user)
                    # 仮作成フラグをFalseに変更
                    user.tentative_group_flg = False
                    user.save()

        # トレーニングに紐づくグループを取得
        destination_group_all = TrainingRelation.objects.filter(training_id=training.id)
        print("---------- destination_group_all ---------", destination_group_all)# TrainingRelation object (43)

        # for group in training.destination_group.all():
        for group in destination_group_all:
            print("---------- トレーニングに紐づくグループ ---------", group)# TrainingRelation object (43)
            print("---------- トレーニングに紐づくグループ id ---------", group.group_id)# 23ae1fcc-8ac6-4ceb-ac41-11f10e135f41

            groups = UserCustomGroupRelation.objects.filter(group_id=group.group_id)
            print("---------- グループ1 ---------", groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (126)>, <UserCustomGroupRelation: UserCustomGroupRelation object (127)>]>

            for group in groups:
                print("---------- グループ2 ---------", group)
                print("---------- グループのユーザー3 ---------", group.group_user)# 6a9faafb-3fd8-4a2e-a096-9d1327b4397c

                # TrainingManageにユーザー分の管理テーブルを作成
                training_manage, created = TrainingManage.objects.get_or_create(
                    training = create_training,
                    user = group.group_user,
                    status = 1, # 未対応
                    subject_manage = create_training.subject
                )
                training_manage.save()

                # TrainingHistoryテーブルにトレーニングの情報を残す
                if training_manage is not None:
                    training_history, created = TrainingHistory.objects.get_or_create(
                        training = create_training,
                        reg_user = create_training.reg_user,
                        user = training_manage.user,
                        status = 1
                    )
                training_history.save()



        # セッションの中にdeletion_user_id_jsonがれば取り出す(=CustomGroupUpdateViewでメンバーを削除)
        if 'deletion_user_id_json' in self.request.session:
            print("--------------- セッションあったよ(削除) --------------")

            # 削除対象のユーザーのIDをセッションから取得
            deletion_user_id_json = self.request.session['deletion_user_id_json'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "")
            print("--------------- 削除対象のユーザーのIDをセッションから取得(削除) --------------", deletion_user_id_json)# 9a058d25-384d-43e1-9a26-c1a680c87ab4

            # リスト化する
            deletion_user_id_list = deletion_user_id_json.split(',')
            print("--------------- リスト化する(削除) --------------", deletion_user_id_list)# ['9a058d25-384d-43e1-9a26-c1a680c87ab4']

            # 作成したトレーニングに紐づくグループを取得(追加)
            training_relation = TrainingRelation.objects.filter(training_id=create_training.id)
            print("--------------- training_relation", training_relation)

            group_list = []
            group_lists_raw = list(training_relation.values_list('group_id', flat=True))
            # IDをstrに直してリストに追加
            for group_uuid in group_lists_raw:
                group_uuid_string = str(group_uuid)
                group_list.append(group_uuid_string)
            print("---------- group_list ---------", group_list)# ['f399cea5-41f3-4120-ad57-6975a13f7b0c', 'e73d908b-0799-4cd5-93b3-3b08a8b233c1']

            # 取得したグループが紐づいているトレーニングを取得(追加)
            training_relations = TrainingRelation.objects.filter(group_id__in=group_list)
            print("---------- training_relations ---------", training_relations)

            training_id_list = []# (追加)
            training_id_lists_raw = list(training_relations.values_list('training_id', flat=True))
            for training_uuid in training_id_lists_raw:
                training_uuid_string = str(training_uuid)
                training_id_list.append(training_uuid_string)
            print("---------- training_id_list ---------", training_id_list)

            # IDと一致するトレーニングをTrainingテーブルから取得する(追加)
            training_qs = Training.objects.filter(id__in=training_id_list).exclude(id=create_training.id)
            print("---------- training_qs ---------", training_qs)# <QuerySet [<Training: トレーニングA>, <Training: トレーニングC>]>

            # ※TrainingRelationから取得したトレーニングをforで回すとトレーニングに紐づいている各グループごとにトレーニングが回ってしまう
            for training in training_qs:
                print("---------- training ---------", training)

                # トレーニングに紐づくグループを取得
                groups = TrainingRelation.objects.filter(training_id=training.id)
                print("---------- groups ---------", groups)# TrainingRelation object (85)

                # グループのIDをstrに直してリストに追加
                group_list = []
                group_lists_raw = list(groups.values_list('group_id', flat=True))
                for group_uuid in group_lists_raw:
                    group_uuid_string = str(group_uuid)
                    group_list.append(group_uuid_string)
                print("---------- group_list ---------", group_list)# ['b376583f-6687-4db0-b2b3-f59d51885e1d']

                # グループに所属しているユーザーを取り出す
                user_custom_groups = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
                print("---------- user_custom_groups ---------", user_custom_groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (152)>, <UserCustomGroupRelation: UserCustomGroupRelation object (192)>, <UserCustomGroupRelation: UserCustomGroupRelation object (200)>]>

                # IDをstrに直してリストに追加
                group_user_list = []
                group_user_lists_raw = list(user_custom_groups.values_list('group_user', flat=True))
                for ggroup_user_uuid in group_user_lists_raw:
                    group_user_uuid_string = str(ggroup_user_uuid)
                    group_user_list.append(group_user_uuid_string)
                print("---------- group_user_list ---------", group_user_list)# ['76d54969-96ad-4485-ac02-e38612d5c070', '6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '9a058d25-384d-43e1-9a26-c1a680c87ab4']

                # set()で重複しているユーザーをリストから除外する
                user_id_list = list(set(group_user_list))


                # 重複しているユーザーが存在する場合
                if set(deletion_user_id_list) & set(user_id_list):
                    # 重複しているユーザーのTrainingManageは消さない
                    print("--------------- 重複しているユーザーが存在する")

                    repetitive_user = set(deletion_user_id_list) & set(user_id_list)
                    repetitive_user_list = list(repetitive_user)
                    print("---------- repetitive_user_list", repetitive_user_list)

                    # 重複するユーザーを除いた削除対象のユーザーと一致するユーザーのTrainingManageを取得
                    user_training_manages_qs = TrainingManage.objects.filter(user__in=deletion_user_id_list, training=training.id).exclude(user__in=repetitive_user_list)
                    print("--------------- 重複するユーザーを除いた削除対象のユーザーと一致するユーザーのTrainingManageを取得(削除) if --------------", user_training_manages_qs)

                else:
                    print("--------------- 重複しているユーザーが存在しない")

                    # 削除対象のユーザーと一致するTrainingManageを取得
                    user_training_manages_qs = TrainingManage.objects.filter(user__in=deletion_user_id_list, training=training.id)
                    print("--------------- 削除対象のユーザーと一致するTrainingManageを取得(削除) else --------------", user_training_manages_qs)

                # ユーザーのTrainingManageを削除する
                user_training_manages_qs.delete()

            # セッションデータを削除する
            del self.request.session['deletion_user_id_json']



        # セッションの中にadd_user_id_jsonがれば取り出す(=CustomGroupUpdateViewでメンバーを追加)
        if 'add_user_id_json' in self.request.session:
            print("--------------- セッションあったよ(追加) --------------")

            # ユーザー情報をセッションから取得
            add_user_id_json = self.request.session['add_user_id_json'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "")
            print("--------------- リスト化する(追加) --------------", add_user_id_json)# 76d54969-96ad-4485-ac02-e38612d5c070,9a058d25-384d-43e1-9a26-c1a680c87ab4

            # リスト化する
            add_user_id_list = add_user_id_json.split(',')

            # グループを取得
            destination_group_qs = form.cleaned_data['destination_group']
            print("---------- destination_group_qs ---------", destination_group_qs)# <QuerySet [<CustomGroup: メガネ☆セブンα>]>

            destination_group_list = []
            group_lists_raw = list(destination_group_qs.values_list('pk', flat=True))
            # IDをstrに直してリストに追加
            for group_uuid in group_lists_raw:
                group_uuid_string = str(group_uuid)
                destination_group_list.append(group_uuid_string)

            # グループに紐づいているトレーニングを取得
            # trainings = Training.objects.filter(destination_group=group_obj.id)
            training_relations = TrainingRelation.objects.filter(group_id__in=destination_group_list)
            print("---------- グループに紐づいているトレーニングを取得 ---------", training_relations)# <QuerySet [<TrainingRelation: TrainingRelation object (43)>]>

            for add_user in add_user_id_list:

                user = User.objects.filter(pk=add_user).first()
                print("--------------- user(追加) --------------", user)

                for training_relation in training_relations:
                    print("--------------- training_relation --------------", training_relation)# TrainingRelation object (17)
                    print("--------------- training_relation --------------", training_relation.training_id)# 1ca93e62-e27b-42a1-b68b-7613ff4eaa21

                    training_obj = Training.objects.filter(id=training_relation.training_id).first()
                    print("--------------- training_obj --------------", training_obj)# <QuerySet [<Training: トレーニング1>]>

                    if not TrainingManage.objects.filter(user=user, training=training_obj):
                        # 新しくグループに追加されたユーザー分のTrainingManagesを作成する
                        training_manage, created = TrainingManage.objects.get_or_create(
                            training = training_obj,
                            user = user.id,
                            status = 1, # 未対応
                            subject_manage = training_obj.subject
                        )
                        training_manage.save()

                    # 追加したユーザーの対応履歴が存在しない場合
                    if not TrainingHistory.objects.filter(user=user, training=training_obj):
                        training_history, created = TrainingHistory.objects.get_or_create(
                            training = training_obj,
                            reg_user = training_obj.reg_user,
                            user = training_manage.user,
                            status = 1
                        )
                        training_history.save()

            # セッションデータを削除する
            del self.request.session['add_user_id_json']

        # トレーニング作成の処理が済んだことがわかるようにセッションを持たせる
        self.request.session['training_register_done'] = 'training_register_done'

        # 作成したトレーニングのpkを取得
        # training_id = training.pk
        training_id = create_training.pk
        # print("---------- training_id ---------", training_id)

        training_id_str = str(training_id)

        # セッションに保存
        training_id_str = json.dumps(training_id_str,ensure_ascii=False)
        self.request.session['training_id_str'] = training_id_str

        # セッションデータがあるか判定
        if '_url_name' in self.request.session:
            # セッションデータを削除する
            del self.request.session['_url_name']

        # セッションデータがあるか判定
        # if 'group_edit_check_session' in self.request.session:
        #     print("---------------- group_edit_check_sessionがあるよ")
        #     # セッションデータを削除する
        #     del self.request.session['group_edit_check_session']

        # セッションデータがあるか判定
        if 'create_tempo_group' in self.request.session:
            # セッションデータを削除する
            del self.request.session['create_tempo_group']

        # メッセージを返す
        messages.success(self.request, "トレーニングを作成しました。")

        print("------------------ トレーニング作成画面終わり")

        return redirect('training:training_management')





"""
トレーニング作成画面内の戻るボタンを押したときの処理(トレーニング新規作成)
"""
class ReturnView(View):
    def get(self, request, *args, **kwargs):

        # セッションデータがあるか判定
        if '_url_name' in self.request.session:
            # セッションデータを削除する
            del self.request.session['_url_name']

        # セッションデータがあるか判定
        # if 'group_edit_check_session' in self.request.session:
        #     print("---------------- group_edit_check_sessionがあるよ")
        #     # セッションデータを削除する
        #     del self.request.session['group_edit_check_session']

        # セッションデータがあるか判定
        if 'create_tempo_group' in self.request.session:
            # セッションデータを削除する
            del self.request.session['create_tempo_group']

        # if 'tempo_customgroup_id_json' in self.request.session:
        if 'tentative_group_id_json' in self.request.session:
            print("--------------- ReturnView tentative_group_id_jsonセッションあったよ --------------")

            # ユーザー情報をセッションから取得
            # tempo_customgroup_id_json = self.request.session['tempo_customgroup_id_json']
            tentative_group_id_json = self.request.session['tentative_group_id_json']
            print("--------tentative_group_id_json --------", tentative_group_id_json)

            # tempo_groups = CustomGroup.objects.filter(pk__in=tempo_customgroup_id_json)
            tentative_groups = UserCustomGroupRelation.objects.filter(group_id__in=tentative_group_id_json, tentative_group_flg=True)
            print("--------------tentative_groups", tentative_groups)

            # テンポラリフラグの立っているグループを削除する
            # tempo_groups.delete()
            tentative_groups.delete()

            # セッションデータを削除する
            # del self.request.session['tempo_customgroup_id_json']
            del self.request.session['tentative_group_id_json']

        return HttpResponseRedirect(reverse('training:training_management'))


"""
トレーニング変更画面内の戻るボタンを押したときの処理(トレーニング変更)
"""
class ReturnTrainingUpdateView(View):
    def get(self, request, *args, **kwargs):

        # セッションデータがあるか判定
        if '_url_name' in self.request.session:
            # セッションデータを削除する
            del self.request.session['_url_name']

        # セッションデータがあるか判定
        # if 'group_edit_check_session' in self.request.session:
        #     print("---------------- group_edit_check_sessionがあるよ")
        #     # セッションデータを削除する
        #     del self.request.session['group_edit_check_session']

        # セッションデータがあるか判定
        if '_update_training' in self.request.session:
            # セッションデータを削除する
            del self.request.session['_update_training']

        # セッションデータがあるか判定
        if 'create_tempo_group' in self.request.session:
            # セッションデータを削除する
            del self.request.session['create_tempo_group']

        # if 'tempo_customgroup_id_json' in self.request.session:
        if 'tentative_group_id_json' in self.request.session:
            print("--------------- tentative_group_id_jsonセッションあったよ --------------")

            # ユーザー情報をセッションから取得
            # tempo_customgroup_id_json = self.request.session['tempo_customgroup_id_json']
            tentative_group_id_json = self.request.session['tentative_group_id_json']
            print("--------tentative_group_id_json --------", tentative_group_id_json)

            # tempo_groups = CustomGroup.objects.filter(pk__in=tempo_customgroup_id_json)
            tentative_groups = UserCustomGroupRelation.objects.filter(group_id__in=tentative_group_id_json, tentative_group_flg=True)
            print("--------------tentative_groups", tentative_groups)

            # テンポラリフラグの立っているグループを削除する
            tentative_groups.delete()

            # セッションデータを削除する
            # del self.request.session['tempo_customgroup_id_json']
            del self.request.session['tentative_group_id_json']

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


# """
# 続けてテストの設問を作成しない場合の処理(トレーニング詳細設定)
# """
# class CancelQuestionRegisterView(View):
#     def get(self, request, *args, **kwargs):

#         # セッションデータがあるか判定
#         if 'question_register_done' in self.request.session:
#             # セッションデータを削除する
#             del self.request.session['question_register_done']

#         # if 'test_parts_register_done' in self.request.session:
#         #     # セッションデータを削除する
#         #     del self.request.session['test_parts_register_done']

#         # セッションデータがあるか判定
#         if 'parts_id_str' in self.request.session:
#             # セッションデータを削除する
#             del self.request.session['parts_id_str']

#         return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


"""
続けてテストの設問を作成しない場合の処理(トレーニング詳細設定)
"""
class CancelQuestionRegisterView(View):
    def get(self, request, *args, **kwargs):

        # セッションデータがあるか判定
        if 'question_register_done' in self.request.session:
            # セッションデータを削除する
            del self.request.session['question_register_done']

        # セッションデータがあるか判定
        if 'parts_id_str' in self.request.session:
            # セッションデータを削除する
            del self.request.session['parts_id_str']

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


"""
続けてアンケートの設問を作成しない場合の処理(トレーニング詳細設定)
"""
class CancelQuestionnaireRegisterView(View):
    def get(self, request, *args, **kwargs):

        # セッションデータがあるか判定
        if 'questionnaire_register_done' in self.request.session:
            # セッションデータを削除する
            del self.request.session['questionnaire_register_done']

        # アンケートパーツのID
        if 'questionnaire_parts_id_str' in self.request.session:
            # セッションデータを削除する
            del self.request.session['questionnaire_parts_id_str']

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


"""
続けてボタン有効化制御の設定をしない場合の処理(トレーニング詳細設定)
"""
class CancelButtonActivateCtlRegisterView(View):
    def get(self, request, *args, **kwargs):

        # セッションデータがあるか判定
        if 'parts_delete_done' in self.request.session:
            # セッションデータを削除する
            del self.request.session['parts_delete_done']

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))




"""
カスタムグループユーザー表示画面
"""
class DestinationGroupDetailView(ListView, CommonView):
    model = CustomGroup
    template_name = 'training/destination_group_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # URLパラメータから対象グループのIDを取得
        pk = self.kwargs['pk']

        # 対象グループのオブジェクトquerysetを取得
        context["group"] = CustomGroup.objects.get(pk=pk)

        # group = CustomGroup.objects.get(pk=pk)
        # print("----------- group", group)

        # グループに所属しているユーザーを取得
        group_users = UserCustomGroupRelation.objects.filter(group_id=pk)

        # リスト化
        group_user_list = []
        group_user_raw = list(group_users.values_list('group_user', flat=True))
        # IDをstrに直してリストに追加
        for group_user_uuid in group_user_raw:
            group_user_string = str(group_user_uuid)
            group_user_list.append(group_user_string)
        print("---------- group_user_list ---------", group_user_list)

        # Userモデルから一致するユーザーを取得
        users = User.objects.filter(id__in=group_user_list)
        print("---------- users ---------", users)

        # 対象グループのメンバーをリレーション先から取得
        # context["group_members"] = CustomGroup.objects.get(pk=pk).group_user.filter(is_activate=1).order_by('created_date').all()
        context["group_members"] = users

        return context





"""
パーツ並び替え画面
"""
class PartsCreateTopView(LoginRequiredMixin, CommonView, TemplateView):
    model = Training
    template_name = 'training/parts_sorting.html'

    # テンプレートにモデルのデータを渡す
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        # URLパラメータから送られたきた相性IDを取得
        training_id = self.kwargs['pk']

        trainings = Training.objects.filter(pk=training_id) \
        .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

        context["trainings"] = trainings

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context





"""
パーツの並べ替え
"""
class PartsCreateAjaxView(APIView):

    def post(self, request, *args, **kwargs):

        try:
            # フロントから送られてきた並び順を変更したパーツのリストを受け取る
            serial_1 = request.POST.getlist('serial[]')

            # 1から始まるインデックスと要素を同時に取得
            for index, parts_id in enumerate(serial_1, 1):

                part_obj = Parts.objects.filter(pk=parts_id).first()

                training = part_obj.parts.all().first()

                # インデックスをパーツのorderに代入
                part_obj.order = index

                part_obj.save()

                qs = Parts.objects.order_by('order')

                part_obj = serializers.serialize("json", qs)

            message = f'パーツの並び順を変更しました。'
            messages.success(self.request, message)


            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "；パーツの並び順を変更しました",
                                "part_obj": part_obj,
                                "training_id": training.id,
                                # IDをJSONでフロントに返す
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'パーツの並び順の変更に失敗しました'
            return JsonResponse(data)





"""
トレーニング管理画面
"""
class TrainingManagementView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/training_management.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()
        print("------------------ current_user.pk", current_user.pk)

        is_training_done = TrainingDone.objects.filter(user_id=current_user.pk).first()
        print("------------------------トレーニング管理画面 training_done_chg", is_training_done)

        # ログインユーザーのリソース状況を取得
        resource_management = ResourceManagement.objects.filter(reg_company_name=current_user.company.id).first()

        if resource_management is not None:
            # BをMBに変換
            total_file_size = resource_management.total_file_size / 1024 / 1024
            # 小数第2位を切り捨て
            total_file_size = round(total_file_size, 2)
            # 残容量                                                             
            remaining_capacity = 500 - total_file_size

            # 残容量がマイナスの値なら0にする
            if remaining_capacity < 0:
                remaining_capacity = 0
            context["remaining_capacity"] = remaining_capacity

        # デフォルトの科目を取得
        default_subject = SubjectManagement.objects.filter(subject_name="デフォルト").first()

        # デフォルトの科目がない場合は新しく作成
        if default_subject is None:
            default_subject, created = SubjectManagement.objects.get_or_create(
                subject_name = "デフォルト",
            )
            # 保存
            default_subject.save()

        # 完了済みのトレーニングの非表示 おそらく使っていない
        # if current_user.is_training_done:
        # if is_training_done:

        #     groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

        #     # できなかったときの書き方
        #     for group in groups:

        #         trainings = Training.objects.filter(Q(destination_user__in=[current_user.id]) | Q(destination_group__in=[group.pk])).exclude(status="3") \
        #         .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

        # # 全表示
        # else:
        #     groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

        #     for group in groups:

        #         trainings = Training.objects.filter(Q(destination_user__in=[current_user.id]) | Q(destination_group__in=[group.pk])).exclude(status="3") \
        #         .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

        # TrainingCreateViewで立てたセッションのフラグをフロントに返す
        if 'training_register_done' in self.request.session:
            training_register_done = self.request.session['training_register_done']
            # context["training_register_done"] = training_register_done
            print("--------------- セッションある --------------")


        # トレーニングのIDのセッションデータをフロントに返す
        if 'training_id_str' in self.request.session:
            training_id_str = self.request.session['training_id_str'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "")
            context["training_id_str"] = training_id_str

        # セッションデータがあるか判定
        if 'tempo_customgroup_id_json' in self.request.session:
            # セッションデータを削除する
            del self.request.session['tempo_customgroup_id_json']

        # for key in list(self.request.session.keys()):
        #     if not key.startswith("_"):
        #         del self.request.session[key]

        training = Training.objects.filter(reg_company=current_user.company.id)
        if training:
            context["training"] = training
        
        # グループが存在するかチェック（トレーニング作成ボタン制御用）
        groups = CustomGroup.objects.filter(group_reg_user=current_user.id,tempo_flg=False)
        if groups:
            context["groups"] = groups

        return context





"""
トレーニングの非表示(Ajax)
"""
class TrainingDoneAjaxView(View):
    model = Training
    template_name = 'training/training_change_management.html'

    def get(self, request):

        # POSTで送られてきたテーブルの値を取得
        tab_menu = request.GET.get('tab_menu')

        current_user = User.objects.filter(pk=self.request.user.id).first()
        groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

        # 全て表示
        if tab_menu == "all":

            for group in groups:

                trainings = Training.objects.filter(Q(destination_user__in=[current_user.id]) | Q(destination_group__in=[group.pk])) \
                .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

            training_obj = serializers.serialize("json", trainings)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "全てのトレーニングを表示します",
                                "data": training_obj,
                                })

        # 未対応
        elif tab_menu == "b":

            for group in groups:

                trainings = Training.objects.filter(Q(destination_user__in=[current_user.id]) | Q(destination_group__in=[group.pk])).exclude(status="1") \
                .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

            training_obj = serializers.serialize("json", trainings)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "未対応のトレーニングを表示します",
                                "data": training_obj,
                                })

        # 対応中
        elif tab_menu == "c":

            for group in groups:

                trainings = Training.objects.filter(Q(destination_user__in=[current_user.id]) | Q(destination_group__in=[group.pk])).exclude(status="2") \
                .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

            training_obj = serializers.serialize("json", trainings)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "対応中のトレーニングを表示します",
                                "data": training_obj,
                                })

        # 完了
        else:

            for group in groups:

                trainings = Training.objects.filter(Q(destination_user__in=[current_user.id]) | Q(destination_group__in=[group.pk])).exclude(status="3") \
                .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

            training_obj = serializers.serialize("json", trainings)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "完了したトレーニングを表示します",
                                "data": training_obj,
                                })






"""
テストパーツ作成画面
"""
class TestPartsCreateView(LoginRequiredMixin, CommonView, CreateView):
    # フォームを変数にセット
    model = Parts
    template_name = "training/test_parts_create.html"
    form_class = AdminTestForm

    def get_form_kwargs(self):
        # formにログインユーザーを渡す
        kwargs = super(TestPartsCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


    def form_valid(self, form):

        training_id = self.kwargs['pk']

        training_obj = Training.objects.filter(pk=training_id).first()

        # フォームからDBオブジェクトを仮生成
        test_parts = form.save(commit=False)

        # パーツの数を取得
        parts_count = training_obj.parts.count()

        # orderに＋1する
        test_parts.order = parts_count + 1

        # 登録ユーザーを保存
        # current_user = User.objects.filter(pk=self.request.user.id).first()
        test_parts.parts_user = self.request.user.id
        # test_parts.parts_user = current_user

        # 保存
        test_parts.save()

        # PartsモデルからIDと一致するパーツオブジェクトを取得(純粋なオブジェクトを取得するために)
        test_parts_obj = Parts.objects.filter(pk=test_parts.id).first()

        # トレーニングとパーツを紐づける
        training_obj.parts.add(test_parts_obj)

        training_obj.save()

        # トレーニングに紐づくグループを取得
        training_relations = TrainingRelation.objects.filter(training_id=training_id)
        # print("------------ training_relations", training_relations)

        # グループをリスト化
        group_list = []
        group_lists_raw = list(training_relations.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_list.append(group_uuid_string)
        # print("---------- group_list ---------", group_list)

        group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
        # print("---------- group_users ---------", group_users)

        # グループに所属しているユーザーを取り出す
        for group_user in group_users:
            # print("---------- group_user ---------", group_user)# UserCustomGroupRelation object (2)
            # print("---------- group_user ---------", group_user.group_user)
            # ユーザーのPartsManageを作成する
            parts_manage, created = PartsManage.objects.get_or_create(
                order = test_parts.order,
                type = test_parts.type,
                parts = test_parts,
                user = group_user.group_user,
                is_parts_required = test_parts.is_required
            )
            parts_manage.save()

        # テストパーツのIDを取得
        parts_id = test_parts.pk
        parts_id_str = str(parts_id)

        # テストパーツ作成の処理が済んだことがわかるようにセッションを持たせる
        self.request.session['question_register_done'] = 'question_register_done'

        # partsのidをセッションに保存
        parts_id_str = json.dumps(parts_id_str,ensure_ascii=False)
        self.request.session['parts_id_str'] = parts_id_str

        # メッセージを返す
        messages.success(self.request, "テストパーツを作成しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


"""
テストパーツ作成の説明ウィンドウ
"""
class TestPartsCreateHelpView(LoginRequiredMixin, TemplateView, CommonView):
    template_name = 'training/test_parts_create_help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).select_related().get()
        context["current_user"] = current_user

        return context


"""
アンケートパーツ作成画面
"""
class QuestionnairePartsCreateView(LoginRequiredMixin, CommonView, CreateView):
    # フォームを変数にセット
    model = Parts
    template_name = "training/questionnaire_parts_create.html"
    form_class = AdminQuestionnaireForm

    def get_form_kwargs(self):

        # formにログインユーザーを渡す
        kwargs = super(QuestionnairePartsCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


    def form_valid(self, form):

        training_id = self.kwargs['pk']

        training_obj = Training.objects.filter(pk=training_id).first()

        # フォームからDBオブジェクトを仮生成
        questionnaire_parts = form.save(commit=False)

        # パーツの数を取得
        parts_count = training_obj.parts.count()

        # orderに＋1する
        questionnaire_parts.order = parts_count + 1

        # 登録ユーザーを保存
        # current_user = User.objects.filter(pk=self.request.user.id).first()
        # print("-------------- current_user アンケートパーツ作成 2", type(current_user))# <class 'accounts.models.User'>
        questionnaire_parts.parts_user = self.request.user.id
        # questionnaire_parts.parts_user = current_user

        # 保存
        questionnaire_parts.save()

        # PartsモデルからIDと一致するパーツオブジェクトを取得(純粋なオブジェクトを取得するために)
        questionnaire_parts_obj = Parts.objects.filter(pk=questionnaire_parts.id).first()

        # トレーニングとパーツを紐づける
        training_obj.parts.add(questionnaire_parts_obj)

        training_obj.save()

        # トレーニングに紐づくグループを取得
        training_relations = TrainingRelation.objects.filter(training_id=training_id)
        # print("------------ training_relations", training_relations)

        # グループをリスト化
        group_list = []
        group_lists_raw = list(training_relations.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_list.append(group_uuid_string)
        # print("---------- group_list ---------", group_list)

        group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
        # print("---------- group_users ---------", group_users)

        # グループに所属しているユーザーを取り出す
        for group_user in group_users:
            # print("---------- group_user ---------", group_user)# UserCustomGroupRelation object (2)
            # print("---------- group_user ---------", group_user.group_user)
            # ユーザーのPartsManageを作成する
            parts_manage, created = PartsManage.objects.get_or_create(
                order = questionnaire_parts.order,
                type = questionnaire_parts.type,
                parts = questionnaire_parts,
                user = group_user.group_user,
                is_parts_required = questionnaire_parts.is_required
            )
            parts_manage.save()

        parts_id = questionnaire_parts.id
        questionnaire_parts_id_str = str(parts_id)

        # partsのidをセッションに保存
        questionnaire_parts_id_str = json.dumps(questionnaire_parts_id_str,ensure_ascii=False)
        self.request.session['questionnaire_parts_id_str'] = questionnaire_parts_id_str

        # アンケートパーツの作成の処理が済んだことがわかるようにセッションを持たせる
        self.request.session['questionnaire_register_done'] = 'questionnaire_register_done'

        # メッセージを返す
        messages.success(self.request, "アンケートパーツを作成しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


"""
ファイルをアップロードする処理
"""
class FileUploadView(View):
    def post(self, request, *args, **kwargs):

        up_file_id = []
        i = 1

        # アップロードされたファイルを得る
        for upload_file in self.request.FILES.values():

            file, created = File.objects.get_or_create(
                name = upload_file.name,
                size = upload_file.size,
                file = upload_file,
            )

            file.file_id = get_random_string(10)

            # 保存
            file.save()

            # file.idを配列に入れている
            up_file_id.append(file.id)

            i+=1

        # 保存したファイルをセッションへ保存,ログアウトしない限りそのセッションが残る
        up_file_id_json = json.dumps(up_file_id)
        self.request.session['up_file_id'] = up_file_id_json

        # 何も返したくない場合、HttpResponseで返す
        return HttpResponse("OK")



"""
ファイルパーツ作成画面
"""
class FilePartsCreateView(LoginRequiredMixin, CommonView, CreateView):
    # フォームを変数にセット
    model = Parts
    template_name = "training/file_parts_create.html"
    form_class = AdminFileForm

    def get_form_kwargs(self):
        # formにログインユーザーを渡す
        kwargs = super(FilePartsCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


    def form_valid(self, form):

        training_id = self.kwargs['pk']

        training_obj = Training.objects.filter(pk=training_id).first()

        # フォームからDBオブジェクトを仮生成
        file_parts = form.save(commit=False)

        # パーツの数を取得
        parts_count = training_obj.parts.count()

        # orderに＋1する
        file_parts.order = parts_count + 1

        # 登録ユーザーを保存
        current_user = User.objects.filter(pk=self.request.user.id).first()
        # print("-------------- current_user ファイルパーツ作成", current_user)# テストユーザー / user@user.com
        # print("-------------- current_user ファイルパーツ作成 2", type(current_user))# <class 'accounts.models.User'>
        file_parts.parts_user = current_user.id
        # file_parts.parts_user = current_user

        # file_idにランダムな文字列を代入
        file_parts.file_id = get_random_string(10)

        # 保存
        file_parts.save()

        # PartsモデルからIDと一致するパーツオブジェクトを取得(純粋なオブジェクトを取得するために)
        file_parts_obj = Parts.objects.filter(pk=file_parts.id).first()

        # トレーニングとパーツを紐づける
        training_obj.parts.add(file_parts_obj)

        training_obj.save()

        # トレーニングに紐づくグループを取得
        training_relations = TrainingRelation.objects.filter(training_id=training_id)
        # print("------------ training_relations", training_relations)

        # グループをリスト化
        group_list = []
        group_lists_raw = list(training_relations.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_list.append(group_uuid_string)
        # print("---------- group_list ---------", group_list)

        group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
        # print("---------- group_users ---------", group_users)

        # グループに所属しているユーザーを取り出す
        for group_user in group_users:
            # print("---------- group_user ---------", group_user)# UserCustomGroupRelation object (2)
            # print("---------- group_user ---------", group_user.group_user)
            # ユーザーのPartsManageを作成する
            parts_manage, created = PartsManage.objects.get_or_create(
                order = file_parts.order,
                type = file_parts.type,
                parts = file_parts,
                user = group_user.group_user,
                is_parts_required = file_parts.is_required
            )
            parts_manage.save()

        # セッションの中にup_file_idがれば取り出す
        if 'up_file_id' in self.request.session:

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_file_id_str = self.request.session['up_file_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_file_id_list = up_file_id_str.split(',')

            # リストをint型に変換
            up_file_id_int = [int(s) for s in up_file_id_list]

            # オブジェクトの取得
            files = File.objects.filter(pk__in=up_file_id_int)
            # print("---------- files ファイルパーツ作成 ---------", files)

            # タスクとファイルを紐付ける(ManyToManyField用)
            file_parts.file.set(files)

            # セッションデータを削除する
            del self.request.session['up_file_id']

            file_parts.save()

            # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
            this_resource_manage = ResourceManagement.objects.filter(reg_company_name=current_user.company.id).first()
            # print("---------- this_resource_manage ---------", this_resource_manage)

            for file in files:
                # print("---------- file ---------", file)# 変更前.PNG
                # print("---------- file.size ---------", file.size)# 171330

                # 会社のディスク使用量にファイルのサイズを足す
                this_resource_manage.total_file_size += int(file.size)
                this_resource_manage.save()

            # メッセージを返す
            messages.success(self.request, "ファイルパーツを作成しました。")

            return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


        else:
            # print("---------- 何もありませんでした ---------")

            # メッセージを返す
            messages.success(self.request, "ファイルパーツを作成しました。")

            return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))



"""
動画をアップロードする処理
"""
class MovieUploadView(View):
    def post(self, request, *args, **kwargs):

        up_movie_id = []
        i = 1

        # アップロードされたファイルを得る
        for upload_movie in self.request.FILES.values():

            movie, created = Movie.objects.get_or_create(
                name = upload_movie.name,
                size = upload_movie.size,
                movie = upload_movie,
            )

            # 保存
            movie.save()

            # file.idを配列に入れている
            up_movie_id.append(movie.id)

            i+=1

        # 保存したファイルをセッションへ保存,ログアウトしない限りそのセッションが残る
        up_movie_id_json = json.dumps(up_movie_id)
        self.request.session['up_movie_id'] = up_movie_id_json

        # 何も返したくない場合、HttpResponseで返す
        return HttpResponse("OK")



"""
ポスターをアップロードする処理
"""
class PosterUploadView(View):
    def post(self, request, *args, **kwargs):

        up_poster_id = []
        i = 1


        # アップロードされたファイルを得る
        for upload_poster in self.request.FILES.values():

            poster, created = Poster.objects.get_or_create(
                name = upload_poster.name,
                size = upload_poster.size,
                poster = upload_poster,
            )

            # 保存
            poster.save()

            # file.idを配列に入れている
            up_poster_id.append(poster.id)

            i+=1

        # 保存したファイルをセッションへ保存,ログアウトしない限りそのセッションが残る
        up_poster_id_json = json.dumps(up_poster_id)

        self.request.session['up_poster_id'] = up_poster_id_json

        # 何も返したくない場合、HttpResponseで返す
        return HttpResponse(up_poster_id)





"""
画像をアップロードする処理
(テスト・アンケートの設問作成画面)
"""
class ImageUploadView(View):
    def post(self, request, *args, **kwargs):

        up_image_id = []
        i = 1

        # アップロードされたファイルを得る
        for upload_image in self.request.FILES.values():

            image, created = Image.objects.get_or_create(
                name = upload_image.name,
                size = upload_image.size,
                image = upload_image,
            )

            # 保存
            image.save()

            # image.idを配列に入れている
            up_image_id.append(image.id)

            i+=1

        # 保存したファイルをセッションへ保存,ログアウトしない限りそのセッションが残る
        up_image_id_json = json.dumps(up_image_id)

        self.request.session['up_image_id'] = up_image_id_json

        # 何も返したくない場合、HttpResponseで返す
        return HttpResponse("OK")


"""
動画パーツ作成画面
"""
class MoviePartsCreateView(LoginRequiredMixin, CommonView, CreateView):
    # フォームを変数にセット
    model = Parts
    template_name = "training/movie_parts_create.html"
    form_class = AdminMovieForm

    def get_form_kwargs(self):

        # formにログインユーザーを渡す
        kwargs = super(MoviePartsCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):

        training_id = self.kwargs['pk']

        training_obj = Training.objects.filter(pk=training_id).first()

        # フォームからDBオブジェクトを仮生成
        movie_parts = form.save(commit=False)

        # パーツの数を取得
        parts_count = training_obj.parts.count()

        # orderに＋1する
        movie_parts.order = parts_count + 1

        # 登録ユーザーを保存
        # current_user = User.objects.filter(pk=self.request.user.id).first()
        movie_parts.parts_user = self.request.user.id
        # movie_parts.parts_user = current_user

        # file_idにランダムな文字列を代入
        movie_parts.file_id = get_random_string(10)

        # 保存
        movie_parts.save()

        # PartsモデルからIDと一致するパーツオブジェクトを取得(純粋なオブジェクトを取得するために)
        movie_parts_obj = Parts.objects.filter(pk=movie_parts.id).first()

        # トレーニングとパーツを紐づける
        training_obj.parts.add(movie_parts_obj)

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()

        # トレーニングに紐づくグループを取得
        training_relations = TrainingRelation.objects.filter(training_id=training_id)
        print("------------ training_relations", training_relations)

        # グループをリスト化
        group_list = []
        group_lists_raw = list(training_relations.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_list.append(group_uuid_string)
        # print("---------- group_list ---------", group_list)

        group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
        # print("---------- group_users ---------", group_users)

        # グループに所属しているユーザーを取り出す
        for group_user in group_users:
            # print("---------- group_user ---------", group_user)# UserCustomGroupRelation object (2)
            # print("---------- group_user ---------", group_user.group_user)
            # ユーザーのPartsManageを作成する
            parts_manage, created = PartsManage.objects.get_or_create(
                order = movie_parts.order,
                type = movie_parts.type,
                parts = movie_parts,
                user = group_user.group_user,
                is_parts_required = movie_parts.is_required
            )
            parts_manage.save()

        # セッションの中にup_poster_idがれば取り出す ※ポスターがない場合はデフォルトの画像が適用される
        if 'up_poster_id' in self.request.session:

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_poster_id_str = self.request.session['up_poster_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_poster_id_list = up_poster_id_str.split(',')

            # リストのInt型に変換
            up_poster_id_int = [int(s) for s in up_poster_id_list]

            # オブジェクトの取得
            poster = Poster.objects.filter(pk__in=up_poster_id_int).first()
            print("---------- poster.size ---------", poster.size)

            # タスクとファイルを紐付ける
            movie_parts.poster = poster

            movie_parts.save()

            # 会社のディスク使用量にポスターのサイズを足す
            this_resource_manage.total_file_size += int(poster.size)
            this_resource_manage.save()

            # セッションデータを削除する
            del self.request.session['up_poster_id']

        else:
            print("---------- up_poster_idなかったよ ---------")

            # 会社のディスク使用量にポスターのサイズを足す
            this_resource_manage.total_file_size += settings.DEFAULT_POSTER
            this_resource_manage.save()



        # セッションの中にup_file_idがれば取り出す
        if 'up_movie_id' in self.request.session:

            print("up_movie_idのセッションがあったよ")

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_movie_id_str = self.request.session['up_movie_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_movie_id_list = up_movie_id_str.split(',')

            # リストのInt型に変換
            up_movie_id_int = [int(s) for s in up_movie_id_list]

            # オブジェクトの取得
            movie = Movie.objects.filter(pk__in=up_movie_id_int).first()
            print("---------- movie.size ---------", movie.size)

            # タスクとファイルを紐付ける
            movie_parts.movie = movie

            movie_parts.save()

            # 会社のディスク使用量に動画ファイルのサイズを足す
            this_resource_manage.total_file_size += int(movie.size)
            this_resource_manage.save()

            # セッションデータを削除する
            del self.request.session['up_movie_id']


        # メッセージを返す
        messages.success(self.request, "動画パーツを作成しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))





"""
テストの設問作成画面
"""
class QuestionRegisterView(LoginRequiredMixin, CommonView, CreateView):
    model = Question
    template_name = 'training/question_register.html'
    form_class = QuestionForm

    # formに値を渡す
    def get_form_kwargs(self):

        kwargs = super(QuestionRegisterView, self).get_form_kwargs()

        # pkを渡す
        kwargs['pk'] = self.kwargs['pk']

        return kwargs


    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        parts_id = self.kwargs['pk']

        test_parts = Parts.objects.filter(pk=parts_id)
        context["test_parts"] = test_parts


        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context


    def form_valid(self, form):

        parts_id = self.kwargs['pk']

        parts_id_str = str(parts_id)

        p_id = Parts.objects.filter(pk=parts_id).first()

        training = Training.objects.filter(parts=parts_id).first()

        # フォームからDBオブジェクトを仮生成(設問)
        question = form.save(commit=False)
        print("------ question ------", question)

        # パーツに紐づくテストの数を取得
        parts_count = Question.objects.filter(parts=p_id).count()

        # orderに＋1する
        question.order = parts_count + 1

        # 登録ユーザーを保存
        question.question_register_user = self.request.user.id

        # 設問に紐づく回答を取得
        formset = ChoiceFormSet(self.request.POST, instance=question)

        # パーツと設問を紐づける
        question.parts = p_id

        # 保存
        question.save()
        formset.save()


        # 記述式の場合
        if question.is_multiple == 3 or question.is_multiple == 4:
            print("----- 記述式の場合 ------")

            for choice_form in question.choice_set.all():
                print("-------choice_form -----", choice_form)

                # 正解にチェックをつける
                choice_form.is_correct = True
                # 保存
                choice_form.save()

        # else:
        #     print("---------- question.is_multiple else ---------")

        # 解答数を取得
        is_correct_count = question.choice_set.filter(is_correct=True).count()
        # print("------- is_correct_count -----", is_correct_count)

        # 記述式の場合
        if question.is_multiple == 3 or question.is_multiple == 4:
            # number_of_answersに1を代入
            question.number_of_answers = 1
        # それ以外の場合
        else:
            question.number_of_answers = is_correct_count

        question.save()

        # セッションの中にup_file_idがれば取り出す
        if 'up_image_id' in self.request.session:

            print("画像があったよ")

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_image_id_str = self.request.session['up_image_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_image_id_list = up_image_id_str.split(',')

            # リストのInt型に変換
            up_image_id_int = [int(s) for s in up_image_id_list]

            # オブジェクトの取得
            images = Image.objects.filter(pk__in=up_image_id_int)

            # タスクとファイルを紐付ける(ManyToManyField用)
            question.image.set(images)

            # セッションデータを削除する
            del self.request.session['up_image_id']

            question.save()

            # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
            this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
            print("---------- this_resource_manage ---------", this_resource_manage)

            for image in images:
                print("---------- image ---------", image)# 変更前.PNG
                print("---------- image.size ---------", image.size)# 171330

                # 会社のディスク使用量にファイルのサイズを足す
                this_resource_manage.total_file_size += int(image.size)
                this_resource_manage.save()

        # メッセージを返す
        messages.success(self.request, "テストの設問を作成しました。")

        # テスト作成画面で設問作成の処理が済んだことがわかるようにセッションを持たせる
        self.request.session['question_register_done'] = 'question_register_done'

        # partsのidをセッション委保存
        parts_id_str = json.dumps(parts_id_str,ensure_ascii=False)
        self.request.session['parts_id_str'] = parts_id_str

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': training.id}))


"""
アンケートの設問作成画面
"""
class QuestionnaireRegisterView(LoginRequiredMixin, CommonView, CreateView):
    model = QuestionnaireQuestion
    template_name = 'training/questionnaire_register.html'
    form_class = QuestionnaireQuestionForm

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        parts_id = self.kwargs['pk']

        questionnaire_parts = Parts.objects.filter(pk=parts_id)
        context["questionnaire_parts"] = questionnaire_parts

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context

    def form_valid(self, form):

        parts_id = self.kwargs['pk']

        questionnaire_parts_id_str = str(parts_id)

        p_id = Parts.objects.filter(pk=parts_id).first()

        training = Training.objects.filter(parts=parts_id).first()

        # フォームからDBオブジェクトを仮生成(設問)
        questionnaire = form.save(commit=False)
        print("---------- questionnaire ---------", questionnaire)# 野うさぎ

        # パーツに紐づくアンケートの数を取得
        parts_count = QuestionnaireQuestion.objects.filter(parts=p_id).count()

        # orderに＋1する
        questionnaire.order = parts_count + 1

        # 登録ユーザーを保存
        questionnaire.questionnair_register_user = self.request.user.id

        # 設問に紐づく回答を取得
        formset = QuestionnaireChoiceFormSet(self.request.POST, instance=questionnaire)

        # パーツと設問を紐づける
        questionnaire.parts = p_id

        # 保存
        questionnaire.save()
        formset.save()

        # セッションの中にup_file_idがれば取り出す
        if 'up_image_id' in self.request.session:

            print("画像があったよ")

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_image_id_str = self.request.session['up_image_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_image_id_list = up_image_id_str.split(',')

            # リストのInt型に変換
            up_image_id_int = [int(s) for s in up_image_id_list]

            # オブジェクトの取得
            images = Image.objects.filter(pk__in=up_image_id_int)

            # タスクとファイルを紐付ける(ManyToManyField用)
            questionnaire.image.set(images)

            # セッションデータを削除する
            del self.request.session['up_image_id']

            questionnaire.save()

            # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
            this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
            print("---------- this_resource_manage ---------", this_resource_manage)

            for image in images:
                print("---------- image ---------", image)# 変更前.PNG
                print("---------- image.size ---------", image.size)# 171330

                # 会社のディスク使用量にファイルのサイズを足す
                this_resource_manage.total_file_size += int(image.size)
                this_resource_manage.save()

        # メッセージを返す
        messages.success(self.request, "アンケートの設問を作成しました。")

        # アンケートの作成画面で設問作成の処理が済んだことがわかるようにセッションを持たせる
        self.request.session['questionnaire_register_done'] = 'questionnaire_register_done'

        # partsのidをセッションに保存
        questionnaire_parts_id_str = json.dumps(questionnaire_parts_id_str,ensure_ascii=False)
        self.request.session['questionnaire_parts_id_str'] = questionnaire_parts_id_str

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': training.id}))


"""
アンケート編集画面
"""
class QuestionnairManagementView(LoginRequiredMixin, FormView, CommonView):
    model = Parts
    template_name = 'training/questionnaire_management.html'
    form_class = TestQuestionForm
    #Formは質問と回答の描画をwidgetで表現できなかったため実際にはつかっていない。

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parts_id = self.kwargs['pk']

        context["login_user"] = self.request.user

        questionnaire = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("questionnairequestion_set", queryset=QuestionnaireQuestion.objects.all().order_by('order'))).first()

        context["test"] = questionnaire

        choice_num = ["ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ"]
        context["choice_num"] = choice_num

        training = Training.objects.filter(parts=questionnaire.id).first()
        context["training_id"] = training.id

        if 'answer_dict_json' in self.request.session:
            answer_dict_json = self.request.session['answer_dict_json']
            context["answer_dict_json"] = answer_dict_json

        return context




"""
アンケートの設問変更
"""
class QuestionnaireUpdateView(LoginRequiredMixin, CommonView, UpdateView):
    model = QuestionnaireQuestion
    template_name = 'training/questionnaire_update.html'
    form_class = QuestionnaireQuestionForm


    # 変更処理
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question_pk = self.kwargs['pk']
        context["question_pk"] = question_pk

        # questionを取得
        questionnaire_question = QuestionnaireQuestion.objects.get(pk=question_pk)

        context["question"] = questionnaire_question

        # questionに紐づいているパーツを取得
        test_parts = Parts.objects.filter(pk=questionnaire_question.parts.id)
        context["test_parts"] = test_parts

        # json形式でシリアライズする
        dist_file = serializers.serialize("json", questionnaire_question.image.all(), fields=('image', 'name', 'id', 'image_id', 'size'))

        # フロントに返す
        context["dist_file"] = dist_file

        return context


    def form_valid(self, form):

        question_pk = self.kwargs['pk']

        # questionを取得
        question = QuestionnaireQuestion.objects.get(pk=question_pk)

        # questionに紐づいているパーツを取得
        questionnaire_parts = Parts.objects.get(pk=question.parts.id)

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        # フォームからDBオブジェクトを仮生成(設問)
        questionnaire_update = form.save(commit=False)

        # 設問に紐づく回答を取得
        formset = QuestionnaireChoiceFormSet(self.request.POST, instance=questionnaire_update)

        # パーツと設問を紐づける
        questionnaire_update.parts = questionnaire_parts

        # 保存
        questionnaire_update.save()
        formset.save()


        # セッションの中にup_poster_idがれば取り出す ※ポスターがない場合はデフォルトの画像が適用される
        if 'up_image_id' in self.request.session:

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_image_id_str = self.request.session['up_image_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_image_id_list = up_image_id_str.split(',')

            # リストのInt型に変換
            up_image_id_int = [int(s) for s in up_image_id_list]

            # オブジェクトの取得
            images = Image.objects.filter(pk__in=up_image_id_int)

            # add()で画像を追加する(ManyToManyField用)
            for image in images:
                print("---------- image ---------", image)# 変更前.PNG
                print("---------- image.size ---------", image.size)# 171330
                print("---------- image.size type ---------", type(image.size))# <class 'str'>

                questionnaire_update.image.add(image)

                # 会社のディスク使用量にファイルのサイズを足す
                this_resource_manage.total_file_size += int(image.size)
                this_resource_manage.save()

            # セッションデータを削除する
            del self.request.session['up_image_id']

            questionnaire_update.save()


        # メッセージを返す
        messages.success(self.request, "アンケートの設問を変更しました。")

        return HttpResponseRedirect(reverse('training:questionnaire_management', kwargs={'pk': questionnaire_parts.id}))






"""
テスト画面
"""
class QuestionManagementView(LoginRequiredMixin, FormView, CommonView):
    model = Parts
    template_name = 'training/question_management.html'
    form_class = TestQuestionForm
    #Formは質問と回答の描画をwidgetで表現できなかったため実際にはつかっていない。

    # ログインユーザーを返す
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["login_user"] = self.request.user

        parts_id = self.kwargs['pk']
        context["parts_id"] = parts_id

        test = Parts.objects.filter(pk=parts_id).prefetch_related(Prefetch("question_parts", queryset=Question.objects.all().order_by('order'))).first()

        context["test"] = test

        choice_num = ["ア","イ","ウ","エ","オ","カ","キ","ク","ケ","コ"]
        context["choice_num"] = choice_num

        training = Training.objects.filter(parts=test.id).first()
        print("--------------------", training)

        context["training_id"] = training.id

        if 'answer_dict_json' in self.request.session:
            answer_dict_json = self.request.session['answer_dict_json']
            context["answer_dict_json"] = answer_dict_json

        return context


"""
テストパーツ編集画面
"""
class TestPartsUpdateView(LoginRequiredMixin, UpdateView):
    model = Parts
    template_name = 'training/test_parts_update.html'
    fields = ('title','description', 'title_detail',
                'description_detail', 'pass_line', 'pass_text1', 'pass_text2', 'unpass_text1', 'unpass_text2', 'is_required', 'answer_content_show')

    def form_valid(self, form):
        test_parts_update = form.save(commit=False)
        # logger.debug("")
        # logger.debug(test_parts_update)
        # logger.error(test_parts_update)

        test_parts_update.save()

        return HttpResponseRedirect(reverse('training:question_management', kwargs={'pk': self.kwargs['pk']}))



"""
テストの設問変更
"""
class QuestionUpdateView(LoginRequiredMixin, CommonView, UpdateView):
    model = Question
    template_name = 'training/question_update.html'
    form_class = QuestionForm

    # formに値を渡す
    def get_form_kwargs(self):

        # formにpkを渡す
        kwargs = super(QuestionUpdateView, self).get_form_kwargs()

        kwargs['pk'] = self.kwargs['pk']

        return kwargs

    # def get_initial(self):

    #     initial={
    #         'is_multiple': 1,
    #     }

    #     # フロントに返す(ユーザー一覧に✔がついた状態で描画される)
    #     return initial


    # def post(self, request, *args, **kwargs):
    #     self.object = self.get_object()
    #     print("self.object", self.object)# アメリカの首都は？

    #     form_class = self.get_form_class()
    #     print("form_class", form_class)# <class 'training.forms.QuestionForm'>

    #     form = self.get_form(form_class)
    #     print("form", form)

    #     qs = Choice.objects.filter(question=self.get_object())
    #     print("qs", qs)

    #     formsets = ChoiceFormSet(self.request.POST, queryset=qs)
    #     print("formsets", formsets)

    #     if form.is_valid():
    #         print("form.is_valid():")
    #         for fs in formsets:
    #             if fs.is_valid():
    #                 print("if fs.is_valid():")
    #                 fs.save()
    #         return self.form_valid(form)
    #     return self.form_invalid(form)


    # 変更処理
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        question_pk = self.kwargs['pk']
        context["question_pk"] = question_pk

        # questionを取得
        question = Question.objects.get(pk=question_pk)

        context["question"] = question

        # questionに紐づいているパーツを取得
        test_parts = Parts.objects.filter(pk=question.parts.id)
        context["test_parts"] = test_parts

        # json形式でシリアライズする
        dist_file = serializers.serialize("json", question.image.all(), fields=('image', 'name', 'id', 'image_id', 'size'))

        # フロントに返す
        context["dist_file"] = dist_file

        return context


    def form_valid(self, form):

        question_pk = self.kwargs['pk']

        # questionを取得
        question = Question.objects.get(pk=question_pk)
        # print("uuuuuuuuuuuu", question.is_multiple)

        # questionに紐づいているパーツを取得
        test_parts = Parts.objects.get(pk=question.parts.id)

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        # フォームからDBオブジェクトを仮生成(設問)
        question_update = form.save(commit=False)

        # 設問に紐づく回答を取得
        formset = ChoiceFormSet(self.request.POST, instance=question_update)
        print("---------- formset 設問編集 ---------", formset)

        # パーツと設問を紐づける
        question_update.parts = test_parts

        # 更新したis_multipleの値で上書き ※selectボックスで選択していたものをラジオボタンに変更したため処理を追加
        question.is_multiple = question_update.is_multiple
        question.text = question_update.text

        # 保存
        question_update.save()

        formset.save()

        question.save()

        # 記述式の場合
        if question.is_multiple == 3 or question.is_multiple == 4:

            # 一番目の選択肢を取得(=記述式で入力したもの)
            choice = question.choice_set.all().first()
            # print("---------- choice_ID",choice.id)

            # 正解にチェックをつける
            choice.is_correct = True

            # 保存
            choice.save()

            # 一番目の選択肢を除いた選択肢を取得
            del_choices = question.choice_set.exclude(id=choice.id)
            # print("---------- del_choices",del_choices)

            # 削除
            del_choices.delete()

        # 解答数を取得
        # is_correct_count = question.choice_set.filter(is_correct=True).count()
        is_correct_count = question_update.choice_set.filter(is_correct=True).count()
        is_correct = question_update.choice_set.filter(is_correct=True)
        print("------- is_correct_count -----", is_correct_count)
        print("------- is_correct -----", is_correct)

        # number_of_answersに代入
        # question.number_of_answers += is_correct_count
        question.number_of_answers = is_correct_count

        question.save()


        # セッションの中にup_poster_idがれば取り出す ※ポスターがない場合はデフォルトの画像が適用される
        if 'up_image_id' in self.request.session:

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_image_id_str = self.request.session['up_image_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_image_id_list = up_image_id_str.split(',')

            # リストのInt型に変換
            up_image_id_int = [int(s) for s in up_image_id_list]

            # オブジェクトの取得
            images = Image.objects.filter(pk__in=up_image_id_int)

            # add()で画像を追加する(ManyToManyField用)
            for image in images:
                print("---------- image ---------", image)# 変更前.PNG
                print("---------- image.size ---------", image.size)# 171330
                print("---------- image.size type ---------", type(image.size))# <class 'str'>

                question_update.image.add(image)

                # 会社のディスク使用量にファイルのサイズを足す
                this_resource_manage.total_file_size += int(image.size)
                this_resource_manage.save()

            # セッションデータを削除する
            del self.request.session['up_image_id']

            question_update.save()


        # メッセージを返す
        messages.success(self.request, "設問を変更しました。")

        return HttpResponseRedirect(reverse('training:question_management', kwargs={'pk': test_parts.id}))


"""
テストの設問削除
"""
class QuestionDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'training/question_management.html'
    model = Question
    form_class = QuestionForm

    def delete(self, *args, **kwargs):

        pk = self.kwargs['pk']

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        # 削除される対象のオブジェクトを取得
        part_obj = Question.objects.filter(pk=pk).first()

        # 設問のorderの振りなおし(管理者ページでの表記用)
        # そのパーツに紐づいている設問の総数を取得
        question_count = Question.objects.filter(parts=part_obj.parts).count()

        # 削除される対象の次のorderのオブジェクトのオーダーを取得
        next_question_order = part_obj.order + 1

        # range(start, stop)にstopの値は結果に含まれないため+1する
        question_count += 1

        # 削除される対象以降のオブジェクトのorderをリストで取得
        next_question_list = list(range(next_question_order, question_count))

        # 削除する以降のオブジェクトを取得
        next_part_obj = Question.objects.filter(order__in=next_question_list, parts=part_obj.parts)

        # 削除する対象のオブジェクトの次のオブジェクトに削除する対象のオーダーを入れる
        index = 0

        for next_part in next_part_obj:

            # 削除する対象以降のオーダーに削除する対象のオーダーを代入
            next_part.order = part_obj.order + index

            # for分が回るたびにindexが＋1される
            index += 1

            next_part.save()

        # 設問に紐づいている画像を取得
        images = part_obj.image.all()
        print("------------- images", images)

        if images:
            for image in images:
                print("---------- image ---------", image)# 変更前.PNG
                print("---------- image.size ---------", image.size)# 171330

                # 会社のディスク使用量に画像のサイズを引く
                this_resource_manage.total_file_size -= int(image.size)
                this_resource_manage.save()

                # 逆参照してその画像が紐づいている他のパーツの数を取得
                another_image_count = Question.objects.filter(image=image).count()
                print("---------- another_image_count ---------", another_image_count)

                if another_image_count > 1:
                    print("---------- 他に画像が紐づいてる設問があったよ ---------")
                else:
                    print("---------- 設問に紐づく画像を削除 ---------")
                    # 設問に紐づく画像を削除
                    image.delete()

        part_obj.delete()

        # 削除後に設問編集画面に遷移させるためのパーツidを取得
        part = Parts.objects.filter(pk=part_obj.parts.id).first()

        # メッセージを返す
        messages.success(self.request, "テストの設問を削除しました。")

        return HttpResponseRedirect(reverse('training:question_management', kwargs={'pk': part.pk}))




"""
アンケートの設問削除
"""
class QuestionnaireDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'training/questionnaire_management.html'
    model = QuestionnaireQuestion
    form_class = QuestionnaireQuestionForm

    def delete(self, *args, **kwargs):

        pk = self.kwargs['pk']

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        # 削除される対象のオブジェクトを取得
        part_obj = QuestionnaireQuestion.objects.filter(pk=pk).first()

        # そのパーツに紐づいている設問の総数を取得
        question_count = QuestionnaireQuestion.objects.filter(parts=part_obj.parts).count()

        # 削除される対象の次のorderのオブジェクトのオーダーを取得
        next_question_order = part_obj.order + 1

        # range(start, stop)にstopの値は結果に含まれないため+1する
        question_count += 1

        # 削除される対象以降のオブジェクトのorderをリストで取得
        next_question_list = list(range(next_question_order, question_count))

        # 削除する以降のオブジェクトを取得
        next_part_obj = QuestionnaireQuestion.objects.filter(order__in=next_question_list, parts=part_obj.parts)

        # 削除する対象のオブジェクトの次のオブジェクトに削除する対象のオーダーを入れる
        index = 0

        for next_part in next_part_obj:

            # 削除する対象以降のオーダーに削除する対象のオーダーを代入
            next_part.order = part_obj.order + index

            # for分が回るたびにindexが＋1される
            index += 1

            next_part.save()

        # 設問に紐づいている画像を取得
        images = part_obj.image.all()
        print("------------- images", images)

        if images:
            for image in images:
                print("---------- image ---------", image)# 変更前.PNG
                print("---------- image.size ---------", image.size)# 171330

                # 会社のディスク使用量に画像のサイズを引く
                this_resource_manage.total_file_size -= int(image.size)
                this_resource_manage.save()

                # 逆参照してその画像が紐づいている他のパーツの数を取得
                another_image_count = QuestionnaireQuestion.objects.filter(image=image).count()
                print("---------- another_image_count ---------", another_image_count)

                if another_image_count > 1:
                    print("---------- 他に画像が紐づいてる設問があったよ ---------")
                else:
                    print("---------- 設問に紐づく画像を削除 ---------")
                    # 設問に紐づく画像を削除
                    image.delete()

        part_obj.delete()

        # 削除後に設問編集画面に遷移させるためのパーツidを取得
        part = Parts.objects.filter(pk=part_obj.parts.id).first()

        # メッセージを返す
        messages.success(self.request, "アンケートの設問を削除しました。")

        return HttpResponseRedirect(reverse('training:questionnaire_management', kwargs={'pk': part.pk}))




"""
アンケートの設問の並び替え画面
"""
class QuestionnaireSortTopView(LoginRequiredMixin, CommonView, TemplateView):
    model = QuestionnaireQuestion
    template_name = 'training/questionnaire_sort_top.html'

    # テンプレートにモデルのデータを渡す
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # URLパラメータから送られたきたIDを取得
        parts_id = self.kwargs['pk']
        context["parts_id"] = parts_id

        questions = QuestionnaireQuestion.objects.filter(parts = parts_id).order_by('order')
        context["questions"] = questions

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context


"""
アンケートの設問の並べ替え
"""
class QuestionnaireSortDoneView(APIView):

    def post(self, request, *args, **kwargs):

        try:
            serial_1 = request.POST.getlist('serial[]')

            # 1から始まるインデックスと要素を同時に取得
            for index, question_id in enumerate(serial_1, 1):

                questionnaire_obj = QuestionnaireQuestion.objects.filter(pk=question_id).first()

                parts = questionnaire_obj.parts

                training_id =  Training.objects.filter(parts=parts).first()

                questionnaire_obj.order = index

                questionnaire_obj.save()

                qs = QuestionnaireQuestion.objects.order_by('order')

                questionnaire_obj = serializers.serialize("json", qs)


            message = f'アンケートの設問の並び順を変更しました。'
            messages.success(self.request, message)


            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "アンケートの並び順を変更しました",
                                "questionnaire_obj": questionnaire_obj,
                                "training_id": training_id.id,
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = '並び順の変更に失敗しました'
            return JsonResponse(data)




"""
テストの設問の並び替え画面
"""
class QuestionSortTopView(LoginRequiredMixin, CommonView, TemplateView):
    model = Question
    template_name = 'training/question_sort_top.html'

    # テンプレートにモデルのデータを渡す
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # URLパラメータから送られたきたIDを取得
        parts_id = self.kwargs['pk']

        questions = Question.objects.filter(parts = parts_id).order_by('order')
        context["questions"] = questions

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context


"""
テストの設問の並べ替え
"""
class QuestionSortDoneAjaxView(APIView):

    def post(self, request, *args, **kwargs):

        try:
            serial_1 = request.POST.getlist('serial[]')

            # 1から始まるインデックスと要素を同時に取得
            for index, question_id in enumerate(serial_1, 1):

                question_obj = Question.objects.filter(pk=question_id).first()

                parts = question_obj.parts

                training_id =  Training.objects.filter(parts=parts).first()

                question_obj.order = index

                question_obj.save()

                qs = Question.objects.order_by('order')

                question_obj = serializers.serialize("json", qs)


            message = f'テストの設問の並び順を変更しました。'
            messages.success(self.request, message)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "テストの並び順を変更しました",
                                "question_obj": question_obj,
                                "training_id": training_id.id,
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = '並び順の変更に失敗しました'
            return JsonResponse(data)



"""
グループ作成
"""
# class CustomGroupCreateView(LoginRequiredMixin, CommonView, CreateView):
class CustomGroupCreateView(LoginRequiredMixin, CommonView, FormView):
    # フォームを変数にセット
    model = CustomGroup
    template_name = 'training/input_customgroup.html'
    form_class = CustomGroupForm

    # formに値を渡す
    def get_form_kwargs(self):

        # formにログインユーザーを渡す
        kwargs = super(CustomGroupCreateView, self).get_form_kwargs()
        # kwargs.update({'user': self.request.user})
        kwargs['user'] = self.request.user

        # formにURL名(=input_customgroup)を渡す
        kwargs.update({'url_name': self.request.resolver_match.url_name})

        return kwargs

    def form_valid(self, form):

        print("-------------- グループ作成")

        # グループに対してユーザーを紐づける
        group_user_qs = form.cleaned_data['group_user']
        group_name = form.cleaned_data['name']
        print("-------------- group_user_qs", group_user_qs)# <QuerySet [<User: 平良 太郎 / 67121@test.jp>, <User: 矢崎 花子 / 6595@test.jp>]>
        print("-------------- group_name", group_name)

        # フォームからDBオブジェクトを仮生成
        # customgroup = form.save(commit=False)

        # 登録ユーザーを保存
        # customgroup.group_reg_user = self.request.user.id

        # CustomGroupモデルのnameフィールドにgroup_nameを保存
        custom_group, created = CustomGroup.objects.get_or_create(
            name = group_name,
            group_reg_user = self.request.user.id
        )
        custom_group.save()

        group = CustomGroup.objects.filter(name=group_name).first()
        print("-------------- group", group)

        # UserCustomGroupRelationモデルのgroup_idフィールドにグループのid、group_userにgroup_user_qsを保存
        for group_user in group_user_qs:
            print("-------------- group_user", group_user)

            user_custom_group_relation, created = UserCustomGroupRelation.objects.get_or_create(
                group_id = group.id,
                group_user = group_user.id,
                # tentative_group_flg = False
            )
            user_custom_group_relation.save()

        # 保存
        # customgroup.save()

        # customgroup.group_user.set(group_user_qs)# add()

        # 保存
        # customgroup.save()

        # メッセージを返す
        messages.success(self.request, "グループを作成しました。")

        return redirect('training:customgroup_management')




"""
グループ変更
"""
# class CustomGroupUpdateView(LoginRequiredMixin, CommonView, CreateView):
class CustomGroupUpdateView(LoginRequiredMixin, CommonView, FormView):

    # フォームを変数にセット
    model = CustomGroup
    template_name = 'training/customgroup_group_update.html'
    form_class = CustomGroupForm


    # セッションの中にtraining_creatが存在しているかチェック
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        session_url_name = ""
        if '_url_name' in self.request.session:
            session_url_name = self.request.session['_url_name']
        context["session_url_name"] = session_url_name

        # group_edit_check_session = ""
        # if 'group_edit_check_session' in self.request.session:
        #     group_edit_check_session = self.request.session['group_edit_check_session']
        # context["group_edit_check_session"] = group_edit_check_session

        return context


    # formに値を渡す
    def get_form_kwargs(self):
        kwargs = super(CustomGroupUpdateView, self).get_form_kwargs()

        # formにログインユーザーを渡す
        kwargs.update({'user': self.request.user})

        # formにURL名(=customgroup_group_update)を渡す
        kwargs.update({'url_name': self.request.resolver_match.url_name})

        # pkを渡す
        kwargs['pk'] = self.kwargs['pk']

        return kwargs


    # 追加
    def get_initial(self):

        # グループ編集ボタンからグループのIDを取得
        group_id = self.kwargs['pk']
        # print("-------------- group_id グループ編集", group_id)# 746e995c-58c3-4bc5-ba4f-4e83f0219143

        # IDと一致するグループを取得
        groups = CustomGroup.objects.filter(pk=group_id).first()
        # print("-------------- groups グループ編集", groups)# テスト

        user_groups = UserCustomGroupRelation.objects.filter(group_id=group_id)
        # print("-------------- groups グループ編集2222", user_groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (4)>, <UserCustomGroupRelation: UserCustomGroupRelation object (5)>]>

        group_user_email_list = []

        for group in user_groups:
            # print("-------------- groups グループ編集4444", group.group_user)# 平良 太郎 / 67121@test.jp
            group_user_email_list.append(group.group_user)

        initial={
            'name': groups.name,
            'group_user': group_user_email_list
        }

        # フロントに返す(ユーザー一覧に✔がついた状態で描画される)
        return initial


    def form_valid(self, form):

        print("------------------ グループ変更始まり")

        # 変更前のグループのユーザーを取得
        group_obj = CustomGroup.objects.filter(pk=self.kwargs['pk']).first()
        print("---------- group_obj ---------", group_obj)# asdffggg

        # 変更があったグループに紐づいているトレーニングを取得
        trainings = TrainingRelation.objects.filter(group_id=group_obj.id)
        # trainings = Training.objects.filter(destination_group=group_obj)
        print("---------- グループに紐づいているトレーニングを取得 ---------", trainings)# <QuerySet [<TrainingRelation: TrainingRelation object (101)>]>

        group_user_brfore_changes = UserCustomGroupRelation.objects.filter(group_id=group_obj.id)
        # group_user_brfore_changes = group_obj.group_user.all()
        print("---------- 変更前のグループのユーザー ---------", group_user_brfore_changes)

        # リスト化
        group_user_brfore_change_list = []
        # group_lists_raw_1 = list(group_user_brfore_changes.values_list('pk', flat=True))
        group_lists_raw_1 = list(group_user_brfore_changes.values_list('group_user', flat=True))

        # IDをstrに直してリストに追加
        for group_user_uuid_1 in group_lists_raw_1:
            group_user_uuid_string_1 = str(group_user_uuid_1)
            group_user_brfore_change_list.append(group_user_uuid_string_1)
        # print("---------- group_user_brfore_change_list ---------", group_user_brfore_change_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

        # 変更後のグループのユーザーを取得
        group_user_after_changes = form.cleaned_data['group_user']
        print("---------- 変更後のグループのユーザー ---------", group_user_after_changes)# <QuerySet [<User: 比嘉 太郎 / 69523@test.jp>, <User: 平良 太郎 / 67121@test.jp>]>

        # リスト化
        group_user_after_change_list = []
        group_lists_raw = list(group_user_after_changes.values_list('pk', flat=True))

        # IDをstrに直してリストに追加
        for group_user_uuid in group_lists_raw:
            group_user_uuid_string = str(group_user_uuid)
            group_user_after_change_list.append(group_user_uuid_string)
        # print("---------- group_user_after_change_list ---------", group_user_after_change_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

        # 変更前と変更後のグループのユーザーの差分から削除したユーザーを算出
        delete_user_set = set(group_user_brfore_change_list).difference(set(group_user_after_change_list))
        print("---------- 削除したユーザー ---------", delete_user_set)# {UUID('51ee2051-ebc9-46b2-82fe-3e9f2eabf439')}

        # グループに追加したユーザーを算出
        add_user_set = set(group_user_after_change_list).difference(set(group_user_brfore_change_list))
        print("---------- 追加したユーザー ---------", add_user_set)#  {'cb8cbe95-ee71-4b76-ba9c-123b62fed467'}

        # 削除したユーザーがいた場合
        if not len(delete_user_set) == 0:
            print("---------- 削除したユーザーいたよ ---------")

            # 削除したユーザーの差分をset型からリスト型に直す
            del_user_list = list(delete_user_set)
            print("---------- del_user_list ---------", del_user_list)

            # セッションが上書きされる前にセッションの値を取得、リストに追加する
            if 'deletion_user_id_json' in self.request.session:
                del_user_list.append(self.request.session['deletion_user_id_json'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "").replace('/', ""))

            # セッションに差分を保存 → TrainingUpdateViewで受け取る
            deletion_user_id_json = json.dumps(del_user_list)
            self.request.session['deletion_user_id_json'] = deletion_user_id_json
            # print("---------- 削除したユーザー session---------", self.request.session['deletion_user_id_json'])# f399cea5-41f3-4120-ad57-6975a13f7b0c 二つのグループ分取れている


        # 追加したユーザーがいた場合
        if not len(add_user_set) == 0:
            print("---------- 追加したユーザーいたよ ---------")

            # 追加したユーザーの差分をset型からリスト型に直す
            add_user_list = list(add_user_set)

            # セッションが上書きされる前にセッションの値を取得、リストに追加する
            if 'add_user_id_json' in self.request.session:
                add_user_list.append(self.request.session['add_user_id_json'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "").replace('/', ""))

            # セッションに差分を保存 → TrainingUpdateViewで受け取る
            add_user_id_json = json.dumps(add_user_list)
            self.request.session['add_user_id_json'] = add_user_id_json
            # print("---------- aaaaaaaaa ---------", self.request.session['add_user_id_json'])# ["9a058d25-384d-43e1-9a26-c1a680c87ab4", "9a058d25-384d-43e1-9a26-c1a680c87ab4"]

        # トレーニング変更から変更を行った場合　※使ってない
        if '_url_name' in self.request.session:
            print("---------- _url_nameあるよ ---------")

            training_id = self.request.session['_update_training']
            print("---------- training_id ---------", training_id)

            training = Training.objects.filter(id=training_id).first()
            print("---------- training ---------", training)

            training.group_edit_check_flg = True

            training.save()

            # グループを変更したことをTrainingUpdateViewに知らせる
            # self.request.session['group_edit_check_session'] = 'group_edit_check_session'

            # 変更前のグループのユーザーを取得
            group_obj = CustomGroup.objects.filter(pk=self.kwargs['pk']).first()

            # フォームからDBオブジェクトを仮生成
            # customgroup = form.save(commit=False)

            # 登録ユーザーを保存
            # customgroup.group_reg_user = self.request.use.id
            group_obj.group_reg_user = self.request.user.id

            # テンポラリフラグをONにする
            # customgroup.tempo_flg = True
            # group_obj.tempo_flg = True # コメントアウト

            # 戻るボタンを押したときにキャンセルできるようにUserCustomGroupRelationテーブルに変更した状態のグループを仮生成する
            for group_user_after_change in group_user_after_changes:
                tentative_group, created = UserCustomGroupRelation.objects.get_or_create(
                    group_id = group_obj.id,
                    group_user = group_user_after_change.id,
                    tentative_group_flg = True
                )
                tentative_group.save()

            # テンポラリフラグが立っているグループがあることをTrainingUpdateViewに知らせる用
            self.request.session['create_tempo_group'] = 'create_tempo_group'

            # 保存
            # customgroup.save()
            group_obj.save()

            # ReturnViewとReturnTrainingUpdateViewにセッションでテンポラリのフラグが立っているグループのIDを送る
            # tempo_flg_true_groups = CustomGroup.objects.filter(tempo_flg=True)
            tentative_groups = UserCustomGroupRelation.objects.filter(tentative_group_flg=True)
            # print("---------- tempo_flg_true_groups ---------", tempo_flg_true_groups)# <QuerySet [<CustomGroup: グループ1>]>

            # リストを用意
            # tempo_flg_true_group_list = []
            tentative_group_list = []

            # for tempo_flg_true_group in tempo_flg_true_groups:
            for tentative_group in tentative_groups:
                # print("---------- tempo_flg_true_group ---------", tempo_flg_true_group)# <QuerySet [<CustomGroup: グループ1>]>

                # tempo_customgroup_uuid_str = str(tempo_flg_true_group.pk)
                tentative_uuid_str = str(tentative_group.group_id)

                # tempo_flg_true_group_list.append(tempo_customgroup_uuid_str)
                tentative_group_list.append(tentative_uuid_str)

            # self.request.session['tempo_customgroup_id_json'] = tempo_flg_true_group_list
            self.request.session['tentative_group_id_json'] = tentative_group_list

            if set(group_user_brfore_change_list) == set(group_user_after_change_list):
                # 何もしない
                print("---------- 全員一致 ---------")
            # 全員一致しなかった場合
            else:
                print("---------- 全員一致しなかった ---------")

            # 新しいグループ名を古いグループ名に代入
            group_obj.name = form.cleaned_data['name']

            group_obj.save()

            print("------------------ グループ変更終わり")

            # メッセージを返す
            messages.success(self.request, "グループを編集しました。")

            return redirect('training:training_create')

        # グループ一覧から変更を行った場合
        else:
            print("---------- _url_nameないよ ---------")

            # グループに紐づいているトレーニングを取得
            # trainings = Training.objects.filter(destination_group=group_obj)
            training_relations = TrainingRelation.objects.filter(group_id=group_obj.id)
            print("---------- training_relations ---------", training_relations)# <QuerySet [<TrainingRelation: TrainingRelation object (50)>]>

            if set(group_user_brfore_change_list) == set(group_user_after_change_list):
                # 何もしない
                print("---------- 全員一致 ---------")
            # 全員一致しなかった場合
            else:
                print("---------- 全員一致しなかった ---------")
                # グループのメンバーを新しく追加した場合
                if add_user_set:
                    print("---------- 追加するよ ---------")

                    for add_user in add_user_set:
                        user = User.objects.filter(pk=add_user).first()
                        print("---------- 追加するユーザー ---------", user)

                        if training_relations:
                            for training_relation in training_relations:
                                print("---------- training_relation.training_id ---------", training_relation.training_id)# ad10bba7-86f4-4c73-90b7-6e1327976379

                                # training = Training.objects.filter(id=training_relation.training_id).first()
                                trainings = Training.objects.filter(id=training_relation.training_id)
                                print("---------- trainings ---------", trainings)# トレーニング1

                                for training in trainings:
                                    print("---------- training ---------", training)# トレーニング1

                                    # 新しくグループに追加されたユーザー分のTrainingManagesを作成する
                                    if not TrainingManage.objects.filter(user=user.id, training=training):
                                        print("---------- TrainingManagesを作成する ---------")
                                        training_manage, created = TrainingManage.objects.get_or_create(
                                            training = training,
                                            user = user.id,
                                            status = 1, # 未対応
                                            subject_manage = training.subject
                                        )
                                        training_manage.save()

                                    # TrainingHistoryテーブルにトレーニングの情報を残す
                                    if not TrainingHistory.objects.filter(user=user.id, training=training):
                                        print("---------- TrainingHistoryを作成する ---------")
                                        training_history, created = TrainingHistory.objects.get_or_create(
                                            training = training,
                                            reg_user = training.reg_user,
                                            user = training_manage.user,
                                            status = 1
                                        )
                                        training_history.save()

                        # UserCustomGroupRelationモデルのgroup_idフィールドにグループのid、group_userにuserのidを保存
                        user_custom_group_relation, created = UserCustomGroupRelation.objects.get_or_create(
                            group_id = group_obj.id,
                            group_user = user.id,
                        )
                        user_custom_group_relation.save()

                    # セッションデータを削除する
                    del self.request.session['add_user_id_json']

                # グループのメンバーを削除した場合
                if delete_user_set:
                    print("---------- 削除するよ ---------")

                    # 削除するユーザーをリストに変換
                    delete_user_list = list(delete_user_set)
                    print("---------- delete_user_list ---------", delete_user_list)# ['9a058d25-384d-43e1-9a26-c1a680c87ab4']

                    # UserCustomGroupRelationテーブルから削除するユーザーの情報を削除
                    del_user_custom_group_relations = UserCustomGroupRelation.objects.filter(group_user__in=delete_user_list, group_id=group_obj.id)
                    print("--------------- del_user_custom_group_relations 削除するユーザー --------------", del_user_custom_group_relations)

                    del_user_custom_group_relations.delete()

                    # 変更があったグループにトレーニングが紐づいている場合、重複ユーザーチェック後、削除したユーザーのTrainingManageを削除する処理を行う
                    # if trainings:
                    if training_relations:
                        print("---------- 変更があったグループにトレーニングが紐づいてるよ ---------")

                        for training_relation in training_relations:
                            print("---------- training_relation.training_id ---------", training_relation.training_id)# ad10bba7-86f4-4c73-90b7-6e1327976379

                            trainings = Training.objects.filter(id=training_relation.training_id)
                            print("---------- trainings ---------", trainings)# トレーニング1

                            for training in trainings:
                                print("---------- training ---------", training)# トレーニング1

                                # トレーニングに紐づくグループを取得
                                groups = TrainingRelation.objects.filter(training_id=training.id)
                                print("---------- groups ---------", groups)# TrainingRelation object (85)

                                # グループのIDをstrに直してリストに追加
                                group_list = []
                                group_lists_raw = list(groups.values_list('group_id', flat=True))
                                for group_uuid in group_lists_raw:
                                    group_uuid_string = str(group_uuid)
                                    group_list.append(group_uuid_string)
                                # print("---------- group_list ---------", group_list)# ['b376583f-6687-4db0-b2b3-f59d51885e1d']

                                # グループに所属しているユーザーを取り出す
                                user_custom_groups = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
                                print("---------- user_custom_groups ---------", user_custom_groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (152)>, <UserCustomGroupRelation: UserCustomGroupRelation object (192)>, <UserCustomGroupRelation: UserCustomGroupRelation object (200)>]>

                                # IDをstrに直してリストに追加
                                group_user_list = []
                                group_user_lists_raw = list(user_custom_groups.values_list('group_user', flat=True))
                                for ggroup_user_uuid in group_user_lists_raw:
                                    group_user_uuid_string = str(ggroup_user_uuid)
                                    group_user_list.append(group_user_uuid_string)
                                # print("---------- group_user_list ---------", group_user_list)# ['76d54969-96ad-4485-ac02-e38612d5c070', '6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '9a058d25-384d-43e1-9a26-c1a680c87ab4']

                                # set()で重複しているユーザーをリストから除外する
                                user_id_list = list(set(group_user_list))

                                # ユーザーの中に削除するユーザーが重複しているかチェック
                                # 重複しているユーザーが存在する場合
                                if set(delete_user_list) & set(user_id_list):
                                    # 重複しているユーザーのTrainingManageは消さない
                                    print("--------------- 重複しているユーザーが存在する")

                                    repetitive_user = set(delete_user_list) & set(user_id_list)
                                    repetitive_user_list = list(repetitive_user)
                                    print("---------- repetitive_user_list", repetitive_user_list)

                                    # 重複ユーザーを除いたユーザーと一致するTrainingManageを取得
                                    user_training_manages_qs = TrainingManage.objects.filter(user__in=delete_user_list, training=training.id).exclude(user__in=repetitive_user_list)
                                    print("--------------- 重複するユーザーを除いたユーザーと一致するTrainingManageを取得(削除) if --------------", user_training_manages_qs)

                                    # 重複ユーザーを除いたユーザーと一致するトグルボタンの展開データを取得
                                    user_folder_is_open_qs = FolderIsOpen.objects.filter(user_id__in=delete_user_list, training=training.id).exclude(user_id__in=repetitive_user_list)
                                    print("---------- user_folder_is_open_qs ---------", user_folder_is_open_qs)

                                else:
                                    print("--------------- 重複しているユーザーが存在しない")

                                    # 削除対象のユーザーと一致するTrainingManageを取得
                                    user_training_manages_qs = TrainingManage.objects.filter(user__in=delete_user_list, training=training.id)# <QuerySet [<TrainingManage: TrainingManage object (480)>]>
                                    print("--------------- 削除対象のユーザーと一致するTrainingManageを取得(削除) else --------------", user_training_manages_qs)

                                    # 重複ユーザーを除いたユーザーと一致するトグルボタンの展開データを取得
                                    user_folder_is_open_qs = FolderIsOpen.objects.filter(user_id__in=delete_user_list, training=training.id)
                                    print("---------- user_folder_is_open_qs ---------", user_folder_is_open_qs)

                                # 削除対象のユーザーと一致するPartsgManageを取得
                                for user_training_manages in user_training_manages_qs:
                                    print("--------------- user_training_manages", user_training_manages)# TrainingManage object (509)
                                    user_parts_manages = user_training_manages.parts_manage.all()
                                    print("--------------- ユーザーのparts_manage", user_parts_manages)# <QuerySet [<PartsManage: PartsManage object (57)>]>
                                    # PartsgManageを削除
                                    user_parts_manages.delete()

                                # TrainingManageを削除
                                user_training_manages_qs.delete()

                                # トグルボタンの展開データを削除
                                user_folder_is_open_qs.delete()

                    # セッションデータを削除する
                    del self.request.session['deletion_user_id_json']

            # 新しいグループ名を古いグループ名に代入
            group_obj.name = form.cleaned_data['name']

            group_obj.save()

            # メッセージを返す
            messages.success(self.request, "グループを編集しました。")

            return redirect('training:customgroup_management')


"""
続けてパーツを作成しない場合の処理(トレーニング詳細設定)
"""
class CancelPartsRegisterView(View):
    def get(self, request, *args, **kwargs):

        # セッションデータがあるか判定
        if 'training_register_done' in self.request.session:
            # セッションデータを削除する
            del self.request.session['training_register_done']

        # セッションデータがあるか判定
        if 'training_id_str' in self.request.session:
            # セッションデータを削除する
            del self.request.session['training_id_str']

        return HttpResponseRedirect(reverse('training:training_management'))


"""
カスタムユーザー管理画面
"""
class CustomGroupManagementView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/customgroup_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        is_training_done = TrainingDone.objects.filter(user_id=current_user.pk).first()
        print("------------------------カスタムユーザー管理画面 training_done_chg", is_training_done)


        # 完了済みのトレーニングの非表示
        # if current_user.is_training_done:
        # if is_training_done:

        #     trainings = Training.objects.filter(destination_user__in=[current_user.id]).exclude(status="3") \
        #     .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        #     context["trainings"] = trainings

        # # 全表示
        # else:

        #     trainings = Training.objects.filter(destination_user__in=[current_user.id]) \
        #     .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        #     context["trainings"] = trainings

        groups = CustomGroup.objects.filter(group_reg_user=current_user.id)# ここ
        # groups = CustomGroup.objects.all()
        context["groups"] = groups

        user_custom_group_relations = UserCustomGroupRelation.objects.all()
        context["user_custom_group_relations"] = user_custom_group_relations

        # for key in list(self.request.session.keys()):
        #     if not key.startswith("_"):
        #         del self.request.session[key]

        # セッションデータがあるか判定
        if '_url_name' in self.request.session:
            # セッションデータを削除する
            del self.request.session['_url_name']

        # セッションデータがあるか判定
        # if 'group_edit_check_session' in self.request.session:
        #     print("---------------- group_edit_check_sessionがあるよ")
        #     # セッションデータを削除する
        #     del self.request.session['group_edit_check_session']


        return context



"""
コース管理画面
"""
class SubjectManagementView(LoginRequiredMixin, ListView, CommonView):
    model = SubjectManagement
    template_name = 'training/subject_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # subjectes = SubjectManagement.objects.filter(Q(subject_reg_user=self.request.user.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')
        subjectes = SubjectManagement.objects.filter(Q(subject_reg_company=self.request.user.company.id)|Q(subject_name="デフォルト")).order_by('created_subject_date')
        print("---------- subjectes", subjectes)
        context["subjectes"] = subjectes
        context["subjecte_count"] = subjectes.count()

        # セッションデータがあるか判定
        if '_url_name' in self.request.session:
            # セッションデータを削除する
            del self.request.session['_url_name']

        # セッションデータがあるか判定
        # if 'group_edit_check_session' in self.request.session:
        #     print("---------------- group_edit_check_sessionがあるよ")
        #     # セッションデータを削除する
        #     del self.request.session['group_edit_check_session']

        return context


"""
コース、ポスターをアップロードする処理
"""
class SubjectPosterUploadView(View):
    def post(self, request, *args, **kwargs):

        up_poster_id = []
        i = 1

        # アップロードされたファイルを得る
        for upload_poster in self.request.FILES.values():

            poster, created = SubjectImage.objects.get_or_create(
                name = upload_poster.name,
                size = upload_poster.size,
                subject_image = upload_poster,
            )

            # 保存
            poster.save()

            # file.idを配列に入れている
            up_poster_id.append(poster.id)

            i+=1

        # 保存したファイルをセッションへ保存,ログアウトしない限りそのセッションが残る
        up_subject_poster_id_json = json.dumps(up_poster_id)

        self.request.session['up_subject_poster_id'] = up_subject_poster_id_json

        # 何も返したくない場合、HttpResponseで返す
        return HttpResponse(up_poster_id)


"""
コースの作成
"""
class SubjectManagementCreateView(LoginRequiredMixin, CommonView, CreateView):
    model = SubjectManagement
    template_name = 'training/subject_management_create.html'
    form_class = SubjectManagementForm

    # ログインユーザーを返す
    def get_form_kwargs(self):
        kwargs = super(SubjectManagementCreateView, self).get_form_kwargs()
        kwargs["login_user"] = self.request.user

        # formにURL名(=subject_management_create)を渡す
        kwargs.update({'url_name': self.request.resolver_match.url_name})

        return kwargs

    def form_valid(self, form):

        # フォームからDBオブジェクトを仮生成
        subject_management = form.save(commit=False)
        # print("-------------- subject_management", subject_management)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        # 登録ユーザーを保存
        # subject_management.subject_reg_user = self.request.user
        subject_management.subject_reg_user = current_user.id

        # 登録ユーザーの会社を保存
        subject_management.subject_reg_company = current_user.company.id

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("------------- this_resource_manage コースの作成", this_resource_manage)

        # レコードがなかった場合
        if this_resource_manage is None:
            print("---------- this_resource_manageがなかったよ ---------")
            # Resource_Managementにトレーニングを作成した会社の管理テーブルを作成
            resource_manage, created = ResourceManagement.objects.get_or_create(
                reg_company_name = current_user.company.id,
                number_of_training = 0,
                number_of_file = 0, # 1トレーニング=20KB(=20480B)
                total_file_size = 0
            )
            resource_manage.save()

        # 保存
        subject_management.save()

        # セッションの中にup_poster_idがれば取り出す ※ポスターがない場合はデフォルトの画像が適用される
        if 'up_subject_poster_id' in self.request.session:

            print("---------- up_subject_poster_idがあるよaaaaaa ---------")

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_poster_id_str = self.request.session['up_subject_poster_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_poster_id_list = up_poster_id_str.split(',')

            # リストのInt型に変換
            up_poster_id_int = [int(s) for s in up_poster_id_list]

            # オブジェクトの取得
            poster = SubjectImage.objects.filter(pk__in=up_poster_id_int).first()
            print("---------- poster. ---------", poster)

            # タスクとファイルを紐付ける
            subject_management.subject_image = poster

            subject_management.save()

            # 会社のディスク使用量にポスターのサイズを足す
            this_resource_manage.total_file_size += int(poster.size)
            this_resource_manage.save()

            # セッションデータを削除する
            del self.request.session['up_subject_poster_id']

        else:
            print("---------- up_subject_poster_idなかったよ ---------")

            # 会社のディスク使用量にポスターのサイズを足す
            this_resource_manage.total_file_size += settings.DEFAULT_SUBJECT_POSTER
            this_resource_manage.save()


        # メッセージを返す
        messages.success(self.request, "コースを作成しました。")

        return redirect('training:subject_management')


"""
コースの変更
"""
class SubjectManagementUpdateView(LoginRequiredMixin, CommonView, UpdateView):
    model = SubjectManagement
    template_name = 'training/subject_management_update.html'
    form_class = SubjectManagementForm

    # ログインユーザーを返す
    def get_form_kwargs(self):
        kwargs = super(SubjectManagementUpdateView, self).get_form_kwargs()

        # formにログインユーザーを渡す
        kwargs["login_user"] = self.request.user
        # formにURL名(=subject_management_update)を渡す
        kwargs.update({'url_name': self.request.resolver_match.url_name})
        # pkを渡す
        kwargs['pk'] = self.kwargs['pk']

        return kwargs


    # 変更処理
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        suject_pk = self.kwargs['pk']
        # print("$$$$$$$$$$$$$", suject_pk)# f06c043f-ec92-424e-9c3e-ec8b9f4a071a

        # トレーニングに紐づいているファイルを取得
        subject = SubjectManagement.objects.get(pk=suject_pk)
        print("$$$$$$$$$$$$$", subject)
        print("$$$$$$$$$$$$$", subject.subject_image)

        # json形式でシリアライズする(動画)
        if subject.subject_image:
            print("画像があったよ")
            dist_poster = serializers.serialize("json", [ subject.subject_image ])
        else:
            print("画像がなかったよ")
            dist_poster = None

        # フロントに返す
        context["dist_poster"] = dist_poster

        return context


    def form_valid(self, form):

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        before_subject = SubjectManagement.objects.filter(id=self.kwargs['pk']).first()
        print("---------- before_subject ---------", before_subject)
        print("---------- before_subject.poster.name ---------", before_subject.subject_image.name)
        # print("---------- before_subject.poster.size ---------", before_subject.subject_image.size)

        # ユーザーが設定したポスターからデフォルトポスターに変更した場合
        # if before_subject.subject_image.name == "default_subject_image":
        if before_subject.subject_image.name == settings.DEFAULT_SUBJECT_IMAGE:
            print("---------- デフォルトポスターに変更したよ ---------")
            # 会社のディスク使用量からデフォルトで設定されているポスターのサイズを足す
            this_resource_manage.total_file_size += settings.DEFAULT_SUBJECT_POSTER
            this_resource_manage.save()

        # フォームからDBオブジェクトを仮生成
        subject_management_update = form.save(commit=False)

        # 選択したトレーニングを取得
        # subject_reg_training_qs = form.cleaned_data['subject_reg_training']
        # print("---------- 選択したトレーニング(変更)---------", subject_reg_training_qs)

        # コースにトレーニングを紐づける
        # subject_management_update.subject_reg_training.set(subject_reg_training_qs)

        # 保存
        subject_management_update.save()

        # セッションの中にup_poster_idがれば取り出す ※ポスターがない場合はデフォルトの画像が適用される
        if 'up_subject_poster_id' in self.request.session:
            print("---------- up_subject_poster_idがあったよ ---------")

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_poster_id_str = self.request.session['up_subject_poster_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_poster_id_list = up_poster_id_str.split(',')

            # リストのInt型に変換
            up_poster_id_int = [int(s) for s in up_poster_id_list]

            # オブジェクトの取得
            poster = SubjectImage.objects.filter(pk__in=up_poster_id_int).first()
            print("---------- poster.name ---------", poster.name)
            print("---------- poster.size ---------", poster.size)

            # ポスター変更前がデフォルトポスターだった場合
            # if before_subject.subject_image.name == "default_subject_image":
            if before_subject.subject_image.name == settings.DEFAULT_SUBJECT_IMAGE:
                print("---------- デフォルトポスターだったよ ---------")
                # 会社のディスク使用量からデフォルトで設定されているポスターのサイズを引く
                this_resource_manage.total_file_size -= settings.DEFAULT_POSTER
                this_resource_manage.save()

            # 会社のディスク使用量に変更したポスターのサイズを足す
            this_resource_manage.total_file_size += int(poster.size)
            this_resource_manage.save()

            # タスクとファイルを紐付ける
            subject_management_update.subject_image = poster

            subject_management_update.save()

            # セッションデータを削除する
            del self.request.session['up_subject_poster_id']

        # メッセージを返す
        messages.success(self.request, "コースを編集しました。")

        return redirect('training:subject_management')


"""
コースの削除(個別)
"""
class SubjectDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'training/subject_management.html'
    model = SubjectManagement
    form_class = SubjectManagementForm

    def delete(self, *args, **kwargs):

        subject_id = self.kwargs['pk']
        print("----------- subject_id", subject_id)

        subject = SubjectManagement.objects.filter(pk=subject_id).first()
        print("----------- subject", subject)

        subject.delete()

        # メッセージを返す
        messages.success(self.request, "コースを削除しました")

        return HttpResponseRedirect(reverse('training:subject_management'))


"""
コースの削除(一括)
"""
class AllSubjectDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            # 削除にチェックをしたコースIDを取得
            checks = request.POST.getlist('checks[]')
            print("---------- checks ---------", checks)

            # IDと一致するコースを削除
            del_subject = SubjectManagement.objects.filter(pk__in=checks).delete()
            print("---------- del_subject ---------", del_subject)

            message = f'コースを削除しました。'
            messages.success(self.request, message)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "コースを削除しました",
                                })

        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'コースの削除に失敗しました'
            return JsonResponse(data)


"""
コース、ポスターの削除
"""
class SubjectPosterDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            poster_pk = request.POST.get('file_name')

            # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
            this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
            print("---------- this_resource_manage ---------", this_resource_manage)

            # # 1から始まるインデックスと要素を同時に取得
            poster_obj = SubjectImage.objects.filter(pk=poster_pk).first()
            print("---------- poster_obj ---------", poster_obj)
            print("---------- poster_obj.size ---------", poster_obj.size)

            # 会社のディスク使用量にファイルのサイズを引く
            this_resource_manage.total_file_size -= int(poster_obj.size)
            this_resource_manage.save()

            poster_obj.delete()

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "サーバーからポスターを削除しました",
                                })

        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'ポスターの削除に失敗しました'
            return JsonResponse(data)




class TrainingListView(DetailView):
    template_name = 'training/training_list.html'
    # model = SubjectManagementForm
    model = SubjectManagement

    # def get_queryset(self):
    #     return super().get_queryset().filter(subject_reg_user=self.request.user.id)


"""
タスク用グループ一括登録
"""
# class CustomGroupBulkCreateView(LoginRequiredMixin, CommonView, CreateView):
class CustomGroupBulkCreateView(LoginRequiredMixin, CommonView, FormView):

    model = CustomGroup
    template_name = 'training/customgroup_bulk_create.html'
    form_class = CustomGroupBulkCreationForm


    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(CustomGroupBulkCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


    def form_valid(self, form):

        # グループ名の取得
        group_name = form.cleaned_data['name']
        print("-------------- group_name", group_name)

        # グループに紐づくユーザーの取得
        reg_user_num = form.cleaned_data['group_user']
        print("-------------- reg_user_num", reg_user_num)

        # リストに変換
        reg_user_list = reg_user_num.splitlines()
        print("-------------- reg_user_list", reg_user_list)

        # ユーザモデルからリスト内のユーザーとメールアドレスが一致するユーザーのクエリーセットを取得
        group_users = User.objects.filter(email__in=reg_user_list)
        print("-------------- group_users", group_users)

        # グループを作成する
        # group = CustomGroup.objects.create(
        #     name=group_name,
        #     group_reg_user=self.request.user,
        #     reg_date=datetime.now()
        # )
        # CustomGroupモデルのnameフィールドにgroup_nameを保存
        group, created = CustomGroup.objects.get_or_create(
            name = group_name,
            group_reg_user = self.request.user.id,
            reg_date = datetime.now()
        )
        group.save()


        # 一度保存してUserのIDを生成してからServiceを登録する
        # group_userはquerysetになっているためobject.set()で保存
        # group.group_user.set(group_users)

        # UserCustomGroupRelationモデルのgroup_idフィールドにグループのid、group_userにgroup_user_qsを保存
        for group_user in group_users:
            print("-------------- group_user", group_user)

            user_custom_group_relation, created = UserCustomGroupRelation.objects.get_or_create(
                group_id = group.id,
                group_user = group_user.id,
            )
            user_custom_group_relation.save()


        messages.success(self.request, "グループを作成しました。")

        return redirect('training:customgroup_management')



"""
トレーニング管理画面(全て表示)
"""
class TrainingChangeManagementView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/training_change_management_all.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        # 逆参照して管理者を引っ張ってくる
        # co_admin = CoAdminUserManagement.objects.filter(admin_user=current_user).first()
        # co_admin = CoAdminUserManagement.objects.filter(admin_user=current_user.id).first()
        # print("----------------------- co_admin", co_admin)# CoAdminUserManagement object (5)
        # print("----------------------- co_admin.admin_user", co_admin.admin_user)# 28caa177-ce84-411f-9775-bffc81d22075

        # co_admin_user_objects = CoAdminUserManagement.objects.filter(co_admin_user__in=[current_user])
        co_admin_user_objects = CoAdminUserManagementRelation.objects.filter(co_admin_user_id__in=[current_user.id])
        print("----------------------- co_admin_user_objects", co_admin_user_objects)# <QuerySet [<CoAdminUserManagement: CoAdminUserManagement object (2)>]>


        # 共同管理者の場合、管理者の情報を取得する
        if co_admin_user_objects:
            print("----------------------- 共同管理者です")

            co_admin_user_list = []

            for co_admin_user in co_admin_user_objects:
                # print("----------------------- 共同管理者の管理者aaaaaa", co_admin_user)
                # print("----------------------- 共同管理者の管理者bbbbbb", co_admin_user.admin_user)# 主査研修担当 / jinji-admin@test.jp
                # print("----------------------- 共同管理者の管理者bbbbbb", co_admin_user.admin_user_id)# 76d54969-96ad-4485-ac02-e38612d5c070

                # 管理者をリストに追加
                # co_admin_user_list.append(co_admin_user.admin_user)
                co_admin_user_list.append(co_admin_user.admin_user_id)

            # print("----------------------- list ccccccc", co_admin_user_list)
            #  [<User: 主査研修担当 / jinji-admin@test.jp>, <User: テストユーザー / user@user.com>]

            # 管理者が作成したトレーニングを取得
            trainings = Training.objects.filter(reg_user__in=co_admin_user_list)
            context["trainings"] = trainings

        else:
            print("----------------------- 管理者です")

            # ログインしているユーザーが管理者の場合 そのユーザーが作成したトレーニングを取得する
            trainings = Training.objects.filter(reg_user=current_user.id)
            context["trainings"] = trainings

        return context




"""
トレーニング管理画面(未対応)
"""
class TrainingChangeManagementWaitingView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/training_change_management_waiting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

        group_obj_lists = []

        for group in groups:
            group_obj_lists.append(group)

        # リスト化
        group_lists_raw = list(groups.values_list('pk', flat=True))

        group_lists = []

        for group_uuid in group_lists_raw:

            group_uuid_string = str(group_uuid)

            group_lists.append(group_uuid_string)


        # TrainingManageからログインユーザーの未対応のオブジェクトを取得する
        # trainings = TrainingManage.objects.filter(user=current_user, status="1")
        trainings = Training.objects.filter(reg_user=current_user.id, training_manage__status="1").order_by('end_date').distinct()
        context["trainings"] = trainings

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]


        return context



"""
トレーニング管理画面(対応中)
"""
class TrainingChangeManagementWorkingView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/training_change_management_working.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

        group_obj_lists = []

        for group in groups:
            group_obj_lists.append(group)

        # リスト化
        group_lists_raw = list(groups.values_list('pk', flat=True))

        group_lists = []

        for group_uuid in group_lists_raw:

            group_uuid_string = str(group_uuid)

            group_lists.append(group_uuid_string)


        # TrainingManageからログインユーザーの対応中のオブジェクトを取得する
        # trainings = TrainingManage.objects.filter(user=current_user, status="2")
        trainings = Training.objects.filter(reg_user=current_user.id, training_manage__status="2").order_by('end_date').distinct()

        context["trainings"] = trainings


        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]


        return context




"""
トレーニング管理画面(完了)
"""
class TrainingChangeManagementDoneView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
    model = Training
    template_name = 'training/training_change_management_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        trainings = Training.objects.filter(destination_user__in=[current_user.id]) \
        .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        context["trainings"] = trainings

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]


        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_user = User.objects.filter(pk=self.request.user.id).first()

        groups = CustomGroup.objects.filter(group_user__in=[current_user.id])

        group_obj_lists = []

        for group in groups:
            group_obj_lists.append(group)

        # リスト化
        group_lists_raw = list(groups.values_list('pk', flat=True))

        group_lists = []

        for group_uuid in group_lists_raw:

            group_uuid_string = str(group_uuid)

            group_lists.append(group_uuid_string)


        # TrainingManageからログインユーザーの完了のオブジェクトを取得する
        # trainings = TrainingManage.objects.filter(user=current_user, status="3")
        trainings = Training.objects.filter(reg_user=current_user.id, training_manage__status="3").order_by('end_date').distinct()

        context["trainings"] = trainings


        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]


        return context





"""
トレーニング編集画面
"""
# class TrainingEditMenulView(LoginRequiredMixin, ListView, CommonView, TraningStatusCheckView):
class TrainingEditMenulView(LoginRequiredMixin, TemplateView, CommonView, FormView, TraningStatusCheckView):

    model = Training
    template_name = 'training/training_edit_menu.html'
    form_class = GuestUserLinkForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["login_user"] = self.request.user

        current_user = User.objects.filter(pk=self.request.user.id).first()

        # ログインユーザーのリソース状況を取得
        resource_management = ResourceManagement.objects.filter(reg_company_name=current_user.company.id).first()
        # BをMBに変換
        total_file_size = resource_management.total_file_size / 1024 / 1024
        # 小数第2位を切り捨て
        total_file_size = round(total_file_size, 2)
        # 残容量
        remaining_capacity = 500 - total_file_size

        # 残容量がマイナスの値なら0にする
        if remaining_capacity < 0:
            remaining_capacity = 0

        context["remaining_capacity"] = remaining_capacity

        training_id = self.kwargs['pk']
        context["training_id"] = training_id

        trainings = Training.objects.filter(id=training_id) \
        .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))
        context["trainings"] = trainings

        # 管理者が登録したゲストユーザーを取得
        # guest_users = GuestUserManagement.objects.filter(resister_user=self.request.user)

        # if guest_users:
        #     context["guest_users"] = guest_users

        # QuestionRegisterViewで立てたセッションのフラグをフロントに返す
        if 'question_register_done' in self.request.session:
            question_register_done = self.request.session['question_register_done']
            print("--------------- セッションある --------------")

        # QuestionnaireRegisterViewで立てたセッションのフラグをフロントに返す
        if 'questionnaire_register_done' in self.request.session:
            questionnaire_register_done = self.request.session['questionnaire_register_done']
            print("--------------- セッションある --------------")

        # テストパーツのIDのセッションデータをフロントに返す
        if 'parts_id_str' in self.request.session:
            parts_id_str = self.request.session['parts_id_str'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "")
            context["parts_id_str"] = parts_id_str

        # アンケートパーツのIDのセッションデータをフロントに返す
        if 'questionnaire_parts_id_str' in self.request.session:
            questionnaire_parts_id_str = self.request.session['questionnaire_parts_id_str'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "")
            context["questionnaire_parts_id_str"] = questionnaire_parts_id_str

        # セッションデータがあるか判定
        if 'training_register_done' in self.request.session:
            # セッションデータを削除する
            del self.request.session['training_register_done']

        # セッションデータがあるか判定
        if 'training_id_str' in self.request.session:
            # セッションデータを削除する
            del self.request.session['training_id_str']

        # セッションデータがあるか判定
        if 'tempo_customgroup_id_json' in self.request.session:
            # セッションデータを削除する
            del self.request.session['tempo_customgroup_id_json']

        return context

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(TrainingEditMenulView, self).get_form_kwargs()

        guest_user_lists = []

        # guest_users = GuestUserManagement.objects.filter(resister_user=self.request.user)
        guest_users = GuestUserManagement.objects.filter(resister_user=self.request.user.id)

        # 共同管理者に指定されているユーザーを取り出す
        for guest_user in guest_users:
            # リストにユーザーのIDを追加
            guest_user_lists.append(guest_user)

        # formにリストを渡す
        kwargs.update({'guest_user_lists': guest_user_lists})

        # ログインしている管理者が所属する会社を取得
        kwargs.update({'admin_user': self.request.user})

        return kwargs

    # ゲストユーザーとトレーニングの紐づけ
    def post(self, request, *args, **kwargs):

        print("------------ ゲストユーザーとトレーニングの紐づけ")

        # POSTで送られてきた値を取得
        guest_user_id_list = request.POST.getlist('guest_user_name')
        print("------------ guest_user_id_list", guest_user_id_list)

        # pkと一致するゲストユーザーを取得
        guest_users = GuestUserManagement.objects.filter(pk__in=guest_user_id_list)
        print("------------ guest_users", guest_users)

        # トレーニングを取得
        training_id = self.kwargs['pk']
        training = Training.objects.filter(pk=training_id).first()
        print("------------ training", training)

        # トレーニングにゲストユーザーを紐づける
        training.destination_guest_user.set(guest_users)

        # 保存
        training.save()

        for guest_user in guest_users:

            print("------------ guest_user", guest_user)

            if not TrainingManage.objects.filter(guest_user_manage=guest_user, training=training):
                print("------------ TrainingManageがない")
                # TrainingManageにユーザー分の管理テーブルを作成
                training_manage, created = TrainingManage.objects.get_or_create(
                    training = training,
                    guest_user_manage = guest_user,
                    status = 1, # 未対応
                    subject_manage = training.subject
                )
                training_manage.save()

            # TrainingHistoryテーブルにトレーニングの情報を残す
            if not TrainingHistory.objects.filter(guest_user_history=guest_user, training=training):
                print("------------ TrainingHistoryがない")
                training_history, created = TrainingHistory.objects.get_or_create(
                    training = training,
                    reg_user = training.reg_user,
                    guest_user_history = guest_user,
                    status = 1
                )
                training_history.save()

        message = f'トレーニングにゲストユーザーを紐づけました。'
        messages.success(self.request, message)

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))






"""
トレーニングの削除
"""
class TrainingDeleteView(DeleteView):
    model = Training
    template_name = 'training/training_edit_menu.html'

    def get_success_url(self):
        print("------------ トレーニングの削除 ------------")

        training_id = self.kwargs['pk']
        training = Training.objects.filter(pk=training_id).first()
        print("------------ training", training)

        # training_manage = TrainingManage.objects.filter(training=training_id).first()
        training_manage = TrainingManage.objects.filter(training=training_id)
        print("------------ training_manage", training_manage)

        # ユーザーのTrainingHistoryを取得
        training_historys = TrainingHistory.objects.filter(training=training_id)
        print("------------ training_historys", training_historys)

        # ユーザーのTrainingHistoryにtrainingの情報をコピーする
        for training_history in training_historys:
            training_history.title = training.title
            training_history.description = training.description
            training_history.reg_user = training.reg_user
            training_history.start_date = training.start_date
            training_history.end_date = training.end_date
            # 削除フラグをtrueにする
            training_history.del_flg = True

            # 保存
            training_history.save()

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        parts_all = training.parts.all()
        print("---------- parts_all ---------", parts_all)

        if parts_all:
            print("---------- parts_allがあるよ ---------")

            for parts in parts_all:

                # ファイルパーツの場合
                if parts.type == 1:
                    print("---------- ファイルパーツです ---------")

                    # 逆参照してそのファイルが紐づいている他のパーツの数を取得
                    # another_parts_count = Parts.objects.filter(file__in=parts.file.all()).count()
                    # print("---------- another_parts_count ---------", another_parts_count)

                    for file in parts.file.all():
                        # 会社のディスク使用量にファイルのサイズを引く
                        this_resource_manage.total_file_size -= int(file.size)
                        this_resource_manage.save()

                        # 紐づいているファイルごとにいくつパーツに紐づいているか判定する
                        another_parts_count = Parts.objects.filter(file=file).count()
                        print("---------- another_parts_count ---------", another_parts_count)

                        if another_parts_count > 1:
                            print("---------- 他にファイルが紐づいてるパーツがあったよ ---------")
                        else:
                            # パーツに紐づくファイルを削除
                            file.delete()

                if parts.type == 2:
                    print("---------- 動画パーツです ---------")

                    # 逆参照してその動画が紐づいている他のパーツの数を取得
                    another_movie_count = Parts.objects.filter(movie=parts.movie).count()
                    print("---------- another_movie_count ---------", another_movie_count)

                    # 逆参照してそのポスターが紐づいている他のパーツの数を取得
                    another_poster_count = Parts.objects.filter(poster=parts.poster).count()
                    print("---------- another_poster_count ---------", another_poster_count)

                    # 会社のディスク使用量から動画のサイズを引く
                    this_resource_manage.total_file_size -= int(parts.movie.size)
                    this_resource_manage.save()

                    if another_movie_count > 1:
                        print("---------- 他に動画が紐づいてるパーツがあったよ ---------")
                    else:
                        # パーツに紐づく動画を削除
                        parts.movie.delete()

                    if parts.poster.name == "default_poster":
                        print("---------- デフォルトポスターだったよ ---------")
                        # 会社のディスク使用量からデフォルトのポスターのサイズを引く
                        this_resource_manage.total_file_size -= settings.DEFAULT_POSTER
                        this_resource_manage.save()

                    else:
                        print("---------- デフォルトポスター以外だったよ ---------")
                        # 会社のディスク使用量からポスターのサイズを引く
                        this_resource_manage.total_file_size -= int(parts.poster.size)
                        this_resource_manage.save()

                        if another_poster_count > 1:
                            print("---------- 他にポスターが紐づいてるパーツがあったよ ---------")
                        else:
                            # パーツに紐づくポスターを削除
                            parts.poster.delete()

                if parts.type == 3:
                    print("---------- テストパーツです ---------")

                    # テストパーツに紐づくテストの設問を取得
                    questions = Question.objects.filter(parts=parts)
                    print("---------- questions ---------", questions)

                    for question in questions:
                        print("---------- question ---------", question)

                        # テストの設問に紐づく画像を取得
                        images = question.image.all()
                        print("---------- images ---------", images)

                        # 画像がある場合
                        if images:
                            for image in images:
                                print("---------- image.name ---------", image.name)
                                print("---------- image.size ---------", image.size)

                                # 会社のディスク使用量からポスターのサイズを引く
                                this_resource_manage.total_file_size -= int(image.size)
                                this_resource_manage.save()

                                # 逆参照してその画像が紐づいている他のパーツの数を取得
                                # another_image_count = Question.objects.filter(image__in=images).count()
                                another_image_count = Question.objects.filter(image=image).count()
                                print("---------- another_image_count ---------", another_image_count)

                                if another_image_count > 1:
                                    print("---------- 他に画像が紐づいてる設問があったよ ---------")
                                else:
                                    # 設問に紐づく画像を削除
                                    image.delete()

                if parts.type == 4:
                    print("---------- アンケートパーツです ---------")

                    # テストパーツに紐づくテストの設問を取得
                    questionnaire_questions = QuestionnaireQuestion.objects.filter(parts=parts)
                    print("---------- questionnaire_questions ---------", questionnaire_questions)

                    for questionnaire_question in questionnaire_questions:
                        print("---------- questionnaire_question ---------", questionnaire_question)

                        # テストの設問に紐づく画像を取得
                        images = questionnaire_question.image.all()
                        print("---------- images ---------", images)

                        # 画像がある場合
                        if images:
                            for image in images:
                                print("---------- image.name ---------", image.name)
                                print("---------- image.size ---------", image.size)

                                # 会社のディスク使用量からポスターのサイズを引く
                                this_resource_manage.total_file_size -= int(image.size)
                                this_resource_manage.save()

                                # 逆参照してその画像が紐づいている他のパーツの数を取得
                                another_image_count = QuestionnaireQuestion.objects.filter(image=image).count()
                                print("---------- another_image_count ---------", another_image_count)

                                if another_image_count > 1:
                                    print("---------- 他に画像が紐づいてる設問があったよ ---------")
                                else:
                                    print("---------- 設問に紐づく画像を削除 ---------")
                                    # 設問に紐づく画像を削除
                                    image.delete()

                # トレーニングに紐づくパーツを削除
                parts.delete()

        # 会社に紐づくトレーニング数から削除したトレーニングの数を引く
        this_resource_manage.number_of_training -= 1

        # トレーニングの合計サイズから削除したトレーニング分を引く ※20KB(=20480B)
        this_resource_manage.number_of_file -= settings.TRAINING_SIZE

        # 会社のディスク使用量から削除したトレーニング分を引く
        this_resource_manage.total_file_size -= settings.TRAINING_SIZE

        this_resource_manage.save()

        # TrainingRelationから一致するものを削除する
        training_relations = TrainingRelation.objects.filter(training_id=training_id)
        print("---------- training_relations ---------", training_relations)

        for training_relation in training_relations:
            groups = UserCustomGroupRelation.objects.filter(group_id=training_relation.group_id)
            # print("---------- groups ---------", groups)

            for group in groups:
                # print("---------- グループのID ---------", group.group_id)
                # print("---------- グルーピングユーザー ---------", group.group_user)

                # トレーニングの表示の切り替えデータを削除
                user_raining_done_chg = TrainingDoneChg.objects.filter(subject=training.subject, user_id=group.group_user)
                # print("---------- トレーニングの表示の切り替え ---------", user_raining_done_chg)

                user_raining_done_chg.delete()


        training_relations.delete()

        # メッセージを返す
        messages.success(self.request, "トレーニングを削除しました。")

        return reverse_lazy('training:training_change_management_all')


"""
トレーニング変更

※グループが外された場合、所属ユーザーのTrainingManageは削除される
※グループが追加された場合、所属ユーザー分のTrainingManageが作成される
"""
# class TrainingUpdateView(LoginRequiredMixin, CommonView, UpdateView):
class TrainingUpdateView(LoginRequiredMixin, CommonView, FormView):
    model = Training
    template_name = 'training/training_update.html'
    form_class = TrainingUpdateForm

    # セッションにurl_nameを保存
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # セッションにurl_nameを保存
        self.request.session['_url_name'] = self.request.resolver_match.url_name

        # セッションにurl_nameを保存
        path_info = self.request.build_absolute_uri()
        print("--------------- path_info", path_info)# http://127.0.0.1:8000/training_update/0fb4075d-f51e-436b-b591-99eeb7b32126

        # URLから末尾のファイル名を抜き出す
        training_id = path_info[path_info.rfind('/') + 1:]
        # print("---------- training_id ---------", training_id)

        self.request.session['_update_training'] = training_id

        context["training"] = Training.objects.get(id=self.kwargs['pk'])

        # group_edit_check_session = ""
        # if 'group_edit_check_session' in self.request.session:
        #     group_edit_check_session = self.request.session['group_edit_check_session']
        # context["group_edit_check_session"] = group_edit_check_session

        return context

    # フォームに対してログインユーザーを渡す
    def get_form_kwargs(self):
        kwargs = super(TrainingUpdateView, self).get_form_kwargs()
        kwargs.update({'login_user': self.request.user})
        return kwargs

    # 追加
    def get_initial(self):

        # グループ編集ボタンからグループのIDを取得
        training_id = self.kwargs['pk']
        # print("-------------- training_id トレーニング編集", training_id)# 746e995c-58c3-4bc5-ba4f-4e83f0219143

        # IDと一致するグループを取得
        training = Training.objects.filter(pk=training_id).first()
        # print("-------------- training トレーニング編集", training)# テスト

        training_groups = TrainingRelation.objects.filter(training_id=training_id)
        # print("-------------- training_groups トレーニング編集", training_groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (4)>, <UserCustomGroupRelation: UserCustomGroupRelation object (5)>]>

        group_list = []
        group_lists_raw = list(training_groups.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_user_uuid in group_lists_raw:
            group_user_uuid_string = str(group_user_uuid)
            group_list.append(group_user_uuid_string)
        # print("---------- group_list ---------", group_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

        initial={
            'title' : training.title,
            'start_date' : training.start_date,
            'end_date' : training.end_date,
            'expired_training_flg' : training.expired_training_flg,
            'description' : training.description,
            'subject' : training.subject,
            'destination_group' : group_list,
            'group_edit_check_flg' : training.group_edit_check_flg,
        }
        # フロントに返す(ユーザー一覧に✔がついた状態で描画される)
        return initial

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        # print("------------------ form", form)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):

        # 変更前にトレーニングに紐づいているグループを取得(テンポラリフラグが立っているグループは除外)
        training = Training.objects.filter(pk=self.kwargs['pk']).first()

        group_user_brfore_changes = TrainingRelation.objects.filter(training_id=training.id)
        print("---------- group_brfore_changes ---------", group_user_brfore_changes)

        # リスト化
        group_brfore_change_list = []
        group_lists_raw_1 = list(group_user_brfore_changes.values_list('group_id', flat=True))
        # IDをstrに直してリストに追加
        for group_uuid_1 in group_lists_raw_1:
            group_uuid_string_1 = str(group_uuid_1)
            group_brfore_change_list.append(group_uuid_string_1)
        print("---------- group_brfore_change_list ---------", group_brfore_change_list)

        # フォームからDBオブジェクトを仮生成
        # training_update = form.save(commit=False)

        # 変更した内容を反映
        training.title = form.cleaned_data['title']
        training.start_date = form.cleaned_data['start_date']
        training.end_date = form.cleaned_data['end_date']
        training.description = form.cleaned_data['description']
        training.subject = form.cleaned_data['subject']
        training.expired_training_flg = form.cleaned_data['expired_training_flg']

        # start_dateの変更がある場合
        # if training_update.start_date is None:
        now1 = datetime.now()

        # 登録時刻との比較用
        now2 = now1.strftime("%Y-%m-%d %H:%M:%S")
        if training.start_date:
            sd = training.start_date.strftime("%Y-%m-%d %H:%M:%S")
        fifteen = now1 + timedelta(minutes=15)
        if training.start_date is None:
            print("------ training.start_date is None -------")
            # 15分後の時刻を代入する
            # now = datetime.now()
            training.start_date = fifteen.strftime("%Y-%m-%d %H:%M:%S")
        elif sd < now2:
            training.start_date = fifteen.strftime("%Y-%m-%d %H:%M:%S")
        else:
            pass
        training.save()

        # コースを変更してもTrainingManageに更新した内容が反映されなかったため追加
        training_manages = TrainingManage.objects.filter(training=training)
        # print("------ training_manages -------", training_manages)

        for training_manage in training_manages:
            training_manage.subject_manage = training.subject
            training_manage.save()


        # セッションの中にcreate_tempo_groupがあればテンポフラグの処理をする
        if 'create_tempo_group' in self.request.session:
            print("---------- create_tempo_groupあったよ ---------")

            # 変更後のグループを取得
            destination_group_qs = form.cleaned_data['destination_group']
            print("---------- destination_group_qs ---------", destination_group_qs)# <QuerySet [<CustomGroup: ミホノブルボンAbc>]>

            destination_group_list = []

            # 選択グループのidのリストを作成
            destination_group_list = list(destination_group_qs.values_list('id', flat=True))
            print("---------- destination_group_list if---------", destination_group_list)# [UUID('f500016e-b775-4d47-bbe0-2118f1b913c6')]

            # リスト内のIDをUUIDの文字列表現に変更
            destination_group_id_list = [str(o) for o in destination_group_list]
            print("---------- 文字変換1 if---------", destination_group_id_list)# ['f500016e-b775-4d47-bbe0-2118f1b913c6']

            # 既存のグループを取得
            group_qs = UserCustomGroupRelation.objects.filter(group_id__in=destination_group_list, tentative_group_flg=False)
            print("---------- 既存のグループ ---------", group_qs)# <QuerySet [<CustomGroup: メガネ☆セブンα>]>

            # 削除
            group_qs.delete()

            # 仮作成フラグが立っているグループを取得
            tentative_group_qs = UserCustomGroupRelation.objects.filter(group_id__in=destination_group_list, tentative_group_flg=True)
            print("---------- 仮作成フラグが立っているグループ ---------", tentative_group_qs)# <QuerySet [<CustomGroup: メガネ☆セブンα>]>

            for tentative_group in tentative_group_qs:
                print("---------- tempo_group ---------", tentative_group.group_id)# f500016e-b775-4d47-bbe0-2118f1b913c6

                # グループのユーザーを取得
                group_users = UserCustomGroupRelation.objects.filter(group_id=tentative_group.group_id)

                for user in group_users:
                    print("---------- user---------", user)
                    # 仮作成フラグをFalseに変更
                    user.tentative_group_flg = False
                    user.save()


            # 既存のグループを取得
            # group_qs = UserCustomGroupRelation.objects.filter(group_id__in=destination_group_list, tentative_group_flg=False)
            # print("---------- 既存のグループ ---------", group_qs)# <QuerySet [<CustomGroup: メガネ☆セブンα>]>


            # テンポラリのフラグが立っているグループを取得
            # tempo_groups = UserCustomGroupRelation.objects.filter(tentative_group_flg=True)
            # print("---------- tempo_groups ---------", tempo_groups)




            # for tempo_group in tempo_groups:

                # print("---------- tempo_group user ---------", tempo_group.group_user.all())

                # 既存のグループを取得
                # existing_groups = CustomGroup.objects.filter(name=tempo_group.name, tempo_flg=False).first()
                # print("---------- existing_groups aaa ---------", existing_groups)

                # 取得したオブジェクトのうち、テンポラリのフラグが立っているグループから立ってないグループに値を引っ越す
                # existing_groups.group_user.set(tempo_groups.group_user.all())
                # existing_groups.group_user.set(tempo_group.group_user.all())

                # 保存
                # existing_groups.save()

                # テンポラリフラグの立っているグループを削除する
                # tempo_group.delete()

            # 保存
            # training_update.save()

        # 変更後のグループを取得
        destination_group_qs = form.cleaned_data['destination_group']
        print("---------- destination_group_qs ---------", destination_group_qs)# <QuerySet [<CustomGroup: ミホノブルボンAbc>]>

        # トレーニングにグループを紐づける
        # training_update.destination_group.set(destination_group_qs)

        # 変更後のグループを取得(テンポラリフラグが立っているグループは除外)
        # after_change_training_obj = Training.objects.filter(pk=self.kwargs['pk']).first()
        # group_after_changes = after_change_training_obj.destination_group.all()
        # print("---------- group_after_changes ---------", group_after_changes)

        # リスト化
        group_after_change_list = []
        group_lists_raw = list(destination_group_qs.values_list('pk', flat=True))

        # IDをstrに直してリストに追加
        for group_uuid in group_lists_raw:
            group_uuid_string = str(group_uuid)
            group_after_change_list.append(group_uuid_string)
        print("---------- group_user_after_change_list ---------", group_after_change_list)

        # 変更前と変更後のグループのグループの差分から削除したグループを算出
        delete_group_set = set(group_brfore_change_list).difference(set(group_after_change_list))
        print("---------- 削除したグループ ---------", delete_group_set)# {UUID('51ee2051-ebc9-46b2-82fe-3e9f2eabf439')}

        # トレーニングに追加したグループを算出
        add_group_set = set(group_after_change_list).difference(set(group_brfore_change_list))
        print("---------- 追加したグループ ---------", add_group_set)

        # 追加したグループがあった場合
        if add_group_set:
            print("---------- 追加したグループがあったよ ---------")

            # 追加したグループの差分をset型からリスト型に直す
            add_group_list = list(add_group_set)
            print("---------- add_group_list ---------", add_group_list)# ['88196b65-a8f7-4c9a-ba35-ed8c69a51cbb']

            # add_groups = CustomGroup.objects.filter(pk__in=add_group_list)
            add_groups = UserCustomGroupRelation.objects.filter(group_id__in=add_group_list)
            print("---------- add_groups ---------", add_groups)#  <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (159)>, <UserCustomGroupRelation: UserCustomGroupRelation object (160)>]>

            # グループのユーザーを取得
            for destination_group in add_groups:
                print("---------- destination_group.group_user ---------", destination_group.group_user)
                print("---------- destination_group.group_id ---------", destination_group.group_id)

                # トレーニングとグループの中間テーブルがない場合はレコードを作成
                if not TrainingRelation.objects.filter(group_id=destination_group.group_id, training_id=training.id):
                    print("---------- TrainingRelationがないよ ---------")
                    training_destination_group_group_relation, created = TrainingRelation.objects.get_or_create(
                        group_id = destination_group.group_id,
                        training_id = training.id,
                    )
                    training_destination_group_group_relation.save()

                # users = destination_group.group_user.all()# エラー　all()は使えない
                # print("---------- users ---------", users)

                if not TrainingManage.objects.filter(user=destination_group.group_user, training=training):
                    print("---------- TrainingManageがないよ ---------")
                    # 新しく追加したグループのユーザー分のTrainingManagesを作成する
                    training_manage, created = TrainingManage.objects.get_or_create(
                        training = training,
                        user = destination_group.group_user,
                        status = 1, # 未対応
                        subject_manage = training.subject
                    )
                    training_manage.save()

                # 追加したユーザーの対応履歴が存在しない場合
                if not TrainingHistory.objects.filter(user=destination_group.group_user, training=training):
                    print("---------- TrainingHistoryがないよ ---------")
                    # 対応履歴を作成する
                    training_history, created = TrainingHistory.objects.get_or_create(
                        training = training,
                        reg_user = training.reg_user,
                        user = training_manage.user,
                        status = 1
                    )
                    training_history.save()


                    # createdがTrueの場合
                    # if created:
                    #     # 未対応で作成する
                    #     training_manage.status = 1
                    # else:
                    #     # 対応中/完了のステータスのままで残す
                    #     print("---------- 何もしない ---------")

                # ユーザーのTrainingManageを保存する
                # training_manage.save()

                # 追加するグループとトレーニングのTrainingRelationを作成
                training_destination_group_group_relation, created = TrainingRelation.objects.get_or_create(
                    group_id = destination_group.group_id,
                    training_id = training.id,
                )
                training_destination_group_group_relation.save()


        if delete_group_set:
            print("---------- 削除したグループがあったよ ---------")

            # 削除したグループの差分をset型からリスト型に直す
            delete_group_list = list(delete_group_set)
            print("---------- delete_group_list ---------", delete_group_list)# ['88196b65-a8f7-4c9a-ba35-ed8c69a51cbb']

            # UserCustomGroupRelationから削除するグループと一致するグループを取得
            del_groups = UserCustomGroupRelation.objects.filter(group_id__in=delete_group_list)
            print("---------- del_groups ---------", del_groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (179)>, <UserCustomGroupRelation: UserCustomGroupRelation object (180)>]>

            # 削除するグループのユーザーをリスト化
            delete_user_list = []
            del_user_group_lists_raw = list(del_groups.values_list('group_user', flat=True))
            for del_user_group_uuid in del_user_group_lists_raw:
                del_user_group_uuid_string = str(del_user_group_uuid)
                delete_user_list.append(del_user_group_uuid_string)
            print("---------- delete_user_list ---------", delete_user_list)# ['f399cea5-41f3-4120-ad57-6975a13f7b0c', 'e73d908b-0799-4cd5-93b3-3b08a8b233c1']

            # 削除しないグループに所属するユーザーのリスト(=複数のグループがトレーニングに紐づいている状態)
            not_del_groups = TrainingRelation.objects.filter(training_id=training.id).exclude(group_id__in=delete_group_list)
            print("---------- not_del_groups ---------", not_del_groups)# <QuerySet [<TrainingRelation: TrainingRelation object (115)>, <TrainingRelation: TrainingRelation object (116)>]>

            # 削除しないグループに所属しているユーザーを取得
            not_del_users_list = []
            for destination_group in not_del_groups:
                not_del_users = UserCustomGroupRelation.objects.filter(group_id=destination_group.group_id)
                print("---------- not_del_users ---------", not_del_users)#  <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (152)>, <UserCustomGroupRelation: UserCustomGroupRelation object (174)>]>

                for not_del_user in not_del_users:
                    not_del_users_list.append(not_del_user.group_user)
                print("---------- not_del_users_list ---------", not_del_users_list)# [<QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (151)>, <UserCustomGroupRelation: UserCustomGroupRelation object (158)>]>, <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (152)>, <UserCustomGroupRelation: UserCustomGroupRelation object (174)>]>]

            # 重複ユーザーがいる場合
            if set(delete_user_list) & set(not_del_users_list):
                print("---------- 重複ユーザーがいます ---------")

                # 重複しているユーザーのリストを作成
                repetitive_user = set(delete_user_list) & set(not_del_users_list)
                repetitive_user_list = list(repetitive_user)
                print("---------- repetitive_user_list ---------", repetitive_user_list)

                # 重複ユーザーを除いたユーザーと一致するTrainingManageを取得
                user_training_manages_qs = TrainingManage.objects.filter(user__in=delete_user_list, training=training.id).exclude(user__in=repetitive_user_list)
                print("--------------- 一致するユーザーのTrainingManageを取得(削除) --------------", user_training_manages_qs)

                # TrainingManageを削除
                user_training_manages_qs.delete()

            else:
                print("---------- 重複ユーザーはいません ---------")

                user_training_manages_qs = TrainingManage.objects.filter(user__in=delete_user_list, training=training.id)
                print("--------------- 一致するユーザーのTrainingManageを取得(削除) --------------", user_training_manages_qs)

                user_training_manages_qs.delete()

            # TrainingRelationから削除するグループと一致するものを削除
            training_relation_qs = TrainingRelation.objects.filter(group_id__in=delete_group_list, training_id=training.id)
            print("--------------- training_relation_qs --------------", training_relation_qs)

            training_relation_qs.delete()

        # 保存
        # training_update.save()

        # セッションの中にdeletion_user_id_jsonがれば取り出す(=CustomGroupUpdateViewでメンバーを削除)
        if 'deletion_user_id_json' in self.request.session:
            print("--------------- セッションあったよ(削除) --------------")

            # 削除対象のユーザーのIDをセッションから取得
            deletion_user_id_json = self.request.session['deletion_user_id_json'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "")

            # リスト化する
            deletion_user_id_list = deletion_user_id_json.split(',')
            print("--------------- リスト化する(削除) --------------", deletion_user_id_list)# ['2b0a5711-0bb3-44b6-b424-73f714e1a9f2']

            # 変更があったトレーニングに紐づくグループを取得
            training_relation = TrainingRelation.objects.filter(training_id=training.id)
            print("--------------- training_relation", training_relation)

            group_list = []
            group_lists_raw = list(training_relation.values_list('group_id', flat=True))
            # IDをstrに直してリストに追加
            for group_uuid in group_lists_raw:
                group_uuid_string = str(group_uuid)
                group_list.append(group_uuid_string)
            print("---------- group_list ---------", group_list)# ['f399cea5-41f3-4120-ad57-6975a13f7b0c', 'e73d908b-0799-4cd5-93b3-3b08a8b233c1']

            # 取得したグループが紐づいているトレーニングを取得(追加)
            training_relations = TrainingRelation.objects.filter(group_id__in=group_list)
            print("---------- training_relations ---------", training_relations)

            training_id_list = []# (追加)
            training_id_lists_raw = list(training_relations.values_list('training_id', flat=True))
            for training_uuid in training_id_lists_raw:
                training_uuid_string = str(training_uuid)
                training_id_list.append(training_uuid_string)
            print("---------- training_id_list ---------", training_id_list)

            # IDと一致するトレーニングをTrainingテーブルから取得する(追加)
            training_qs = Training.objects.filter(id__in=training_id_list)
            print("---------- training_qs ---------", training_qs)# <QuerySet [<Training: トレーニングA>, <Training: トレーニングC>]>

            for training in training_qs: # (追加)
                print("---------- training ---------", training)

                # トレーニングに紐づくグループを取得
                groups = TrainingRelation.objects.filter(training_id=training.id)
                print("---------- groups ---------", groups)# TrainingRelation object (85)

                # グループのIDをstrに直してリストに追加
                group_list = []
                group_lists_raw = list(groups.values_list('group_id', flat=True))
                for group_uuid in group_lists_raw:
                    group_uuid_string = str(group_uuid)
                    group_list.append(group_uuid_string)
                print("---------- group_list ---------", group_list)# ['b376583f-6687-4db0-b2b3-f59d51885e1d']

                # グループに所属しているユーザーを取り出す
                user_custom_groups = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
                print("---------- user_custom_groups ---------", user_custom_groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (152)>, <UserCustomGroupRelation: UserCustomGroupRelation object (192)>, <UserCustomGroupRelation: UserCustomGroupRelation object (200)>]>

                # IDをstrに直してリストに追加
                group_user_list = []
                group_user_lists_raw = list(user_custom_groups.values_list('group_user', flat=True))
                for ggroup_user_uuid in group_user_lists_raw:
                    group_user_uuid_string = str(ggroup_user_uuid)
                    group_user_list.append(group_user_uuid_string)
                print("---------- group_user_list ---------", group_user_list)# ['76d54969-96ad-4485-ac02-e38612d5c070', '6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '9a058d25-384d-43e1-9a26-c1a680c87ab4']

                # set()で重複しているユーザーをリストから除外する
                user_id_list = list(set(group_user_list))


                # 重複しているユーザーが存在する場合
                if set(deletion_user_id_list) & set(user_id_list):
                    # 重複しているユーザーのTrainingManageは消さない
                    print("--------------- 重複しているユーザーが存在する")

                    repetitive_user = set(deletion_user_id_list) & set(user_id_list)
                    repetitive_user_list = list(repetitive_user)
                    print("---------- repetitive_user_list", repetitive_user_list)

                    # 重複するユーザーを除いた削除対象のユーザーと一致するユーザーのTrainingManageを取得
                    user_training_manages_qs = TrainingManage.objects.filter(user__in=deletion_user_id_list, training=training.id).exclude(user__in=repetitive_user_list)
                    print("--------------- 重複するユーザーを除いた削除対象のユーザーと一致するユーザーのTrainingManageを取得(削除) if --------------", user_training_manages_qs)

                else:
                    print("--------------- 重複しているユーザーが存在しない")

                    # 削除対象のユーザーと一致するTrainingManageを取得
                    user_training_manages_qs = TrainingManage.objects.filter(user__in=deletion_user_id_list, training=training.id)
                    print("--------------- 削除対象のユーザーと一致するTrainingManageを取得(削除) else --------------", user_training_manages_qs)

                # ユーザーのTrainingManageを削除する
                user_training_manages_qs.delete()

            # セッションデータを削除する
            del self.request.session['deletion_user_id_json']







        # セッションの中にadd_user_id_jsonがれば取り出す(=CustomGroupUpdateViewでメンバーを追加)
        if 'add_user_id_json' in self.request.session:

            print("--------------- セッションあったよ(追加) --------------")

            # ユーザー情報をセッションから取得
            add_user_id_json = self.request.session['add_user_id_json'].replace(" ", "").replace('"', "").replace("[", "").replace("]", "")
            print("--------------- リスト化する(追加) --------------", add_user_id_json)

            # リスト化する
            add_user_id_list = add_user_id_json.split(',')

            # グループを取得
            destination_group_qs = form.cleaned_data['destination_group']
            print("---------- destination_group_qs ---------", destination_group_qs)# <QuerySet [<CustomGroup: メガネ☆セブンα>]>

            destination_group_list = []
            group_lists_raw = list(destination_group_qs.values_list('pk', flat=True))
            # IDをstrに直してリストに追加
            for group_uuid in group_lists_raw:
                group_uuid_string = str(group_uuid)
                destination_group_list.append(group_uuid_string)

            # グループに紐づいているトレーニングを取得
            # trainings = Training.objects.filter(destination_group__in=destination_group_list)
            training_relations = TrainingRelation.objects.filter(group_id__in=destination_group_list)
            print("---------- グループに紐づいているトレーニングを取得 ---------", training_relations)# <QuerySet [<Training: ステータス確認用テスト>, <Training: 令和2年度 新任主査級研修>, <Training: テスト112>]>

            for add_user in add_user_id_list:

                user = User.objects.filter(pk=add_user).first()
                print("--------------- user(追加) --------------", user)

                for training_relation in training_relations:
                    print("--------------- training_relation --------------", training_relation)# TrainingRelation object (17)
                    print("--------------- training_relation --------------", training_relation.training_id)# 1ca93e62-e27b-42a1-b68b-7613ff4eaa21

                    training_obj = Training.objects.filter(id=training_relation.training_id).first()
                    print("--------------- training_obj --------------", training_obj)# <QuerySet [<Training: トレーニング1>]>

                    # 新しくグループに追加されたユーザー分のTrainingManagesを作成する
                    if not TrainingManage.objects.filter(user=user, training=training_obj):
                        print("--------------- training_relationがなかった --------------")
                        training_manage, created = TrainingManage.objects.get_or_create(
                            training = training_obj,
                            user = user.id,
                            status = 1, # 未対応
                            subject_manage = training_obj.subject
                        )
                        training_manage.save()


                    # 追加したユーザーの対応履歴が存在しない場合
                    if not TrainingHistory.objects.filter(user=user, training=training_obj):
                        print("--------------- training_historyがなかった --------------")
                        # 対応履歴を作成する
                        training_history, created = TrainingHistory.objects.get_or_create(
                            training = training_obj,
                            reg_user = training_obj.reg_user,
                            user = training_manage.user,
                            status = 1
                        )
                        training_history.save()


                    # createdがTrueの場合
                    # if created:
                    #     # 未対応で作成する
                    #     training_manage.status = 1
                    #     # training_history.status = 1
                    # else:
                    #     # 対応中/完了のステータスのままで残す
                    #     print("---------- 何もしない ---------")

                    # ユーザーのTrainingManageを保存する
                    # training_manage.save()

            # セッションデータを削除する
            del self.request.session['add_user_id_json']

        # セッションデータがあるか判定
        if 'create_tempo_group' in self.request.session:
            # セッションデータを削除する
            del self.request.session['create_tempo_group']
        else:
            print("---------- セッションデータがないよ create_tempo_group ---------")

        # メッセージを返す
        messages.success(self.request, "トレーニングを編集しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': self.kwargs['pk']}))


"""
グループの変更を行った場合、トレーニング変更画面に値を渡す
"""
class GroupEditCheckAjaxView(APIView):

    def get(self, request, *args, **kwargs):
        print("----------------GroupEditCheckAjaxView")

        # URLパラメータから送られたきたIDを取得
        training_id = self.kwargs['pk']

        # idと一致するObjectを取得
        training_obj = Training.objects.filter(pk=training_id).first()
        print("----------------training_obj", training_obj)
        print("----------------group_edit_check_flg", training_obj.group_edit_check_flg)

        # group_edit_check_flgの状態を変数に格納
        group_edit_check_flg = training_obj.group_edit_check_flg

        # テンプレートにdataで渡す
        return JsonResponse({'data': group_edit_check_flg,
        })


"""
ボタン有効化制御、制御条件の変更(表示)
"""
class ButtonActivateCtlView(LoginRequiredMixin, CommonView, ListView):
    model = Training
    template_name = 'training/button_activate_ctl.html'

    # テンプレートにモデルのデータを渡す
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        # URLパラメータから送られたきた相性IDを取得
        training_id = self.kwargs['pk']

        trainings = Training.objects.filter(pk = training_id) \
        .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

        context["trainings"] = trainings

        # トレーニングに紐づいているパーツを取得
        training_obj = Training.objects.filter(pk=training_id).first()
        parts_selects = training_obj.parts.all()

        context["parts_selects"] = parts_selects

        for key in list(self.request.session.keys()):
            if not key.startswith("_"):
                del self.request.session[key]

        return context


# """
# ボタン有効化制御、制御条件の変更(表示) 追加
# """
# class ButtonActivateCtlEditView(LoginRequiredMixin, CommonView, ListView):
#     model = Training
#     template_name = 'training/button_activate_ctl_edit.html'

#     # テンプレートにモデルのデータを渡す
#     def get_context_data(self, **kwargs):

#         context = super().get_context_data(**kwargs)

#         # URLパラメータから送られたきた相性IDを取得
#         training_id = self.kwargs['pk']

#         trainings = Training.objects.filter(pk = training_id) \
#         .prefetch_related(Prefetch("parts", queryset=Parts.objects.all().order_by('order')))

#         context["trainings"] = trainings

#         # トレーニングに紐づいているパーツを取得
#         training_obj = Training.objects.filter(pk=training_id).first()
#         parts_selects = training_obj.parts.all()

#         context["parts_selects"] = parts_selects

#         for key in list(self.request.session.keys()):
#             if not key.startswith("_"):
#                 del self.request.session[key]

#         return context

"""
ボタン有効化制御、制御条件画面に
登録されている値を渡す
"""
class ButtonActivateCtlEditAjaxView(APIView):

    def get(self, request, *args, **kwargs):

        # URLパラメータから送られたきたIDを取得
        training_id = self.kwargs['pk']

        # maintenance_idと一致するObjectを取得
        training_obj = Training.objects.filter(pk=training_id).first()

        # トレーニングに紐づいているパーツを取得
        parts = training_obj.parts.all()

        parts_active_ctl_dict = {}

        for parts in parts:

            print("------------- parts", parts)

            # パーツのIDと一致するControlConditionsを取得 koko
            parts_origin_objs = ControlConditions.objects.filter(parts_origin=parts.id)
            print("------------- parts_origin_objs", parts_origin_objs)

            if parts_origin_objs:

                for parts_origin_obj in parts_origin_objs:

                    print("------------- 依存元2", parts_origin_obj.parts_destination)

                    # 辞書に依存先と依存元を追加
                    parts_active_ctl_dict[str(parts_origin_obj.parts_destination.id)] = str(parts_origin_obj.parts_origin.id)

            # print("------------- parts_active_ctl_dict", parts_active_ctl_dict)

        # テンプレートにdataで辞書を渡す
        return JsonResponse({'data': parts_active_ctl_dict,
                    })



"""
ボタン有効化制御の変更(登録, Ajax)
"""
class ButtonActivateCtlUpdateView(View):

    def post(self, request, *args, **kwargs):

        try:
            print("----------------ButtonActivateCtlUpdateView")

            # チェックされたチェックボックスのIDを取得
            checks = request.POST.getlist('checks[]')
            print("----------------checks", checks)# c1ba98dc-b059-4ee4-bbad-41fc3b663960

            # チェックされていないチェックボックスのIDを取得
            unchecks = request.POST.getlist('unchecks[]')
            print("----------------unchecks", unchecks)

            # unchecksがある場合はボタン有効化制御を削除する
            if unchecks:

                parts_obj = Parts.objects.filter(pk__in=unchecks).first()
                print("----------------parts_obj", parts_obj)

                training =  Training.objects.filter(parts=parts_obj).first()
                print("----------------training", training)

                # トレーニングに紐づいているパーツを取得
                parts = training.parts.all()

                for parts in parts:
                    # parts_origin_objs = ControlConditions.objects.filter(parts_origin=parts.id)
                    parts_origin_objs = ControlConditions.objects.filter(parts_destination__in=unchecks)
                    print("----------------parts_origin_objs", parts_origin_objs)

                    # すでに依存元がDBに登録されている場合
                    if parts_origin_objs:
                        print("------------- DBに依存元があったよ unchecks")

                        for parts_origin_obj in parts_origin_objs:
                            print("------------- parts_origin_obj", parts_origin_obj)# ControlConditions object (17)
                            # 該当するものを削除する
                            parts_origin_obj.delete()

                    # btn_activate_ctlをFalseにする
                    parts.btn_activate_ctl = False

                    parts.save()

            # checksがある場合はボタン有効化制御を作成する
            if checks:

                parts_obj = Parts.objects.filter(pk__in=checks).first()
                print("----------------parts_obj", parts_obj)# テストA

                # trainingを取得
                training =  Training.objects.filter(parts=parts_obj).first()
                print("----------------training", training)# 彩の国埼玉

                # トレーニングに紐づいているパーツを取得
                parts = training.parts.all()

                for parts in parts:
                    parts_origin_objs = ControlConditions.objects.filter(parts_origin=parts.id)
                    print("----------------parts_origin_objs", parts_origin_objs)# None

                    # すでに依存元がDBに登録されている場合
                    if parts_origin_objs:
                        print("------------- DBに依存元があったよ cheks")

                        for parts_origin_obj in parts_origin_objs:
                            print("------------- parts_origin_obj", parts_origin_obj)# ControlConditions object (17)
                            # 該当するものを削除する
                            parts_origin_obj.delete()

                # ✔した配列のIDに一致するクエリセットを取得
                parts_objs = Parts.objects.filter(pk__in=checks)

                for parts_obj in parts_objs:

                    # btn_activate_ctlをTrueにする
                    parts_obj.btn_activate_ctl = True

                    parts_obj.save()

                # フロントから送られてきた依存元・先の値を取得
                qdict = request.POST.copy()
                print("----------------qdict", qdict)

                # QueryDictを辞書に変換
                d = dict(qdict)

                # 辞書の中からunchecks[]を取得
                if d.get("unchecks[]"):

                    # 指定したキーの要素を辞書から削除する
                    qdict.pop("unchecks[]")

                for key, value in qdict.lists():

                    # array[0][],array[1][]の場合
                    if not key == "checks[]":

                        print("----------------value 0", d[key][0])# 0 49e32a8c-86d5-4098-a44a-2d94ac2e2265
                        print("----------------value 1", d[key][1])# 1
                        print("----------------key", key)# array[0][]
                        print("----------------list", qdict.lists())# <dict_itemiterator object at 0x0000024E4D0A8908>

                        # 依存元
                        parts_origin = d[key][1]
                        print("----------------2", parts_origin)# 49e32a8c-86d5-4098-a44a-2d94ac2e2265

                        # 依存先
                        parts_destination_1 = d[key][0]
                        print("----------------3", parts_destination_1)# c1ba98dc-b059-4ee4-bbad-41fc3b663960

                        # 値が空のときはスキップ
                        if parts_origin:
                            print("----- parts_origin if ------")
                            # 1つ目の依存先が選択されていない場合
                            if len(parts_destination_1) <= 32:
                                # 何もしない
                                print("----- 32文字以下 1 ------")

                            else:
                                # 作成
                                obj = ControlConditions.objects.create(
                                    parts_origin = Parts.objects.filter(id=parts_origin).first(),
                                    parts_destination = Parts.objects.filter(id=parts_destination_1).first(),
                                )

                                obj.save()


                    # 2つ目の依存先が選択されていない場合
                    # if len(parts_destination_2) <= 32:
                    #     # 何もしない
                    #     print("----- 32文字以下 2 ------")
                    # else:

                    #     obj_2 = ControlConditions.objects.create(

                    #         parts_origin = Parts.objects.get(id=parts_origin),

                    #         parts_destination = Parts.objects.filter(id=parts_destination_2).first(),
                    #     )

                    #     obj_2.save()

            message = f'ボタン有効化制御・制御条件を変更しました。'
            messages.success(self.request, message)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "登録を変更しました",
                                "training_id": training.id,
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る

            data = {}
            data['status'] = 'ng'
            data['message'] = '登録の変更に失敗しました'
            return JsonResponse(data)





"""
制御条件の変更(表示) ※使ってない
"""
class ControlConditionsUpdateView(View):

    def post(self, request, *args, **kwargs):

        try:

            print("----------------ControlConditionsUpdateView")

            qdict = request.POST

            for key, value in qdict.lists():

                parts_origin = value[0]

                parts_destination_1 = value[1]
                parts_destination_2 = value[2]

                lists = [parts_destination_1, parts_destination_2]

                # 1つ目の依存先が選択されていない場合
                if len(parts_destination_1) <= 32:
                    # 何もしない
                    print("----- 32文字以下 1 ------")
                else:

                    obj = ControlConditions.objects.create(

                        parts_origin = Parts.objects.get(id=parts_origin),

                        parts_destination = Parts.objects.filter(id=parts_destination_1).first(),

                    )

                    obj.save()

                # 2つ目の依存先が選択されていない場合
                if len(parts_destination_2) <= 32:
                    # 何もしない
                    print("----- 32文字以下 2 ------")
                else:

                    obj_2 = ControlConditions.objects.create(

                        parts_origin = Parts.objects.get(id=parts_origin),

                        parts_destination = Parts.objects.filter(id=parts_destination_2).first(),
                    )

                    obj_2.save()

            message = f'ボタン有効化制御・制御条件を変更しました。'
            messages.success(self.request, message)


            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "制御条件を変更しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = '制御条件の変更に失敗しました'
            return JsonResponse(data)






"""
パーツの削除
"""
class PartsDeleteView(DeleteView):
    model = Parts
    template_name = 'training/training_edit_menu.html'

    def get_success_url(self):
        print("---------- パーツの削除 ---------")

        parts_id = self.kwargs['pk']
        # print("---------- parts_id ---------", parts_id)

        training = Training.objects.filter(parts=parts_id).first()

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        # print("---------- this_resource_manage ---------", this_resource_manage)

        # トレーニングに紐づいているパーツを取得
        parts = training.parts.all()
        # print("---------- all_parts ---------", parts)

        # パーツの数を取得
        parts_count = training.parts.all().count()

        for parts in parts:
            # 依存元を取得
            parts_origin_objs = ControlConditions.objects.filter(parts_destination=parts.id)
            # print("------------- parts_origin_objs 1", parts_origin_objs)

            # 該当するものを削除する
            parts_origin_objs.delete()

            # btn_activate_ctlをFalseにする
            parts.btn_activate_ctl = False
            parts.save()

        # 削除対象のパーツを取得
        del_parts = Parts.objects.filter(id=parts_id).first()
        print("------------- del_parts", del_parts)

        if del_parts.type == 1:
            print("------------- ファイルパーツです")

            # 逆参照してそのファイルが紐づいている他のパーツの数を取得
            another_parts = Parts.objects.filter(file__in=del_parts.file.all())
            print("---------- another_parts ---------", another_parts)

            # files = parts.file.all()
            files = del_parts.file.all()
            print("------------- files", files)

            for file in files:
                print("---------- file ---------", file)# 変更前.PNG
                print("---------- file.size ---------", file.size)# 171330

                # 会社のディスク使用量からファイルのサイズを引く
                this_resource_manage.total_file_size -= int(file.size)
                this_resource_manage.save()

                another_parts_count = Parts.objects.filter(file=file).count()
                print("---------- another_parts_count ---------", another_parts_count)

                if another_parts_count > 1:
                    print("---------- 他にファイルが紐づいてるパーツがあったよ ---------")
                else:
                    print("---------- パーツに紐づくファイルを削除 ---------")
                    # パーツに紐づくファイルを削除
                    file.delete()

        elif del_parts.type == 2:
            print("------------- 動画パーツです")

            # 逆参照してその動画が紐づいている他のパーツの数を取得
            another_movie_count = Parts.objects.filter(movie=del_parts.movie).count()
            print("---------- another_movie_count ---------", another_movie_count)

            # 逆参照してそのポスターが紐づいている他のパーツの数を取得
            another_poster_count = Parts.objects.filter(poster=del_parts.poster).count()
            print("---------- another_poster_count ---------", another_poster_count)

            movie = del_parts.movie.movie
            print("------------- movie", movie)# uploads/movie/test_c09Gazc.mp4
            print("------------- movie.size", movie.size)

            poster = del_parts.poster.poster
            print("------------- poster", poster)
            print("------------- poster.size", poster.size)

            # 会社のディスク使用量から動画とポスターのサイズを引く
            this_resource_manage.total_file_size -= int(movie.size)

            if another_movie_count > 1:
                print("---------- 他に動画が紐づいてるパーツがあったよ ---------")
            else:
                print("---------- パーツに紐づく動画を削除 ---------")
                # 動画を削除
                del_parts.movie.delete()

            # デフォルトのポスターの場合
            # if poster == "uploads/poster/default_poster.JPG":
            if del_parts.poster.name == "default_poster":
                print("---------- デフォルトポスターだったよ ---------")
                this_resource_manage.total_file_size -= settings.DEFAULT_POSTER
            else:
                this_resource_manage.total_file_size -= int(del_parts.poster.size)

                if another_poster_count > 1:
                    print("---------- 他にポスターが紐づいてるパーツがあったよ ---------")
                else:
                    # ポスターを削除
                    del_parts.poster.delete()

            this_resource_manage.save()

        elif del_parts.type == 3:
            print("------------- テストパーツです")

            questions = Question.objects.filter(parts=del_parts)
            print("---------- questions ---------", questions)

            for question in questions:
                images = question.image.all()
                print("------------- images", images)

                # 画像がある場合
                if images:
                    for image in images:
                        print("---------- image ---------", image)# 変更前.PNG
                        print("---------- image.size ---------", image.size)# 171330

                        # 会社のディスク使用量からファイルのサイズを引く
                        this_resource_manage.total_file_size -= int(image.size)
                        this_resource_manage.save()

                        # 逆参照してその画像が紐づいている他のパーツの数を取得
                        another_image_count = Question.objects.filter(image=image).count()
                        print("---------- another_image_count ---------", another_image_count)

                        if another_image_count > 1:
                            print("---------- 他に画像が紐づいてる設問があったよ ---------")
                        else:
                            print("---------- 設問に紐づく画像を削除 ---------")
                            # 設問に紐づく画像を削除
                            image.delete()

        elif del_parts.type == 4:
            print("------------- アンケートパーツです")

            questionnaires = QuestionnaireQuestion.objects.filter(parts=del_parts)
            print("---------- questionnaires ---------", questionnaires)

            for questionnaire in questionnaires:
                images = questionnaire.image.all()
                print("------------- images", images)

                # 画像がある場合
                if images:
                    for image in images:
                        print("---------- image ---------", image)# 変更前.PNG
                        print("---------- image.size ---------", image.size)# 171330

                        # 会社のディスク使用量からファイルのサイズを引く
                        this_resource_manage.total_file_size -= int(image.size)
                        this_resource_manage.save()

                        # 逆参照してその画像が紐づいている他のパーツの数を取得
                        another_image_count = QuestionnaireQuestion.objects.filter(image=image).count()
                        print("---------- another_image_count ---------", another_image_count)

                        if another_image_count > 1:
                            print("---------- 他に画像が紐づいてる設問があったよ ---------")
                        else:
                            print("---------- 設問に紐づく画像を削除 ---------")
                            # 設問に紐づく画像を削除
                            image.delete()

        # トレーニングに紐づいているパーツから削除した分のパーツの数を引く
        parts_after_del = parts_count - 1

        if parts_after_del >= 2:
            # パーツの削除が済んだことがわかるようにセッションを持たせる
            self.request.session['parts_delete_done'] = 'parts_delete_done'

        # # パーツの削除が済んだことがわかるようにセッションを持たせる
        # self.request.session['parts_delete_done'] = 'parts_delete_done'

        # メッセージを返す
        messages.success(self.request, "パーツを削除しました。")

        return reverse_lazy('training:training_edit_menu', kwargs={'pk': training.id})


"""
カスタムグループの削除(個別)
※リストを比較して重複するユーザーのTrainingManageは削除しない
"""
class CustomgroupDeleteView(DeleteView):
    model = CustomGroup
    template_name = 'training/customgroup_management.html'

    def get_success_url(self):

        # 削除対象のグループのIDを取得
        group_id = self.object.pk

        # 一致するグループを取得
        del_group = CustomGroup.objects.filter(pk=group_id).first()
        print("---------- del_group ---------", del_group)# チームA
        print("---------- del_group pk ---------", del_group.pk)# 89808f62-9161-4821-af92-9c22f1ffbe25

        # del_users = del_group.group_user.all()
        del_users = UserCustomGroupRelation.objects.filter(group_id=del_group.id)
        print("---------- del_users ---------", del_users)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (24)>, <UserCustomGroupRelation: UserCustomGroupRelation object (25)>]>

        # 削除するグループに所属しているユーザーのリストを作成
        delete_user_list = []

        # delete_user_list = list(del_users)
        delete_user_list_raw = list(del_users.values_list('group_user', flat=True))
        print("---------- delete_user_list ---------", delete_user_list_raw)#  [<UserCustomGroupRelation: UserCustomGroupRelation object (24)>, <UserCustomGroupRelation: UserCustomGroupRelation object (25)>]

        # IDをstrに直してリストに追加
        for group_user_uuid in delete_user_list_raw:
            group_user_uuid_string = str(group_user_uuid)
            delete_user_list.append(group_user_uuid_string)

        # 削除しないグループに所属するユーザーのリスト
        not_del_users_list = []

        # グループが紐づいているトレーニングの情報を取得
        trainings = TrainingRelation.objects.filter(group_id=del_group.pk)
        print("---------- グループに紐づいているトレーニングを取得 ---------", trainings)# <QuerySet [<TrainingRelation: TrainingRelation object (177)>]>

        if trainings:
            # トレーニングをリスト化
            training_list = []
            delete_training_list_raw = list(trainings.values_list('training_id', flat=True))
            print("---------- delete_training_list_raw ---------", delete_training_list_raw)# [UUID('66796700-1f36-4ad5-9fcf-1d216954049d'), UUID('f3986e94-53f4-4258-afb6-91b170d92698')]

            # IDをstrに直してリストに追加
            for training_uuid in delete_training_list_raw:
                training_uuid_string = str(training_uuid)
                training_list.append(training_uuid_string)
            print("---------- training_list ---------", training_list)# ['66796700-1f36-4ad5-9fcf-1d216954049d', 'f3986e94-53f4-4258-afb6-91b170d92698']

            # トレーニングに紐づいている削除対象のグループを除いたグループを取得する
            not_del_groups = TrainingRelation.objects.filter(training_id__in=training_list).exclude(group_id=group_id)
            print("---------- not_del_groups ---------", not_del_groups)# <QuerySet []>

            # グループに所属しているユーザーを取得
            for not_del_group in not_del_groups:

                users = UserCustomGroupRelation.objects.filter(group_id=not_del_group.group_id)
                print("---------- グループに所属しているユーザーを取得 ---------", users)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (24)>, <UserCustomGroupRelation: UserCustomGroupRelation object (25)>]>

                # 削除しないグループのユーザーをforで回して取り出す
                for not_del_users in users:
                    print("---------- not_del_users ---------", not_del_users)# UserCustomGroupRelation object (47)
                    # リストにユーザーを追加
                    not_del_users_list.append(not_del_users.group_user)
                    print("---------- not_del_users_list ---------", not_del_users_list)#  [<UserCustomGroupRelation: UserCustomGroupRelation object (47)>, <UserCustomGroupRelation: UserCustomGroupRelation object (48)>]

            # リストの中に共通するユーザーがいる場合
            if set(delete_user_list) & set(not_del_users_list):
                print("---------- 重複ユーザーがいます ---------")

                # 重複しているユーザーのリストを作成
                repetitive_user = set(delete_user_list) & set(not_del_users_list)
                repetitive_user_list = list(repetitive_user)
                print("---------- repetitive_user_list ---------", repetitive_user_list)# ['9a058d25-384d-43e1-9a26-c1a680c87ab4']

                # 重複ユーザーを除いたユーザーと一致するTrainingManageを取得
                user_training_manages_qs = TrainingManage.objects.filter(user__in=delete_user_list, training__in=training_list).exclude(user__in=repetitive_user_list)
                print("--------------- 重複ユーザーを除いた一致するユーザーのTrainingManageを取得(削除) --------------", user_training_manages_qs)

                # 重複ユーザーを除いたユーザーと一致するトグルボタンの展開データを取得
                user_folder_is_open_qs = FolderIsOpen.objects.filter(user_id__in=delete_user_list, training__in=training_list).exclude(user_id__in=repetitive_user_list)
                print("---------- user_folder_is_open_qs ---------", user_folder_is_open_qs)

            # TrainingManageを削除しない
            else:
                print("---------- 重複ユーザーはいません ---------")

                # ユーザーと一致するTrainingManageを取得
                user_training_manages_qs = TrainingManage.objects.filter(user__in=delete_user_list, training__in=training_list)
                print("---------- user_training_manages_qs ---------", user_training_manages_qs)

                # ユーザーと一致するトグルボタンの展開データを取得
                user_folder_is_open_qs = FolderIsOpen.objects.filter(user_id__in=delete_user_list, training__in=training_list)
                print("---------- user_folder_is_open_qs ---------", user_folder_is_open_qs)

            # 削除対象のユーザーと一致するPartsgManageを取得
            for user_training_manages in user_training_manages_qs:
                print("--------------- user_training_manages", user_training_manages)# TrainingManage object (509)
                user_parts_manages = user_training_manages.parts_manage.all()
                print("--------------- ユーザーのparts_manage", user_parts_manages)# <QuerySet [<PartsManage: PartsManage object (57)>]>
                # PartsgManageを削除
                user_parts_manages.delete()

            # TrainingManageを削除
            user_training_manages_qs.delete()

            # トグルボタンの展開データを削除
            user_folder_is_open_qs.delete()

        # UserCustomGroupRelationテーブルから該当する一行を削除
        del_users.delete()

        # メッセージを返す
        messages.success(self.request, "グループを削除しました。")

        return reverse_lazy('training:customgroup_management')

"""
カスタムグループの削除(一括)
"""
class AllCustomgroupDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            del_user_list = []

            # 削除しないグループに所属するユーザーのリスト
            not_del_users_list = []

            # 削除にチェックをしたグループIDを取得
            checks = request.POST.getlist('checks[]')

            # IDと一致するグループを取得
            del_groups = CustomGroup.objects.filter(pk__in=checks)
            print("---------- del_groups ---------", del_groups)# <QuerySet [<CustomGroup: 削除用2>, <CustomGroup: 削除用1>]>

            for del_group in del_groups:
                print("---------- del_group ---------", del_group)# 削除用2

                del_users = UserCustomGroupRelation.objects.filter(group_id=del_group.id)
                print("---------- del_users ---------", del_users)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (24)>, <UserCustomGroupRelation: UserCustomGroupRelation object (25)>]>

                # グループに所属しているユーザーを取得
                # for users in del_group.group_user.all():
                for users in del_users:
                    print("---------- users ---------", users)# UserCustomGroupRelation object (41)

                    # リストにユーザーを追加
                    del_user_list.append(users)

                    # UserCustomGroupRelationテーブルから該当する一行を削除
                    users.delete()

            print("---------- del_user_list ---------", del_user_list)# [<UserCustomGroupRelation: UserCustomGroupRelation object (31)>, <UserCustomGroupRelation: UserCustomGroupRelation object (32)>, <UserCustomGroupRelation: UserCustomGroupRelation object (29)>, <UserCustomGroupRelation: UserCustomGroupRelation object (30)>]


            # そのグループが紐づいているトレーニングの情報を取得する
            trainings = Training.objects.filter(destination_group=del_group.pk)
            print("---------- グループに紐づいているトレーニングを取得 ---------", trainings)

            if trainings:

                for training in trainings:
                    # トレーニングに紐づいている削除対象のグループを除いたグループを取得する
                    not_del_groups = training.destination_group.all().exclude(id__in=checks)
                    print("---------- not_del_groups ---------", not_del_groups)

                # グループに所属しているユーザーを取得
                for destination_group in not_del_groups:

                    # 削除しないグループのユーザーをforで回して取り出す
                    for not_del_users in destination_group.group_user.all():
                        print("---------- not_del_users ---------", not_del_users)

                        # リストにユーザーを追加
                        not_del_users_list.append(not_del_users)
                        print("---------- not_del_users_list ---------", not_del_users_list)

                # 完了済みのTrainingManageがあった場合
                if TrainingManage.objects.filter(user__in=del_user_list, status=3):

                    done_training_manages = TrainingManage.objects.filter(user__in=del_user_list, status=3)
                    print("--------------- 完了済みのTrainingManage--------------", done_training_manages)

                    # リストの中に共通するユーザーがいる場合
                    if set(del_user_list) & set(not_del_users_list):
                        print("---------- 重複ユーザーがいます ---------")

                        # 重複しているユーザーのリストを作成
                        repetitive_user = set(del_user_list) & set(not_del_users_list)
                        repetitive_user_list = list(repetitive_user)
                        print("---------- repetitive_user_list ---------", repetitive_user_list)

                        # 重複ユーザーを除いたユーザーと一致するTrainingManageを取得
                        user_training_manages_qs = TrainingManage.objects.filter(user__in=del_user_list).exclude(user__in=repetitive_user_list)
                        print("--------------- 一致するユーザーのTrainingManageを取得(削除) --------------", user_training_manages_qs)

                        # TrainingManageを削除
                        user_training_manages_qs.delete()

                    # TrainingManageを削除しない
                    else:
                        print("---------- 重複ユーザーはいません ---------")

                        # ユーザーと一致するTrainingManageを取得
                        user_training_manages_qs = TrainingManage.objects.filter(user__in=del_user_list)
                        user_training_manages_qs.delete()

            # グループを削除
            CustomGroup.objects.filter(pk__in=checks).delete()

            message = f'グループを削除しました。'
            messages.success(self.request, message)

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "グループを削除しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'グループを削除に失敗しました'
            return JsonResponse(data)




"""
テストパーツの変更
"""
class PartsTestUpdateView(LoginRequiredMixin, CommonView, UpdateView):
    model = Parts
    template_name = 'training/parts_test_update.html'
    form_class = PartsUpdateForm

    def get_form_kwargs(self):

        # formにログインユーザーを渡す
        kwargs = super(PartsTestUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['pk'] = self.kwargs['pk']
        return kwargs


    def form_valid(self, form):

        parts_id = self.kwargs['pk']

        training = Training.objects.filter(parts=parts_id).first()

        # フォームからDBオブジェクトを仮生成
        parts_test_update = form.save(commit=False)

        # 保存
        parts_test_update.save()

        # PartsManageに更新した内容を反映
        parts_manages = PartsManage.objects.filter(parts=parts_test_update)

        for parts_manage in parts_manages:
            parts_manage.is_parts_required = parts_test_update.is_required
            parts_manage.save()

        # メッセージを返す
        messages.success(self.request, "テストパーツを編集しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': training.id}))


"""
アンケートパーツの変更
"""
class PartsQuestionnaireUpdateView(LoginRequiredMixin, CommonView, UpdateView):
    model = Parts
    template_name = 'training/parts_questionnaire_update.html'
    form_class = PartsQuestionnaireUpdateForm


    def get_form_kwargs(self):

        # formにログインユーザーを渡す
        kwargs = super(PartsQuestionnaireUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['pk'] = self.kwargs['pk']
        return kwargs

    def form_valid(self, form):

        parts_id = self.kwargs['pk']

        training = Training.objects.filter(parts=parts_id).first()

        # フォームからDBオブジェクトを仮生成
        parts_questionnaire_update = form.save(commit=False)

        # 保存
        parts_questionnaire_update.save()

        # PartsManageに更新した内容を反映
        parts_manages = PartsManage.objects.filter(parts=parts_questionnaire_update)

        for parts_manage in parts_manages:
            parts_manage.is_parts_required = parts_questionnaire_update.is_required
            parts_manage.save()

        # メッセージを返す
        messages.success(self.request, "アンケートパーツを編集しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': training.id}))


"""
動画パーツの変更
"""
class PartsMovieUpdateView(LoginRequiredMixin, CommonView, UpdateView):
    model = Parts
    template_name = 'training/parts_movie_update.html'
    form_class = PartsMovieUpdateForm


    def get_form_kwargs(self):

        # formにログインユーザーを渡す
        kwargs = super(PartsMovieUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['pk'] = self.kwargs['pk']
        return kwargs


    # 変更処理
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        parts_pk = self.kwargs['pk']

        # トレーニングに紐づいているファイルを取得
        parts = Parts.objects.get(pk=parts_pk)

        # json形式でシリアライズする(動画)
        dist_file = serializers.serialize("json", [ parts.movie])# ifでNoneの場合か分岐する

        if parts.poster:
            dist_poster = serializers.serialize("json", [ parts.poster ])
        else:
            dist_poster = None

        # フロントに返す
        context["dist_file"] = dist_file
        context["dist_poster"] = dist_poster

        return context


    def form_valid(self, form):

        parts_id = self.kwargs['pk']

        training = Training.objects.filter(parts=parts_id).first()

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        before_parts = Parts.objects.filter(id=parts_id).first()
        # print("---------- before_parts.movie.name ---------", before_parts.movie.name)
        # print("---------- before_parts.movie.size ---------", before_parts.movie.size)
        # print("---------- before_parts.poster.name ---------", before_parts.poster.name)
        # print("---------- before_parts.poster.size ---------", before_parts.poster.size)

        # フォームからDBオブジェクトを仮生成
        parts_movie_update = form.save(commit=False)
        print("---------- parts_movie_update.poster.name ---------", parts_movie_update.poster.name)# default_poster

        # ユーザーが設定したポスターからデフォルトポスターに変更した場合
        if before_parts.poster.name == "default_poster":
            print("---------- デフォルトポスタに変更したよ ---------")
            # 会社のディスク使用量からデフォルトで設定されているポスターのサイズを足す
            this_resource_manage.total_file_size += settings.DEFAULT_POSTER
            this_resource_manage.save()

        # 保存
        parts_movie_update.save()

        # PartsManageに更新した内容を反映
        parts_manages = PartsManage.objects.filter(parts=parts_movie_update)

        for parts_manage in parts_manages:
            parts_manage.is_parts_required = parts_movie_update.is_required
            parts_manage.save()

        # セッションの中にup_poster_idがれば取り出す ※ポスターがない場合はデフォルトの画像が適用される
        if 'up_poster_id' in self.request.session:

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_poster_id_str = self.request.session['up_poster_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_poster_id_list = up_poster_id_str.split(',')

            # リストのInt型に変換
            up_poster_id_int = [int(s) for s in up_poster_id_list]

            # オブジェクトの取得
            poster = Poster.objects.filter(pk__in=up_poster_id_int).first()
            print("---------- poster.name ---------", poster.name)
            print("---------- poster.size ---------", poster.size)

            # ポスター変更前がデフォルトポスターだった場合
            if before_parts.poster.name == "default_poster":
                print("---------- デフォルトポスターだったよ ---------")
                # 会社のディスク使用量からデフォルトで設定されているポスターのサイズを引く
                this_resource_manage.total_file_size -= settings.DEFAULT_POSTER
                this_resource_manage.save()

            # 会社のディスク使用量に変更したポスターのサイズを足す
            this_resource_manage.total_file_size += int(poster.size)
            this_resource_manage.save()

            # タスクとファイルを紐付ける
            parts_movie_update.poster = poster

            parts_movie_update.save()

            # セッションデータを削除する
            del self.request.session['up_poster_id']

        # # セッションの中にup_file_idがれば取り出す
        if 'up_movie_id' in self.request.session:

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_movie_id_str = self.request.session['up_movie_id'].replace(" ", "").replace("[", "").replace("]", "")

            # リストに変換
            up_movie_id_list = up_movie_id_str.split(',')

            # リストのInt型に変換
            up_movie_id_int = [int(s) for s in up_movie_id_list]

            after_movie = Movie.objects.filter(pk__in=up_movie_id_int).first()
            print("---------- after_movie.size ---------", after_movie.size)

            # ファイルのパスを取得
            movie_path = urllib.parse.unquote(before_parts.movie.movie.url)

            # ファイルパスを分割してファイル名だけ取得
            movie_name = movie_path.split('/',4)[4]

            # 絶対パスでファイル実体を削除
            os.remove(os.path.join(settings.MOVIE_FULL_MEDIA_ROOT, movie_name))

            # 会社のディスク使用量にファイルのサイズを引く
            this_resource_manage.total_file_size -= int(before_parts.movie.size)
            this_resource_manage.save()

            # DBの対象行を削除
            before_parts.movie.delete()

            # 古いモデルオブジェクトに新しいものを代入
            parts_movie_update.movie = after_movie

            parts_movie_update.save()

            # 会社のディスク使用量にファイルのサイズを足す
            this_resource_manage.total_file_size += int(after_movie.size)
            this_resource_manage.save()

            # セッションデータを削除する
            del self.request.session['up_movie_id']

        # PartsモデルからIDと一致するパーツオブジェクトを取得(純粋なオブジェクトを取得するために)
        movie_parts_obj = Parts.objects.filter(pk=parts_movie_update.id).first()

        # トレーニングとパーツを紐づける
        training.parts.add(movie_parts_obj)

        # メッセージを返す
        messages.success(self.request, "動画パーツを編集しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': training.id}))






"""
ファイルパーツの変更
"""
class PartsFileUpdateView(LoginRequiredMixin, UpdateView, CommonView):
    model = Parts
    template_name = 'training/parts_file_update.html'
    form_class = PartsFileUpdateForm

    def get_form_kwargs(self):

        # formにログインユーザーを渡す
        kwargs = super(PartsFileUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['pk'] = self.kwargs['pk']
        return kwargs

    # 変更処理
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        parts_pk = self.kwargs['pk']
        context["parts_pk"] = parts_pk

        # トレーニングに紐づいているファイルを取得
        parts = Parts.objects.get(pk = parts_pk)
        print("-------------------", parts.id)

        # json形式でシリアライズする
        dist_file = serializers.serialize("json", parts.file.all(), fields=('name', 'file', 'id', 'file_id', 'size'))
        print("------------------- dist_file", dist_file)

        # フロントに返す
        context["dist_file"] = dist_file

        return context


    def form_valid(self, form):

        parts_id = self.kwargs['pk']

        training = Training.objects.filter(parts=parts_id).first()

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        # フォームからDBオブジェクトを仮生成
        parts_file_update = form.save(commit=False)

        # 保存
        parts_file_update.save()

        # PartsManageに更新した内容を反映
        parts_manages = PartsManage.objects.filter(parts=parts_file_update)

        for parts_manage in parts_manages:
            parts_manage.is_parts_required = parts_file_update.is_required
            parts_manage.save()

        # セッションの中にup_file_idがれば取り出す
        if 'up_file_id' in self.request.session:

            print("--------------- up_file_id --------------", self.request.session['up_file_id'])# [99]
            print("--------------- up_file_id タイプ --------------", type(self.request.session['up_file_id']))# <class 'str'>

            # ファイルとタスクを紐付ける
            # ファイル情報をセッションから取得
            up_file_id_str = self.request.session['up_file_id'].replace(" ", "").replace("[", "").replace("]", "")
            print("--------------- up_file_id_str --------------", up_file_id_str)# 99

            # リストに変換
            up_file_id_list = up_file_id_str.split(',')
            print("--------------- up_file_id_list --------------", up_file_id_list)# ['99']
            print("--------------- up_file_id_list タイプ --------------", type(up_file_id_list))# <class 'list'>

            # リストのInt型に変換
            up_file_id_int = [int(s) for s in up_file_id_list]
            print("--------------- up_file_id_int --------------", up_file_id_int)# [99]

            # オブジェクトの取得
            files = File.objects.filter(pk__in=up_file_id_int)

            for file in files:
                print("---------- file ---------", file)# 変更前.PNG
                print("---------- file.size ---------", file.size)# 171330
                print("---------- file.size type ---------", type(file.size))# <class 'str'>

                # file_idにランダムな文字列を代入
                file.file_id = get_random_string(10)
                file.save()

                # 会社のディスク使用量にファイルのサイズを足す
                this_resource_manage.total_file_size += int(file.size)
                this_resource_manage.save()

            # タスクとファイルを紐付ける(ManyToManyField用)
            parts_file_update.file.add(*files)

            # セッションデータを削除する
            del self.request.session['up_file_id']

            parts_file_update.save()


        # メッセージを返す
        messages.success(self.request, "ファイルパーツを編集しました。")

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': training.id}))


"""
ポスターの削除
"""
class PosterDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            poster_pk = request.POST.get('file_name')

            # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
            this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
            print("---------- this_resource_manage ---------", this_resource_manage)

            # # 1から始まるインデックスと要素を同時に取得
            poster_obj = Poster.objects.filter(pk=poster_pk).first()
            print("---------- poster_obj ---------", poster_obj)
            print("---------- poster_obj.size ---------", poster_obj.size)

            # 会社のディスク使用量にファイルのサイズを引く
            this_resource_manage.total_file_size -= int(poster_obj.size)
            this_resource_manage.save()

            poster_obj.delete()

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "サーバーからポスターを削除しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'ポスターの削除に失敗しました'
            return JsonResponse(data)




"""
ファイルの削除
"""
class FileDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            print("----------------- ファイルの削除")

            file_pk = request.POST.get('file_name')
            print("--------------- file_pk", file_pk)

            # parts_id = self.kwargs['pk']
            parts_pk = request.POST.get('parts_pk')
            print("---------- parts_pk ---------", parts_pk)

            file_parts = Parts.objects.filter(pk=parts_pk).first()
            print("------------------ file_parts", file_parts)

            # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
            this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
            print("---------- this_resource_manage ---------", this_resource_manage)

            # 1から始まるインデックスと要素を同時に取得
            file = File.objects.filter(pk=file_pk).first()
            print("---------- file_obj ---------", file)
            print("---------- file_obj.size ---------", file.size)

            # 会社のディスク使用量にファイルのサイズを引く
            this_resource_manage.total_file_size -= int(file.size)
            this_resource_manage.save()

            another_parts_count = Parts.objects.filter(file=file).count()
            print("---------- another_parts_count ---------", another_parts_count)

            if another_parts_count > 1:
                print("---------- 他にファイルが紐づいてるパーツがあったよ ---------")
                file_parts.file.remove(file)
                file_parts.save()
            else:
                # パーツに紐づくファイルを削除
                file.delete()

            # file_obj.delete()

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "サーバーからファイルを削除しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'ファイルの削除に失敗しました'
            return JsonResponse(data)


"""
画像の削除
"""
class ImageDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            print("----------------- 画像の削除")

            image_pk = request.POST.get('image_up_name')

            question_pk = request.POST.get('question_pk')
            print("---------- question_pk ---------", question_pk)

            question = Question.objects.filter(pk=question_pk).first()
            print("------------------ question", question)

            questionnaire_question = QuestionnaireQuestion.objects.filter(pk=question_pk).first()
            print("------------------ questionnaire_question", questionnaire_question)

            # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
            this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
            print("---------- this_resource_manage ---------", this_resource_manage)

            # 1から始まるインデックスと要素を同時に取得
            image = Image.objects.filter(pk=image_pk).first()
            print("---------- image_obj ---------", image)
            print("---------- image_obj.size ---------", image.size)

            # 会社のディスク使用量に画像のサイズを引く
            this_resource_manage.total_file_size -= int(image.size)
            this_resource_manage.save()

            another_parts_count_question = Question.objects.filter(image=image).count()
            print("---------- another_parts_count_question ---------", another_parts_count_question)

            another_parts_count_questionnaire = QuestionnaireQuestion.objects.filter(image=image).count()
            print("---------- another_parts_count_questionnaire ---------", another_parts_count_questionnaire)

            if another_parts_count_question:
                print("---------- テストの設問 ---------")
                if another_parts_count_question > 1:
                    print("---------- 他にファイルが紐づいてるパーツがあったよ ---------")
                    question.image.remove(image)
                    question.save()
                else:
                    # パーツに紐づくファイルを削除
                    image.delete()

            if another_parts_count_questionnaire:
                print("---------- アンケートの設問 ---------")
                if another_parts_count_questionnaire > 1:
                    print("---------- 他にファイルが紐づいてるパーツがあったよ ---------")
                    questionnaire_question.image.remove(image)
                    questionnaire_question.save()
                else:
                    # パーツに紐づくファイルを削除
                    image.delete()

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "サーバーから画像を削除しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = 'ポスターの削除に失敗しました'
            return JsonResponse(data)





"""
テストの設問変更 選択肢の削除
"""
class ChoiceDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            choice_id = request.POST.get('choice_id')

            # 一致するchoiceを取得
            choice_obj = Choice.objects.filter(pk=choice_id).first()

            choice_obj.delete()

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "選択項目を削除しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = '選択項目の削除に失敗しました'
            return JsonResponse(data)


"""
テストの設問変更 選択肢の削除
"""
class QuestionnaireChoiceDeleteView(View):

    def post(self, request, *args, **kwargs):

        try:
            choice_id = request.POST.get('choice_id')

            # 一致するchoiceを取得
            choice_obj = QuestionnaireChoice.objects.filter(pk=choice_id).first()

            choice_obj.delete()

            # メッセージを生成してJSONで返す
            return JsonResponse({"status": "ok",
                                "message": "選択項目を削除しました",
                                })


        except Exception as e:
            print("ERROR", e) # 'e'の中にエラーの該当行が入る
            data = {}
            data['status'] = 'ng'
            data['message'] = '選択項目の削除に失敗しました'
            return JsonResponse(data)


class MemberListView(DetailView):
    template_name = 'training/member_list.html'
    model = CustomGroup

    # def get_queryset(self):
    #     return super().get_queryset().filter(user_id=self.request.user.id)

"""
トレーニングの複製
"""
class TrainingCopyView(View):

    def post(self, request, *args, **kwargs):
    # def post_save(self, sender,instance, **kwargs):

        print("------------------ トレーニングの複製")

        training_id = self.kwargs['pk']

        # コピー元のレコードを取得
        training = Training.objects.filter(pk=training_id).first()
        print("------------------ training", training)

        # コピー元のタイトルを取得
        original_training_title = training.title

        original_training_destination_groups = training.destination_group.all()
        print("---------- 宛先グループ ---------", original_training_destination_groups)

        # トレーニングに紐づく全てのパーツを取得
        original_training_parts_all = training.parts.all()
        print("---------- パーツ ---------", original_training_parts_all)

        # トレーニングを複製する
        training.id = None # idをNoneにすることで新規登録できる
        training.title = training.title + "コピー_1" # 元のオブジェクトからデータを引き継いで一部加工
        training.save()# 保存

        # トレーニングにグループを紐づける
        training.destination_group.set(original_training_destination_groups)

        # リソース管理テーブルからトレーニングを作成した会社のレコードを取得
        this_resource_manage = ResourceManagement.objects.filter(reg_company_name=self.request.user.company.id).first()
        print("---------- this_resource_manage ---------", this_resource_manage)

        # 会社に紐づくトレーニング数に新規作成したトレーニングの数を足す
        this_resource_manage.number_of_training += 1
        print("---------- this_resource_manage.number_of_training ---------", this_resource_manage.number_of_training)

        # トレーニングの合計サイズ = 会社に紐づくトレーニング数 × 20KB(=20480B)
        this_resource_manage.number_of_file = this_resource_manage.number_of_training * settings.TRAINING_SIZE

        # 会社のディスク使用量(=トレーニングの合計サイズ+ファイルの合計サイズ)
        this_resource_manage.total_file_size += settings.TRAINING_SIZE

        this_resource_manage.save()

        # トレーニングに紐づくグループを取得
        for group in training.destination_group.all():

            # グループに所属する全ユーザーを取得
            for user in group.group_user.all():

                # TrainingManageにユーザー分の管理テーブルを作成
                training_manage, created = TrainingManage.objects.get_or_create(
                    training = training,
                    user = user,
                    status = 1, # 未対応
                    subject_manage = training.subject
                )
                training_manage.save()

                # TrainingHistoryテーブルにトレーニングの情報を残す
                if training_manage is not None:
                    training_history, created = TrainingHistory.objects.get_or_create(
                        training = training,
                        reg_user = training.reg_user,
                        user = training_manage.user,
                        status = 1
                    )
                training_history.save()

        # パーツを複製する
        for parts in original_training_parts_all:

            # ファイルパーツ
            if parts.type == 1:

                files = parts.file.all()
                print("---------- file ---------", files)

                parts.id = None # インスタンスのidを空にする
                parts.title = parts.title + "コピー"
                parts.save()# 保存

                # ファイルを紐づける
                parts.file.set(files)
                parts.save()# 保存

            # 動画パーツ
            elif parts.type == 2:
                print("------------- 動画パーツです")

                parts.id = None # インスタンスのidを空にする
                parts.title = parts.title + "コピー"
                parts.save()# 保存

                if not parts.poster:
                    print("---------- デフォルトポスターだったよ ---------")
                    # 会社のディスク使用量にポスターのサイズを足す
                    this_resource_manage.total_file_size += settings.DEFAULT_POSTER

            # テストパーツ
            elif parts.type == 3:
                print("------------- テストパーツです")

                # 紐づいている設問を取得
                questions = Question.objects.filter(parts=parts)
                print("---------- questions ---------", questions)

                # 複製
                parts.id = None # インスタンスのidを空にする
                parts.title = parts.title + "コピー"
                parts.save()# 保存

                copy_parts = Parts.objects.filter(pk=parts.id).first()
                print("---------- copy_parts ---------", copy_parts)

                for question in questions:

                    images = question.image.all()
                    print("---------- images ---------", images)

                    choices = Choice.objects.filter(question=question)
                    print("---------- choices ---------", choices)

                    question.id = None # インスタンスのidを空にする
                    question.save()# 保存

                    # 設問にパーツを紐づける
                    question.parts = copy_parts
                    # 画像を紐づける
                    question.image.set(images)
                    # 保存
                    question.save()

                    for choice in choices:
                        choice.id = None # インスタンスのidを空にする
                        choice.save()# 保存

                        # 設問にパーツを紐づける
                        choice.question = question
                        # 保存
                        choice.save()

            # アンケートパーツ
            elif parts.type == 4:
                print("------------- アンケートパーツです")

                # 紐づいている設問を取得
                questionnaire_questions = QuestionnaireQuestion.objects.filter(parts=parts)
                print("---------- questionnaire_questions ---------", questionnaire_questions)

                parts.id = None # インスタンスのidを空にする
                parts.title = parts.title + "コピー"
                parts.save()# 保存

                copy_parts = Parts.objects.filter(pk=parts.id).first()
                print("---------- copy_parts ---------", copy_parts)

                for questionnaire_question in questionnaire_questions:

                    images = questionnaire_question.image.all()
                    print("---------- images ---------", images)

                    choices = QuestionnaireChoice.objects.filter(question=questionnaire_question)
                    print("---------- QuestionnaireChoice ---------", choices)

                    questionnaire_question.id = None # インスタンスのidを空にする
                    questionnaire_question.save()# 保存

                    # 設問にパーツを紐づける
                    questionnaire_question.parts = copy_parts
                    # 画像を紐づける
                    questionnaire_question.image.set(images)
                    # 保存
                    questionnaire_question.save()

                    for choice in choices:
                        choice.id = None # インスタンスのidを空にする
                        choice.save()# 保存

                        # 設問にパーツを紐づける
                        choice.question = questionnaire_question

                        # 保存
                        choice.save()

            # パーツをトレーニングに紐づける
            training.parts.add(parts.id)

        # メッセージを返す
        message = f"「" + original_training_title + "」" + "から" + training.title + "を複製しました。"
        messages.success(self.request, message)

        return HttpResponseRedirect(reverse('training:training_edit_menu', kwargs={'pk': training.id}))