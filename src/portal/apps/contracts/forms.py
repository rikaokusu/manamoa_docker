from django import forms
from accounts.models import User, Company, Service, Stripe
from .models import Estimates, Plan, Contract, PaymentMethod, Discount
from payment.models import Payment
# 日付カレンダー表示
import bootstrap_datepicker_plus as datetimepicker
from betterforms.multiform import MultiModelForm

# DBのカウント(サービステーブルから契約テーブルの数を計算する際に使用)
from django.db.models import Count, Q

# 翻訳
from django.utils.translation import gettext_lazy as _
# 時間を扱う
import datetime

"""
見積書のサービス選択用ラジオボタン
"""
class Service_Radio_For_Estimate(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'contracts/forms/widget/service_radio.html'
    def get_context(self, name, value, attrs):
            service_initial_name_list = []
            service_contract_count_list = []
            service_contract_user_count_list = []
            service_contract_user_count_dict = {}
            service_contracted_user_count_list = {}
            context = super(Service_Radio_For_Estimate, self).get_context(name, value, attrs)
            services = Service.objects.all().annotate(num_contract=Count('contract', filter=Q(contract__company_id=self.attrs['company_id']))).exclude(name="Comming Soon")

            for service in services:
                # サービス毎の頭文字をリストへ追加
                service_initial_name = service.initial
                service_initial_name_list.append(service_initial_name)

                # サービス毎の契約状況を調査。契約状況にログインユーザーの存在を確認してカウントアップする(0=は未契約、1以上は契約)
                service_contract_count = service.num_contract
                print('なむこんとらくとのかず＝＝＝＝＝＝',service_contract_count)
                service_contract_count_list.append(service_contract_count)

            context['service_initial_name_list'] = service_initial_name_list
            context['service_contract_count_list'] = service_contract_count_list

            return context

"""
見積書のプラン選択用ラジオボックス
"""
class Plan_Radio_For_Estimate(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'contracts/forms/widget/plan_radio.html'

    def get_context(self, name, value, attrs):
            plan_price_list = []

            context = super(Plan_Radio_For_Estimate, self).get_context(name, value, attrs)
            plans = Plan.objects.filter(is_trial=False, is_option=False).values('id', 'price')
            plan_price_dict = [entry for entry in plans]

            context['plan_price_dict'] = plan_price_dict

            return context

"""
見積書のオプション選択用ラジオボックス
"""
class Option_Radio_For_Estimate(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'contracts/forms/widget/option_radio.html'

    def get_context(self, name, value, attrs):
            plan_price_list = []
            context = super(Option_Radio_For_Estimate, self).get_context(name, value, attrs)
            plans = Plan.objects.filter(is_trial=False, is_option=True).values('id', 'price', 'category')
            plans_cat_list = Plan.objects.filter(is_trial=False, is_option=True).order_by("name").values_list('category', flat=True)
            plan_price_dict = [entry for entry in plans]
            plans_cat_dict = [entry for entry in plans_cat_list]
            # plans_cat_dict = [entry for entry in plans_list]
            context['plans_cat_list'] = list(plans_cat_list)
            context['plan_price_dict'] = plan_price_dict

            return context


"""
見積書の支払い方法選択用チェックボックス
"""
class Payment_Radio_For_Estimate(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'contracts/forms/widget/payment_radio.html'

    def get_context(self, name, value, attrs):
            context = super(Payment_Radio_For_Estimate, self).get_context(name, value, attrs)
            stripe_id = Stripe.objects.filter(company=self.attrs['user'].company).first()

            if stripe_id.stripe_card_id:
                context['stripe_id'] = stripe_id
            else:
                context['stripe_id'] = 'None'
            return context

"""
見積書の作成(STEP1)
"""
class EstimateStep1Form(forms.ModelForm):

    start_day = forms.DateField(required=True, label="サービス利用開始日", 
                                widget=datetimepicker.DatePickerInput(format='%Y/%m/%d',
                                options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM', 'minDate' : datetime.datetime.today().strftime('%Y-%m-%d'), 'tooltips': {
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
            }), input_formats=['%Y/%m/%d'])


    # dist_start_date = forms.DateTimeField(required=True, label="配布開始日", widget=datetimepicker.DateTimePickerInput(format='%Y/%m/%d %H:%M:%S', options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM',}), input_formats=['%Y/%m/%d %H:%M:%S'])



    class Meta:
        model = Estimates
        fields = ('service','start_day',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(EstimateStep1Form, self).__init__(*args, **kwargs)
        self.fields['service'] = forms.ModelChoiceField(label="利用サービス",
                                        widget=Service_Radio_For_Estimate(attrs = {'company_id': self.user.company, 'readonly':'readonly'}),
                                        queryset=Service.objects.annotate(num_contract=Count('contract', filter=Q(contract__company=self.user.company))).exclude(name="Comming Soon"),
                                        required=True,
                                        empty_label=None,
                                                    )



"""
見積書の作成--Estimate(STEP2)
"""
class EstimateStep2Form(forms.ModelForm):

    class Meta:
        model = Estimates
        fields = ('plan', 'option1', 'option2', 'option3', 'option4','option5' )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.service_id = kwargs.pop('service_id')
        service = Service.objects.get(pk=self.service_id)

        super(EstimateStep2Form, self).__init__(*args, **kwargs)
        self.fields['plan'] = forms.ModelChoiceField(label="プラン",
                                        widget=Plan_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=False, is_trial=False).order_by('layout'),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['option1'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="1").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option2'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="2").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option3'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="3").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option4'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="4").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option5'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="5").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

"""
請求書の宛名選択のカスタマイズをするためのウィジェット
"""
class Bill_Address_Radio(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'contracts/forms/widget/bill_address_radio.html'

"""
請求先
"""
BILL_ADDRESS = (
            ('1', '会社'),
            ('2', '設定した請求先'),
)

"""
見積書の作成(STEP3)
"""
class EstimateStep3Form(forms.ModelForm):
    discount = forms.CharField(label="割引コード", required=False, max_length=10)

    class Meta:
        model = Estimates
        fields = ('method_payment', 'is_invoice_need', 'bill_address')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(EstimateStep3Form, self).__init__(*args, **kwargs)
        self.fields['method_payment'] = forms.ModelChoiceField(label="支払い方法",
                                        widget=Payment_Radio_For_Estimate(attrs = {'user': self.user}),
                                        queryset=PaymentMethod.objects.all(),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['is_invoice_need'] = forms.BooleanField(label="請求書オプション", 
                                        required=False,)

        self.fields['bill_address'] = forms.ChoiceField(label='請求書の宛名',
                                        required=True, 
                                        widget=Bill_Address_Radio(), 
                                        choices=BILL_ADDRESS
                                        )


"""
見積書の複製
"""
class EstimateCopyForm(forms.ModelForm):

    discount = forms.CharField(label="割引コード", required=False, max_length=10)
    start_day = forms.DateField(required=True, label="サービス利用開始日", 
                    widget=datetimepicker.DatePickerInput(format='%Y/%m/%d',
                    options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM', 'minDate' : datetime.datetime.today().strftime('%Y-%m-%d'), 'tooltips': {
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
                }), input_formats=['%Y/%m/%d'])

    class Meta:
        model = Estimates
        fields = ('start_day',)

   
"""
申し込み
"""
class OfferStep1Form(forms.ModelForm):

    start_day = forms.DateField(required=True, label="サービス利用開始日", 
                                widget=datetimepicker.DatePickerInput(format='%Y/%m/%d', 
                                options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM', 'minDate' : datetime.datetime.today().strftime('%Y-%m-%d'),'tooltips': {
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
            }),input_formats=['%Y/%m/%d'])

    class Meta:
        model = Estimates
        fields = ('start_day', 'plan', 'option1', 'option2', 'option3', 'option4','option5')


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.service_id = kwargs.pop('service_id')
        service = Service.objects.get(pk=self.service_id)
        super(OfferStep1Form, self).__init__(*args, **kwargs)
        # self.fields['service'] = forms.ModelChoiceField(label="利用サービス",
        #                                 widget=Service_Radio_For_Estimate(attrs = {'company_id': self.user.company, 'readonly':'readonly'}),
        #                                 queryset=Service.objects.annotate(num_contract=Count('contract', filter=Q(contract__user_id=self.user))),
        #                                 required=False,
        #                                 empty_label=None,
        #                                             )

        self.fields['plan'] = forms.ModelChoiceField(label="プラン",
                                        widget=Plan_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=False, is_trial=False).order_by('layout'),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['option1'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="1").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option2'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="2").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option3'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="3").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option4'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="4").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option5'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'company_id': self.user.company}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="5").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )


"""
申込み　ステップ2
"""
class OfferStep2Form(forms.ModelForm):
    discount = forms.CharField(label="割引コード", required=False, max_length=10)

    class Meta:
        model = Estimates
        fields = ('method_payment', 'is_invoice_need','bill_address')

    def __init__(self, *args, **kwargs):
        self.total_price = kwargs.pop('total_price')
        self.user = kwargs.pop('user')
        super(OfferStep2Form, self).__init__(*args, **kwargs)
        self.fields['method_payment'] = forms.ModelChoiceField(label="支払い方法",
                                        widget=Payment_Radio_For_Estimate(attrs = {'total_price': self.total_price,'user':self.user}),
                                        queryset=PaymentMethod.objects.all(),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['is_invoice_need'] = forms.BooleanField(label="請求書オプション", required=False,)
       
        self.fields['bill_address'] = forms.ChoiceField(label='請求書の宛名',
                                        required=True, 
                                        widget=Bill_Address_Radio(), 
                                        choices=BILL_ADDRESS
                                        )



class UpdateContractNochangeStep1Form(forms.ModelForm):
    # discount = forms.CharField(label="割引コード", required=False, max_length=10)
    
    class Meta:
        model = Estimates
        fields = ('method_payment', 'is_invoice_need')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        # self.contract_id = kwargs.pop('contract_id')

        super(UpdateContractNochangeStep1Form, self).__init__(*args, **kwargs)
        self.fields['method_payment'] = forms.ModelChoiceField(label="支払い方法",
                                        widget=Payment_Radio_For_Estimate(attrs = {'user':self.user}),
                                        queryset=PaymentMethod.objects.all(),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['is_invoice_need'] = forms.BooleanField(label="請求書オプション", required=False,)

class UpdateContractChangeStep1Form(forms.ModelForm):

    # start_day = forms.DateField(required=True, label="サービス利用開始日", widget=datetimepicker.DatePickerInput(format='%Y/%m/%d', options={'locale': 'ja', 'dayViewHeaderFormat': 'YYYY年 MMMM',}), input_formats=['%Y/%m/%d'])

    class Meta:
        model = Estimates
        # fields = ('start_day', 'plan', 'option')
        fields = ('start_day', 'plan', 'option1', 'option2', 'option3', 'option4', 'option5')


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.service_id = kwargs.pop('service_id')
        service = Service.objects.get(pk=self.service_id)
        super(UpdateContractChangeStep1Form, self).__init__(*args, **kwargs)

        self.fields['plan'] = forms.ModelChoiceField(label="プラン",
                                        widget=Plan_Radio_For_Estimate(attrs = {'user_id': self.user.id}),
                                        queryset=Plan.objects.filter(service=service, is_option=False, is_trial=False),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['option1'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'user_id': self.user.id}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="1").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option2'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'user_id': self.user.id}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="2").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option3'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'user_id': self.user.id}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="3").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option4'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'user_id': self.user.id}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="4").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option5'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Estimate(attrs = {'user_id': self.user.id}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="5").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

class UpdateContractChangeStep2Form(forms.ModelForm):
    # discount = forms.CharField(label="割引コード", required=False, max_length=10)

    class Meta:
        model = Estimates
        fields = ('method_payment', 'is_invoice_need')

    # def __init__(self, *args, **kwargs):
    #     self.total_price = kwargs.pop('total_price')
    #     super(UpdateContractChangeStep2Form, self).__init__(*args, **kwargs)
    #     self.fields['method_payment'] = forms.ModelChoiceField(label="支払い方法",
    #                                     widget=Payment_Radio_For_Estimate(attrs = {'total_price': self.total_price}),
    #                                     queryset=PaymentMethod.objects.all(),
    #                                     required=True,
    #                                     empty_label=None,
    #                                                 )
 
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        # self.contract_id = kwargs.pop('contract_id')

        super(UpdateContractChangeStep2Form, self).__init__(*args, **kwargs)
        self.fields['method_payment'] = forms.ModelChoiceField(label="支払い方法",
                                        widget=Payment_Radio_For_Estimate(attrs = {'user':self.user}),
                                        queryset=PaymentMethod.objects.all(),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['is_invoice_need'] = forms.BooleanField(label="請求書オプション", required=False,)