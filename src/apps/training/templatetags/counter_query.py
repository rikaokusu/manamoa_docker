from django import template
register = template.Library()

@register.filter
def counter_query(qs,i):

    print("クエリーセット", qs)
    print("回したい数", i)


    # obj = qs.objects.all()[:i]
    # return obj

    for i in range(i):

        return qs