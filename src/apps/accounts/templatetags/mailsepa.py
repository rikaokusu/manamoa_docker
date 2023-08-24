from django import template
import datetime

register = template.Library()

@register.filter
def mailsepa(email):
    email_list = email.split('@')
    elength = len(email_list[0]) 
    email_slice1 = (email_list[0][0:3])
    email_slice2 = (email_list[0][3:])
    hana = elength -3 
    
    if elength <= 3:
        email_part =  email_list[0] + '@' + email_list[1]
    elif elength > 3:
        email_slice2 = "*" * hana
        email_part = email_slice1 + email_slice2 + "@" + email_list[1]

    return email_part
