from django import template
register = template.Library()

@register.filter
def get_user_name(email,domain):
    # メールアドレスをユーザ名とドメインに分割
    email_list = email.rsplit('@', 1)

    subdomain = email_list[1].replace(domain, '')

    # サブドメインがある場合の処理
    if subdomain :
        # サブドメインについているドットを削除して結合
        user_name = email_list[0] + "@" + subdomain[:-1]

    # サブドメインがない場合の処理
    else:
        user_name = email_list[0]

    return user_name
