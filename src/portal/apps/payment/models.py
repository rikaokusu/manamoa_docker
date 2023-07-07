from django.db import models

from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django.contrib.auth.base_user import BaseUserManager
import os

import uuid

from accounts.models import User, Company, Messages, Service
from contracts.models import PaymentMethod, Contract

# """
# STRIPEPLANテーブル
# """
# class StripeOption(models.Model):
#     # ユーザー
#     name = models.CharField('プラン名', max_length=255)
    # ユーザー
    # stripe_id = models.CharField('stripe ID', max_length=255)


"""
支払いテーブル
"""
class Payment(models.Model):
    # ユーザー
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, related_name='payment_user')

    # 支払い済みフラグ
    is_paymented = models.BooleanField(default=False, blank=True)

    # 支払い方法
    method_payment = models.ForeignKey(PaymentMethod, null=True, on_delete=models.CASCADE, verbose_name='支払い方法', related_name='payment_paymentmethod')

    # 支払い日
    created_date = models.DateTimeField(_('created date'), default=timezone.now, blank=True)

    # 支払い回数
    pay_count = models.IntegerField('支払い回数', blank=False, default=1)

    # StripeのサブスクリプションID(プラン)
    stripe_plan = models.CharField(_('stripe plan'), max_length=255, null=True, blank=True)

    # StripeのサブスクリプションスケジュールID(プラン変更)
    stripe_sched_plan = models.CharField(_('stripe sched plan'), max_length=255, null=True, blank=True)