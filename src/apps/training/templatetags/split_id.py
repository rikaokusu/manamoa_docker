from django import template
import re
register = template.Library()

@register.filter
def split_id(value):
    # print("------------ value id切り取り", value)# ('玉城 太郎', '65961@test.jp', UUID('cc4f2f79-7bb9-4418-8bc8-d4cbc075ddef'), 'group_user')
    # print("------------ value type", type(value))# <class 'str'>

    new_value_1 = value.split(',')[2]
    # new_value_1 = value.split('UUID')[1]
    # print("------------ new_value 1", new_value_1)# ('cc4f2f79-7bb9-4418-8bc8-d4cbc075ddef'), 'group_user')

    # new_value_1_5 = new_value_1.split(',')[:-1]
    # print("------------ new_value 1.5", new_value_1_5)# ["('cc4f2f79-7bb9-4418-8bc8-d4cbc075ddef')"]

    new_value_2 = new_value_1.replace("'", "").replace("(", "").replace(")", "").replace("UUID", "").replace(" ", "")# cc4f2f79-7bb9-4418-8bc8-d4cbc075ddef, group_user
    # new_value_2 = new_value_1.replace("'", "").replace("UUID", "")
    # new_value_2 = new_value_1.replace("UUID", "")
    # print("------------ new_value 2", new_value_2)

    # new_value_3 = re.sub("[()]","", new_value_2)
    new_value_3 = new_value_2.split(',')[:-1]
    # print("------------ new_value 3", new_value_3)

    # new_value_4 = new_value_3.strip()
    new_value_4 = [item.replace("'", "").replace("[", "").replace("]", "") for item in new_value_3]
    # print("------------ new_value 4", new_value_4)


    return new_value_2