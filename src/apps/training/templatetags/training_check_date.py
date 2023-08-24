from django import template
# from datetime import datetime, timedelta
import datetime
import pytz

utc=pytz.UTC

register = template.Library()

@register.filter
def training_check_date(date):
# def training_check_date(value):

    # print("----------- value", value)# 2022-06-29 23:32:14+00:00
    # print("----------- date 1", date)
    # print(type(date))

    # 日時を日付に変換する
    date = date.date()
    # print("----------- date aaaaa", date)
    # print(type(date))

    # 今日の日付を取得
    today = datetime.date.today()# 2022-07-01
    # print("----------- today", today)
    # print(type(today))

    # 試用期間終了前の場合はTrueを返す
    return today > date
    # return today < date
