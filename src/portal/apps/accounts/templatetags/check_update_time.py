from django import template
from datetime import datetime,timezone
from dateutil.relativedelta import relativedelta
register = template.Library()

@register.filter
def check_update_time(lasttime):
    now = datetime.now(timezone.utc)
    arrowtime =  lasttime + relativedelta(minutes=3)
    # 試用期間終了前の場合はTrueを返す
    return arrowtime < now