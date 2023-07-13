from django import forms
from contracts.models import Contract
from django.conf import settings
from accounts.models import User, Company, Service
from contracts.models import Estimates, Plan, Contract, PaymentMethod, Discount
from payment.models import Payment
from django.db.models import Prefetch
"""
プラン変更用ラジオボックス
"""
class Plan_Radio_For_Payment(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'payment/forms/widget/plan_radio.html'

    def get_context(self, name, value, attrs):

            context = super(Plan_Radio_For_Payment, self).get_context(name, value, attrs)
            contract = Contract.objects.filter(pk=self.attrs['contract']).first()
            plans = Plan.objects.filter(is_trial=False, is_option=False).values('id', 'price')
            plan_price_dict = [entry for entry in plans]
            context['contract'] = contract
            context['plan_price_dict'] = plan_price_dict

            return context

"""
見積書のオプション選択用ラジオボックス
"""
class Option_Radio_For_Payment(forms.RadioSelect):
    input_type = 'radio'
    template_name = 'payment/forms/widget/option_radio.html'

    def get_context(self, name, value, attrs):
            context = super(Option_Radio_For_Payment, self).get_context(name, value, attrs)
            contract = Contract.objects.filter(pk=self.attrs['contract']).first()
            c_list = []

            # if contract.option1:
            #     c_option1 = Plan.objects.filter(pk=contract.option1.id).values('id', 'price', 'category')
            #     c_options.append(c_option1)
            # if contract.option2:
            #     c_option2 = Plan.objects.filter(pk=contract.option2.id).values('id', 'price', 'category')
            #     c_options.append(c_option2)
            # if contract.option3:
            #     c_option3 = Plan.objects.filter(pk=contract.option3.id).values('id', 'price', 'category')
            #     c_options.append(c_option3)
            # if contract.option4:
            #     c_option4 = Plan.objects.filter(pk=contract.option4.id).values('id', 'price', 'category')
            #     c_options.append(c_option4)
            # if contract.option5:
            #     c_option5 = Plan.objects.filter(pk=contract.option5.id).values('id', 'price', 'category')
            #     c_options.append(c_option5)

            #現在選択中のオプションリスト
            if contract.option1:
                c_list.append(contract.option1.id)
            if contract.option2:
                c_list.append(contract.option2.id)
            if contract.option3:
                c_list.append(contract.option3.id)
            if contract.option4:
                c_list.append(contract.option4.id)
            if contract.option5:
                c_list.append(contract.option5.id)

            c_optioin_list = Plan.objects.filter(pk__in=c_list)

            plans = Plan.objects.filter(is_trial=False, is_option=True).values('id', 'price', 'category')
            plans_cat_list = Plan.objects.filter(is_trial=False, is_option=True).order_by("name").values_list('category', flat=True)
            plan_price_dict = [entry for entry in plans]
            # plans_cat_dict = [entry for entry in plans_list]
            context['contract'] = contract
            context['plans_cat_list'] = list(plans_cat_list)
            context['plan_price_dict'] = plan_price_dict
            context['c_options_dict'] = c_optioin_list
            # context['plan'] = plan

            return context


"""
プランを変更するフォーム
"""
class ChangeContractForm(forms.ModelForm):

    class Meta:
        model = Contract
        fields = ('plan', 'option1', 'option2', 'option3', 'option4','option5')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.contract = kwargs.pop('contract')
        super(ChangeContractForm, self).__init__(*args, **kwargs)

        contract = Contract.objects.filter(pk=self.contract).first()
        service = Service.objects.get(id=contract.service_id)

        #self.service_id = kwargs.pop('service_id')

        #service = Service.objects.get(pk=self.service_id)

        self.fields['plan'] = forms.ModelChoiceField(label="プラン",
                                        widget=Plan_Radio_For_Payment(attrs = {'user_id': self.user.id,'contract': self.contract}),
                                        queryset=Plan.objects.filter(service=service, is_option=False, is_trial=False).order_by('layout'),
                                        required=True,
                                        empty_label=None,
                                                    )

        self.fields['option1'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Payment(attrs = {'user_id': self.user.id,'contract': self.contract}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="1").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option2'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Payment(attrs = {'user_id': self.user.id,'contract': self.contract}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="2").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option3'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Payment(attrs = {'user_id': self.user.id,'contract': self.contract}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="3").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option4'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Payment(attrs = {'user_id': self.user.id,'contract': self.contract}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="4").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )

        self.fields['option5'] = forms.ModelChoiceField(label="オプション",
                                        widget=Option_Radio_For_Payment(attrs = {'user_id': self.user.id,'contract': self.contract}),
                                        queryset=Plan.objects.filter(service=service, is_option=True, is_trial=False, category="5").order_by('layout'),
                                        required=False,
                                        empty_label = 'なし',
                                                    )