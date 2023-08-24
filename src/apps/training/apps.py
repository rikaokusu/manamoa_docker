from django.apps import AppConfig
import os
from django.conf import settings


class TrainingConfig(AppConfig):
    name = 'training'
    path = os.path.join(settings.BASE_DIR, 'training')
