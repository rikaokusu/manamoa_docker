from django import template
from datetime import datetime, date
register = template.Library()

@register.filter
def check_for_expiration_date(value):
    # print("------------1", value)# 2023-01-31 02:53:37+00:00

    ExpirationDate = datetime.strftime(value, '%Y-%m-%d')
    # print("------------2", ExpirationDate)#2023-01-31
    # print("------------2 type", type(ExpirationDate))# <class 'str'>

    # 今日の日付を取得
    now_1 = datetime.now()
    now = datetime.strftime(now_1, "%Y-%m-%d")
    # print("------------3 now", now)# 2023-01-12
    # print("------------3 now type", type(now))# <class 'str'>

    if ExpirationDate >= now:
        result = True
    else:
        result = False

    return result