from django import template
from contracts.models import Contract, Plan, PaymentMethod, Estimates

register = template.Library()

#契約一覧画面で初回申込み時の契約書を表示
@register.filter
def get_contract_first(contract,current_user):
    if contract.status == '1':
        return None
    else:
        old_estimate = Estimates.objects.filter(service=contract.service,user__company=current_user.company,is_signed=True).order_by('start_day').first()
        return old_estimate