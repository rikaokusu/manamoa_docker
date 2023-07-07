from django.contrib import admin
from contracts.models import Contract, Plan, Discount


class ContractAdmin(admin.ModelAdmin):
    list_display = ('user', 'service', 'plan', 'status', 'contract_start_date', 'contract_end_date', 'pay_start_date', 'pay_end_date', 'minor_total', 'tax', 'total', 'is_autocheckout', 'is_invoice_need',)
    list_display_links = ('user', 'service', 'status', 'contract_start_date', 'contract_end_date', 'pay_start_date', 'pay_end_date',)


class PlanAdmin(admin.ModelAdmin):
    list_display = ('is_option', 'is_trial', 'service', 'category', 'stripe_plan_id', 'name', 'price', 'unit_price', 'user_num', 'description', 'layout')
    list_display_links =('stripe_plan_id', 'name', 'price', 'user_num', 'description', 'layout')

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'coupon_code', 'coupon_id', 'discount_type', 'discount_rate', 'expiration_date', 'limit', 'limit_all', 'target','payment')
    list_display_links =('name', 'coupon_code', 'coupon_id', 'discount_type', 'discount_rate', 'expiration_date', 'limit', 'limit_all', 'target','payment')

admin.site.register(Contract, ContractAdmin,)
admin.site.register(Plan, PlanAdmin,)
admin.site.register(Discount, DiscountAdmin,)
