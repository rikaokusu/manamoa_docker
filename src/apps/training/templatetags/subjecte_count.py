from django import template
from training.models import Training, SubjectManagement
register = template.Library()

@register.filter
def subjecte_count(value, current_user):
    print("ばりゅー", value)
    print("ばりゅー current_user", current_user)
    subjecte_count = Training.objects.filter(subject=value).count()
    # subjecte_count = Training.objects.filter(subject=value, reg_user=current_user).count()
    print("-------------- subjecte_count", subjecte_count)

    return subjecte_count
