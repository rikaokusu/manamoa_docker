from django import template
from training.models import Training, SubjectManagement
register = template.Library()

@register.filter
def exclude_training(value):
    print("--------------- ばりゅー", value)

    # subjectes = SubjectManagement.objects.filter(subject_reg_training=value).first()
    # print("subjectes", subjectes)

    # return subjectes
    return value