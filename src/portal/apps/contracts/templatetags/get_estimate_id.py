from django import template
from contracts.models import Contract, Plan, PaymentMethod, Estimates

register = template.Library()

@register.filter
def get_estimate_id(queryset, current_user):

    estimate1 = Estimates.objects.filter(user=current_user,is_use=1).values_list('service_id',flat=True)

    estimate = queryset.filter(user__company=current_user.company).first()
    
    if estimate:
        return estimate.service_id
    elif estimate1:
        return estimate1
    else:
        return 0

    

