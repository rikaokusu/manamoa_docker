from django import template
from training.models import Training, SubjectManagement
register = template.Library()

@register.filter
def get_subject(value):
    # print("------------- get_subject", value)

    trainings = Training.objects.filter(subject=value)
    # print("-------------------- trainings", trainings)

    return trainings
