from django import template
from training.models import ControlConditions, PartsManage, Parts
register = template.Library()


@register.filter
def btn_activate_ctl(value, current_user):
    # print("----------- value 1 ----------", value)# テストファイル3
    # print("----------- value 2 ----------", value.btn_activate_ctl)# True
    # print("----------- ユーザー ----------", current_user)# ユーザー / user@user.com


    # ボタン有効化制御がTrueの場合
    if value.btn_activate_ctl:
        # print("----------- True ----------")

        # 依存先をチェックする
        # controlconditions = ControlConditions.objects.filter(parts_origin=value)
        controlconditions = ControlConditions.objects.filter(parts_destination=value)
        # print("----------- 依存先 1 ----------", controlconditions)# <QuerySet [<ControlConditions: ControlConditions object (70)>]>

        parts_status_list = []

        for controlcondition in controlconditions:

            # PartsManageからログインしているユーザーの依存元を取得
            user_parts_manages = PartsManage.objects.filter(user=current_user.id, parts=controlcondition.parts_origin)
            # print("------ parts_manage ------", user_parts_manages)

            for user_parts_manage in user_parts_manages:

                # 依存先のステータスをリストに追加
                parts_status_list.append(user_parts_manage.status)

        # print("------ parts_status_list ------" ,parts_status_list)

        # 依存先が1つだけの場合
        if controlconditions.count() == 1:

            # print("------ 一つだけ ------")

            # ステータスが完了していた場合
            if parts_status_list:
                if parts_status_list[0] == 3:

                    # ボタンのdisabledが無効になる
                    return False

                else:
                    return True
            else:
                return True


        # 依存先が複数あった場合
        else:
            # print("----- 複数 -----")
            # リストの中に完了ステータス(=3)が2個あった場合
            if parts_status_list.count(3) == 2:
                return False
            else:
                return True

        # return True

    else:
        # print("----------- false ----------")

        return False