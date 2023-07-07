from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         # 'ENGINE': 'django.db.backends.sqlite3',
#         # 'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'portal',
#         'USER': 'yuitech',
#         'PASSWORD': 'VMS0ghMrGB<x',
#         'HOST': '192.168.2.24',
#         'PORT': '3306',
#     }
# }

#appのコンテナ構築時に設定したDBの設定情報を反映させる
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'CLportal_db',
        'USER': 'yuitech',
        'PASSWORD': 'password',
        'HOST': 'db',
        'PORT': '3306',
    }
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_ROOT = '/static/'
STATIC_URL = '/static/'

# STATIC_ROOT = '/usr/share/nginx/html/static'

# アプリケーションに紐付かない静的ファイルの置き場所（プロジェクト直下のstaticディレクトリを示す）
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# プロジェクト直下にmediaフォルダが作成される
# MEDIA_ROOT = '/usr/share/nginx/html/media'
MEDIA_ROOT = '/media/'

# アップロードファイルにはFQDN+/media/+uploads+ファイル名でアクセスする
MEDIA_URL = '/media/'

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'local': {
#             'format': '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(message)s'
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'formatter': 'local',
#         },
#     },
#     'loggers': {
#         # 自作したログ出力
#         '': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         # Djangoのエラー・警告・開発WEBサーバのアクセスログ
#         'django': {
#             'handlers': ['console'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#         # 実行SQL
#         'django.db.backends': {
#             'handlers': ['console'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#     }
# }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(module)s %(process)d %(thread)d %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        '': {
            'level': DEBUG,
            'handlers': ['console',],
        },
    },
}

