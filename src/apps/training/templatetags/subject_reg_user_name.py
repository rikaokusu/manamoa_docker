from django import template
from accounts.models import User
from training.models import Training, SubjectManagement
register = template.Library()

@register.filter
def subject_reg_user_name(value):

    subject_reg_user_name = User.objects.filter(id=value).first()
    # print("subject_reg_user_name", subject_reg_user_name)

    return subject_reg_user_name
