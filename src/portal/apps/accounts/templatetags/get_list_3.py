from django import template

register = template.Library()

@register.filter
def get_list_3(queryset, nam):

    if nam == "option1":
        option = queryset.filter(category=1).first()
        if option:
            return 1
        else:
            return 0

    elif nam == "option2":
        option = queryset.filter(category=2).first()
        if option:
            return 1
        else:
            return 0

    elif nam == "option3":
        option = queryset.filter(category=3).first()
        if option:
            return 1
        else:
            return 0

    elif nam == "option4":
        option = queryset.filter(category=4).first()
        if option:
            return 1
        else:
            return 0    

    else:
        option = queryset.filter(category=5).first()
        if option:
            return 1
        else:
            return 0