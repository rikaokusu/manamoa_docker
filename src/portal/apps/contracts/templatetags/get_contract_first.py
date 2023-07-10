# from django import template
# from contracts.models import Contract, Plan, PaymentMethod, Estimates

# register = template.Library()

# #1はなし
# #
# #
# #
# #

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
