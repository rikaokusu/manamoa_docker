from django import template
from training.models import Training, TrainingRelation, UserCustomGroupRelation

register = template.Library()

@register.filter
def get_training_status_waiting(queryset, value):

    # トレーニングを取得
    training = Training.objects.filter(id=value).first()
    # print("------------- training", training)

    # トレーニングに紐づいているグループを取得
    # groups = training.destination_group.all()
    groups = TrainingRelation.objects.filter(training_id=training.id)

    # グループをリスト化
    group_list = []
    group_lists_raw = list(groups.values_list('group_id', flat=True))
    # IDをstrに直してリストに追加
    for group_uuid in group_lists_raw:
        group_uuid_string = str(group_uuid)
        group_list.append(group_uuid_string)
    print("---------- group_list ---------", group_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

    group_users = UserCustomGroupRelation.objects.filter(group_id__in=group_list)
    print("---------- group_users ---------", group_users)

    # グループに所属するユーザーをリスト化
    group_user_list = []
    group_user_lists_raw = list(group_users.values_list('group_user', flat=True))
    # IDをstrに直してリストに追加
    for group_user_uuid in group_user_lists_raw:
        group_user_uuid_string = str(group_user_uuid)
        group_user_list.append(group_user_uuid_string)
    print("---------- group_user_list ---------", group_user_list)# ['6a9faafb-3fd8-4a2e-a096-9d1327b4397c', '76d54969-96ad-4485-ac02-e38612d5c070']

    # # グループをリスト化
    # group_lists = []
    # for group in groups:
    #     # グループに所属しているユーザーを取り出す
    #     for group_user in group.group_user.all():
    #         # リストにユーザーのIDを追加
    #         group_lists.append(group_user.pk)

    # set()で重複しているユーザーをリストから除外する
    # group_list = list(set(group_lists))
    group_user_list = list(set(group_user_list))

    # リスト内のIDをUUIDの文字列表現に変更
    # user_id_list = [str(o) for o in group_list]
    user_id_list = [str(o) for o in group_user_list]

    # トレーニングの各ステータス数を取得
    # training_manages_mitaiou = training.training_manage.filter(status=1).count()
    training_manages_mitaiou = training.training_manage.filter(status="1", user__in=user_id_list).count()

    print("------------- 未対応", training_manages_mitaiou)

    return training_manages_mitaiou
