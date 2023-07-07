from django.contrib import admin
from .models import Payment

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_paymented', 'method_payment', 'created_date', 'pay_count', 'stripe_plan')
    list_display_links = ('user',)

    # def _payjp_option(self, row):
    #     return ','.join([x.name for x in row.payjp_option.all()])


admin.site.register(Payment, PaymentAdmin,)