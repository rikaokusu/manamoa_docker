from django import template
import datetime

register = template.Library()
tody = datetime.date.today()

@register.filter
def get_contract_status(queryset, current_user):
    # contracts1 = queryset.filter(company=current_user.company,status="2").first()
    # contracts2 = queryset.filter(company=current_user.company).first()

    # if contracts1:
    #     return contracts1.status
    # elif contracts2:
    #     return contracts2.status

    # else:
    #     return None


    #試用中
    contracts1 = queryset.filter(company=current_user.company,status="1").first()
    #契約中
    contracts2 = queryset.filter(company=current_user.company,status="2").first()
    #解約
    contracts3 = queryset.filter(company=current_user.company,status="3").first()
    #更新済
    contracts4 = queryset.filter(company=current_user.company,status="4").first()

    if contracts2:
        print('こんとらくつ契約中',contracts2)
        return contracts2.status
    elif contracts1 or contracts3 or contracts4:
        if contracts3 and tody < contracts3.contract_end_date.date():
            print('こんとらくつ3',contracts3)
            return contracts3.status
        elif contracts1 and tody < contracts1.contract_end_date.date():
            print('こんとらくつ1',contracts1)
            return contracts1.status
        elif contracts4:
            print('こんとらくつ４',contracts4)
            return contracts4.status
        else:
            status = "5"
            print('こんとらくつ５')
            return status
    else:
        print('こんとらくつなーーす')
        return None
