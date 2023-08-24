from django import template
import re
register = template.Library()

@register.filter
def split_name(value):
    # print("------------ value", value)# ('宮城 花子', UUID('e05943a9-9a9f-40c0-ace3-b809cce911ca'))

    new_value_1 = value.split(',')[3]
    # print("------------ new_value 111", new_value_1)# ('cc4f2f79-7bb9-4418-8bc8-d4cbc075ddef'), 'group_user')

    new_value_2 = new_value_1.replace("'", "").replace("(", "").replace(")", "").replace(" ", "")# cc4f2f79-7bb9-4418-8bc8-d4cbc075ddef, group_user
    # new_value_2 = new_value_1.replace("'", "").replace("UUID", "")
    # new_value_2 = new_value_1.replace("UUID", "")
    # print("------------ new_value 2222", new_value_2)

    # new_value_3 = re.sub("[()]","", new_value_2)
    new_value_3 = new_value_2.split(',')[1:]
    # print("------------ new_value 3333", new_value_3)# ['group_guest_user']

    # new_value_4 = [item.replace("'", "").replace("[", "").replace("]", "").replace(" ", "")  for item in new_value_3]
    # print("------------ new_value 44444", new_value_4)

    return new_value_2