from .base import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': 'training',
    #     'USER': 'yuitech',
    #     'PASSWORD': 'password',
    #     'HOST': '127.0.0.1',
    #     'PORT': '3316',
    # },

    'default': {
        # 'ENGINE': 'django.db.backends.sqlite3',
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'training',
        'USER': 'yuitech',
        'PASSWORD': 'password',
        'HOST': '127.0.0.1',
        'PORT': '3316',
    },


}

# 利用するRouter, manage.pyから見ての相対パス
# DATABASE_ROUTERS = [
#     'routers.AuthRouter',
# ]

# アプリケーションごとの接続先DBのマッピング
# DATABASE_APPS_MAPPING = {
#     # defaultには管理系のTable
#     'admin'              : 'default',
#     'auth'               : 'default',
#     'contenttypes'       : 'default',
#     'sessions'           : 'default',
#     'messages'           : 'default',
#     'staticfiles'        : 'default',
#     'django_celery_beat' : 'default',
#     # userにはユーザー系処理
#     'accounts'          : 'user',
#     'bulk'              : 'user',
#     # defaultには契約関連のTable
#     'contracts'         : 'default',
# }

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

# アプリケーションに紐付かない静的ファイルの置き場所（プロジェクト直下のstaticディレクトリを示す）
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# プロジェクト直下にmediaフォルダが作成される
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ファイル削除用にパスを作成
FULL_MEDIA_ROOT = os.path.join(MEDIA_ROOT, 'uploads')

# 動画ファイル削除用にパスを作成 FULL_MEDIA_ROOT(C:\Users\user\Dropbox\08.開発\training_pj\media\uploads)
MOVIE_FULL_MEDIA_ROOT = os.path.join(FULL_MEDIA_ROOT, 'movie')

# アップロードファイルにはFQDN+/media/+uploads+ファイル名でアクセスする
MEDIA_URL = '/media/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'local': {
            'format': '%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'local',
        },
    },
    'loggers': {
        # 自作したログ出力
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        # Djangoのエラー・警告・開発WEBサーバのアクセスログ
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        # 実行SQL
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
