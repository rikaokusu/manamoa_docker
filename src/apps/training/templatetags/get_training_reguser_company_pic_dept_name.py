from django import template
from accounts.models import User
register = template.Library()

@register.filter
def get_training_reguser_company_pic_dept_name(value):
    # print("------------- val", value)

    reg_user = User.objects.filter(id=value).first()
    # print("-------------------- reg_user", reg_user)

    return reg_user.company.pic_dept_name