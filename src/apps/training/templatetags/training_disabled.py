from django import template
from training.models import TrainingManage, Training
# 時刻取得
from datetime import datetime, timedelta
# import datetime
import pytz

utc=pytz.UTC

register = template.Library()


@register.filter
def training_disabled(value):

    # print("----------- value 1 ----------", value)# 削除用トレーニング
    # print("----------- value 2 ----------", value.start_date)# 2022-06-14 04:44:26+00:00

    # 今日の日付を取得
    today = datetime.now().replace(tzinfo=utc)
    # print("----------- today", today)# 2022-06-27 16:18:29.543330

    current_datetime = today.replace(tzinfo=utc)
    # print("----------- current_datetime", current_datetime)

    start_date = value.start_date.replace(tzinfo=utc)
    # print("----------- start_date", start_date)

    # start_dateが今日より後の場合
    if start_date > current_datetime:
        # print("----------- True ----------")

        return True

    else:
        # print("----------- false ----------")

        return False