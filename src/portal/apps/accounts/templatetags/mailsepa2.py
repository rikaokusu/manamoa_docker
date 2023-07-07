from django import template
import datetime

register = template.Library()

@register.filter
def mailsepa2(email):
    email_list = email.split('@')
    elength = len(email_list[0])
    email_slice1 = (email_list[0][0:3])
    email_slice2 = (email_list[0][3:])
    email_domain = email_list[1].split('.')
    domain_count = len(email_domain)

    hana = '********'
    
    if elength <= 3:
        if domain_count == 3:
            email_part =  email_list[0] + hana + '@' + hana + '.' + email_domain[1] + email_domain[2]
        elif domain_count == 4:
            email_part =  email_list[0] + hana + '@' + hana + '.' + email_domain[2] + email_domain[3]
        elif domain_count == 5:
            email_part =  email_list[0] + hana + '@' + hana + '.' + email_domain[3] + email_domain[4]
        else:
            email_part =  email_list[0] + hana + '@' + hana + '.' + email_domain[1]
    else:
        if domain_count == 3:
            email_part = email_slice1 + hana + "@" + hana + '.' + email_domain[1] + email_domain[2]
        elif domain_count == 4:
            email_part = email_slice1 + hana + "@" + hana + '.' + email_domain[2] + email_domain[3]
        elif domain_count == 5:
            email_part = email_slice1 + hana + "@" + hana + '.' + email_domain[3] + email_domain[4]
        else:
            email_part = email_slice1 + hana + '@' + hana + '.' + email_domain[1]

    return email_part
