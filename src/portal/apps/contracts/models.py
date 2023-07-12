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

from accounts.models import User, Company, Messages, Service




"""
プランテーブル
"""
class Plan(models.Model):
    #id
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # サービス
    service = models.ForeignKey(Service, null=False, on_delete=models.CASCADE, default=1)
    # 商品ID（★stripeの商品IDを値に用いる）
    stripe_plan_id = models.CharField('StripeのプランID', max_length=100, blank=False, default="pln")
    # 名前
    name = models.CharField('プラン名', max_length=30, blank=False)
    # 料金(年額)
    price = models.IntegerField('価格', blank=True, default=0)
    # 単価(月額)
    unit_price = models.IntegerField('価格(単価)', blank=True, default=0)
    # 説明
    description = models.TextField('説明', blank=True)
    # ユーザー数
    user_num = models.IntegerField('ユーザー数', blank=True, default=0)
    # カテゴリー
    category = models.CharField('カテゴリー', max_length=30, default="なし")
    # オプションフラグ
    is_option = models.BooleanField(default=False, blank=True)
    # 試用フラグ
    is_trial = models.BooleanField(default=False, blank=True)
    #Stripe用価格id
    stripe_price_id = models.CharField('Stripeの価格ID', max_length=100, blank=False, default="price")
    #表示順
    layout = models.IntegerField('表示順', blank=True, default=1)
    # 現在の価格利用可能期限
    end_date = models.DateTimeField(_('end_date'), null=True, blank=True)

    def __str__(self):
        return self.name

"""
支払い方法テーブル
"""
class PaymentMethod(models.Model):
    # 表示名
    name = models.CharField('名前', max_length=255)
    # 説明
    description = models.TextField('説明', blank=True)
    # 決済割引
    payment_discount = models.IntegerField('決済割引', blank=True, default=0)


    def __str__(self):
        return self.name


"""
割引テーブル
"""
class Discount(models.Model):
    DISCOUNT_TIPE = (
            ('1', '％'),
            ('2', '円'),
    )
    PAYMENT_METHOD = (
            ('1','クレジット'),
            ('2','銀行振込'),
    )

    #id
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #名前
    name = models.CharField('クーポン名', max_length=50, blank=False)
    #クーポンコード(ユーザー表示用)
    coupon_code = models.CharField('クーポンコード', max_length=20, null=True, blank=True)
    # クーポンID
    coupon_id = models.CharField('クーポンID', max_length=50, blank=False, default="coupon")
    #割引タイプ
    discount_type = models.CharField(_('discount_type'), max_length=1, choices=DISCOUNT_TIPE, blank=False, default="2")
    #割引率
    discount_rate = models.IntegerField('割引率', blank=False, default=0)
    #使用期限
    expiration_date = models.DateTimeField(_('expiration date'), default=timezone.now, blank=True)
    #回数制限(個別)
    limit = models.IntegerField('回数制限(個別)', blank=True, null=True)
    #回数制限(全体)
    limit_all = models.IntegerField('回数制限(全体)', blank=True, null=True)
    #引換え済回数
    number_of_use = models.IntegerField('引換え済回数', blank=True, default=0)
    #対象者(デフォルトは全員適用の１)
    target = models.IntegerField('対象カテゴリー', blank=False, default="1")
    #対象の支払い手段
    payment = models.CharField(_('discount_type'), max_length=1, choices=PAYMENT_METHOD, blank=False, default="1")



"""
見積テーブル
"""
class Estimates(models.Model):
    #見積りID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ユーザー
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, default="")
    # サービス
    service = models.ForeignKey(Service, null=False, on_delete=models.CASCADE, verbose_name='サービス')
    # 表示用ナンバー
    num = models.CharField(_('estimates no'), max_length=20, blank=False)
    # プラン
    plan = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='プラン', default="", related_name='estimate_plan')
    # 終了日(見積期限）
    expiration_date = models.DateTimeField(_('expiration date'), default=timezone.now, blank=True)
    # 小計(プラン＋オプション＋割引含めた値)
    minor_total = models.IntegerField('小計', blank=False, default=0)
    # 消費税
    tax = models.IntegerField('消費税', blank=False, default=0)
    # 合計(プラン＋オプション＋割引＋消費税)
    total = models.IntegerField('合計', blank=False, default=0)
    # 小計(プラン＋オプションの合計を月額に割った値)
    unit_minor_total = models.IntegerField('小計(単価)', blank=False, default=0)
    # 合計(プラン＋オプションの合計値)
    unit_total = models.IntegerField('合計(単価)', blank=False, default=0)
    # 使用フラグ
    is_use = models.BooleanField('使用フラグ', blank=False, default=False)
    # 契約開始日
    # start_day = models.DateTimeField(_('start date'), default=timezone.now, blank=True)
    
    start_day = models.DateField(_('start date'), default=timezone.now, blank=True)
    # 契約終了日
    end_day = models.DateTimeField(_('end date'), default=timezone.now, blank=True)
    # 請求書オプションフラグ
    is_invoice_need = models.BooleanField('請求書オプションフラグ', blank=True, null=True, default=False)
    # 支払い方法
    method_payment = models.ForeignKey(PaymentMethod, null=True, on_delete=models.CASCADE, verbose_name='支払い方法', related_name='estimate_payment', default=1)
    # 更新用フラグ
    is_update = models.BooleanField('更新用フラグ', blank=True, default=False)
    # プラン変更用フラグ
    is_change = models.BooleanField('プラン変更用フラグ',blank=True,default=False)
    # 作成日
    created_date = models.DateTimeField(_('created date'), default=timezone.now, blank=True)
    #請求先選択
    bill_address = models.IntegerField('請求書の宛先', default='1')
    #作成途中の仮フラグ
    temp_check = models.BooleanField('仮作成フラグ',blank=False, default=True)
    # オプション1
    option1 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション1', default="", related_name='estimate_option1')
    # オプション2
    option2 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション2', default="", related_name='estimate_option2')
    # オプション3
    option3 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション3', default="", related_name='estimate_option3')
    # オプション4
    option4 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション4', default="", related_name='estimate_option4')
    # オプション5
    option5 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション5', default="", related_name='estimate_option5')
    # クーポン
    discount = models.ForeignKey(Discount, null=True, on_delete=models.CASCADE, verbose_name='割引', related_name='estimate_discount')
    # 差額
    difference = models.IntegerField('差額', blank=False, default=0)
    # 契約フラグ（正式に契約を結んだ見積りのみ）
    is_signed = models.BooleanField('契約フラグ',blank=False, default=False)


"""
契約テーブル
"""
class Contract(models.Model):

    STATUS_CHOICES = (
            ('1', '試用'),
            ('2', '本番'),
            ('3', '解約'),
            ('4', '旧契約')
    )
    #ID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # ユーザー
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE, default="")
    # 会社
    company = models.ForeignKey(Company, null=False, on_delete=models.CASCADE, default="")
    # サービス
    service = models.ForeignKey(Service, null=False, on_delete=models.CASCADE, default=1)
    # service = models.CharField('サービス', max_length=10, blank=True, null=True)
    # ステータス(試用、本番)
    status = models.CharField(_('status'), max_length=1, choices=STATUS_CHOICES, blank=True)
    # 契約開始日(試用、本番)
    contract_start_date = models.DateTimeField(_('contract start date'), null=True)
    # 契約終了日(試用、本番）
    contract_end_date = models.DateTimeField(_('contract end date'), null=True)
    # 支払い開始日(試用、本番)
    pay_start_date = models.DateTimeField(_('pay start date'), null=True)
    # 支払い終了日(試用、本番）
    pay_end_date = models.DateTimeField(_('pay end date'), null=True)
    # 紐づく見積
    estimate = models.ManyToManyField(Estimates, verbose_name="見積もり", blank=True)
    # 紐づく支払い(※循環インポートを避けるためクラス名から指定)
    payment = models.ForeignKey('payment.Payment', null=True, default="", on_delete=models.CASCADE)
    # プラン
    plan = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='プラン', related_name='contract_plan')
    # 小計
    minor_total = models.IntegerField('小計', blank=False, default=0)
    # 消費税
    tax = models.IntegerField('消費税', blank=False, default=0)
    # 合計
    total = models.IntegerField('合計', blank=False, default=0)
    # 自動更新の有効・無効
    is_autocheckout = models.BooleanField(null=True)
    # 請求書オプションフラグ
    is_invoice_need = models.BooleanField('請求書オプションフラグ', blank=True, default=False)
    # 請求書オプション割引
    # invoice_op_discount = models.IntegerField('請求書オプション割引', blank=True, default='3000')
    # オプション1
    option1 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション1', default="", related_name='contract_option1')
    # オプション2
    option2 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション2', default="", related_name='contract_option2')
    # オプション3
    option3 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション3', default="", related_name='contract_option3')
    # オプション4
    option4 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション4', default="", related_name='contract_option4')
    # オプション5
    option5 = models.ForeignKey(Plan, null=True, on_delete=models.CASCADE, verbose_name='オプション5', default="", related_name='contract_option5')
    # クーポン
    discount = models.ForeignKey(Discount, null=True, on_delete=models.CASCADE, verbose_name='割引', related_name='contract_discount')
    # 解約日
    cancellation_date = models.DateTimeField(_('cancellation_date'), null=True)