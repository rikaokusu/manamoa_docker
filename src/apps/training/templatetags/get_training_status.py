from django import template
from training.models import Training

register = template.Library()

@register.filter
def get_training_status(queryset, value):
    training = Training.objects.filter(id=value).first()
    obj = queryset.filter(training=training).first()
    if obj:
        return obj.get_status_display

    # obj = queryset.filter(training=training).order_by('status')
    # if obj:
    #     return obj

