from django import template

register = template.Library()

@register.filter
def postsepa(postcode):
    post_code1 = postcode[:3]
    post_code2 = postcode[4:]
    
    p_code = post_code1 + '-' + post_code2

    return p_code
