from django import template
from contracts.models import Contract
from datetime import datetime, date, timedelta, timezone
from dateutil.relativedelta import relativedelta
import pytz
# today = datetime.now(pytz.timezone('Asia/Tokyo'))

register = template.Library()

@register.filter
def onemonth_date(service,current_user):
    contract = Contract.objects.filter(service__name=service,company=current_user.company,status="2").first()
    today = datetime.now(timezone.utc)
    one_month = contract.contract_end_date - relativedelta(months=1)
    # 一ヶ月前はTrueを返す
    return one_month

