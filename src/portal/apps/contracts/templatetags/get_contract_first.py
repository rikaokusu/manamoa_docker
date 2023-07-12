from django import template
from contracts.models import Contract, Plan, PaymentMethod, Estimates

register = template.Library()

#契約一覧画面で初回申込み時の契約書を表示
# 1:なし（試用）
# 2:当契約、または初回契約書
# 3:当契約、または以前の契約書
# 4:当契約、または以前の契約書

@register.filter
def get_contract_first(contract,current_user):
    if contract.status == '1':
        return None
    else:
        old_estimate = Estimates.objects.filter(service=contract.service,user__company=current_user.company,is_signed=True).order_by('start_day').first()
        print('おーるどえすてぃめいと',old_estimate)
        return old_estimate
            

    # contract_estimate = contracts.estimate.filter(estimates_id=estimate.id)
    # print('こんとらくとえすてぃめいと',contract_estimate)
    # contract2 = Contract.objects.get(pk=contract_estimate.contract_id)
    # print('関連する見積りと契約',contract)
    # if contract2:
    #     return contract2.status
    # else:
    #     return None

# @register.filter
# def get_contract_first(contract):
#     contracts = Contract.objects.all()

    # contract_estimate = contracts.estimate.filter(estimates_id=estimate.id)
    # print('こんとらくとえすてぃめいと',contract_estimate)
    # contract2 = Contract.objects.get(pk=contract_estimate.contract_id)
    # print('関連する見積りと契約',contract)
    # if contract2:
    #     return contract2.status
    # else:
    #     return None
