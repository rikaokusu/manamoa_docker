from django import template
register = template.Library()


@register.filter
def select_exclude(queryset, value):

    print("----------- value ----------", value)# 2be772f3-5a9b-4b1d-8f98-c2824971c8ab
    print("----------- queryset ----------", queryset)# <QuerySet [<Parts: テストファイル3>, <Parts: アンケート>, <Parts: テスト>]>

    # クエリセットからvalueのidに該当するパーツを除外
    parts_selects = queryset.exclude(id=value).order_by("order")

    return parts_selects