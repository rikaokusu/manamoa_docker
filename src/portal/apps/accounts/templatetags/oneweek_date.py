from django import template
from contracts.models import Estimates
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta
import pytz
# today = datetime.now(pytz.timezone('Asia/Tokyo'))

register = template.Library()

@register.filter
def oneweek_date(num):
    estimate = Estimates.objects.filter(num=num).first()
    today = datetime.now(timezone.utc)
    one_month = estimate.expiration_date - relativedelta(weeks=1)
    # 一ヶ月前はTrueを返す
    return one_month

