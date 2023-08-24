from django import template
from training.models import Training, TrainingManage, User

register = template.Library()

@register.filter
def get_user_status(queryset, value):

    # current_user = User.objects.filter(pk=value.user)
    print("----------- ユーザー1 ----------", value)# ユーザー / user@user.com

    # training = Training.objects.filter(id=value).first()

    # user_manage = training.training_manage.filter(user=current_user).first()
    # print("-----------------------ユーザー2", user_manage.user)
    # print("-----------------------ステータス", user_manage.status)


    return value
    # return user_manage.status