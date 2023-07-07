from django import template
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta
import pytz
register = template.Library()

@register.filter
def is_oneweekago(date):
    today = datetime.now(timezone.utc)
    one_week_ago = date - relativedelta(weeks=1)
    # 一ヶ月前はTrueを返す
    return one_week_ago < today
