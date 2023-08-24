from django.apps import AppConfig
import os
from django.conf import settings


class AccountsConfig(AppConfig):
    name = 'accounts'
    path = os.path.join(settings.BASE_DIR, 'accounts')
