from django import template
register = template.Library()

@register.filter
def get_contract_id(queryset, current_user):
    # print('かれんとゆーざー',current_user.company)
    contract1 = queryset.filter(user__company=current_user.company,status="2").first()

    contract2 = queryset.filter(user__company=current_user.company).first()
    if contract1:
        return contract1.id
    elif contract2:
        return contract2.id

    else:
        return None

