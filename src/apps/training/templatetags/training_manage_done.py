from django import template
from training.models import Training, TrainingManage

register = template.Library()

@register.filter
def training_manage_done(value):
    print("------------ value", value)# トレーニングA

    training_manage_count = TrainingManage.objects.filter(training=value).count()
    print("------------ training_manage_count", training_manage_count)

    training_manage_done_count = TrainingManage.objects.filter(training=value, status=3).count()
    print("------------ training_manage_done_count", training_manage_done_count)

    if training_manage_count == training_manage_done_count:
        return True
    else:
        return False