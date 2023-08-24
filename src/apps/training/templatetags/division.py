from django import template
register = template.Library()

@register.filter
def division(list):
    # Falseがlistに何個含まれているかを調べる=リスト.count(値)
    # cnt = arg.count(value)

    # # リストの中の合計
    # arg = sum(arg)

    # # 結果 = Falseの数 ÷ TrueとFalseの合計
    # result = int(value) / int(arg)

    result = sum(list) - list.count("False")
    return result