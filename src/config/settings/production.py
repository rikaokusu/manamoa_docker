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
#         'NAME': 'training',
#         'USER': 'yuitech',
#         'PASSWORD': 'password',
#         # 'HOST': 'localhost',
#         'HOST': 'db', # docker-compose.ymlで定義した名前と同じにする必要があります。
#         'PORT': '3306',
#     }
# }

DATABASES = {
    # まなもあの設定
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'training',
        'USER': 'yuitech',
        'PASSWORD':'password',
        'HOST':'db_manamoa',# docker-compose.ymlで設定した名前を設定
        'PORT': '3306',
    },
    # ポータルの設定 ※ポータルで認証を行う場合に必要
    'user': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'portal',
        # 'NAME': 'CLportal_db',
        'USER': 'yuitech',
        'PASSWORD': 'password',
        # 'HOST': '127.0.0.1',
        'HOST': 'db',
        # 'PORT': '3313',
        'PORT': '3306',
    }

}

# # Static files (CSS, JavaScript, Images)
# # https://docs.djangoproject.com/en/2.1/howto/static-files/

# STATIC_URL = '/static/'

# # collectstaticで集められるディレクトリ。Nginxの指定と合わせる
# # STATIC_ROOT = '/usr/share/nginx/html/static'
STATIC_ROOT = '/static/'


# # アプリケーションに紐付かない静的ファイルの置き場所（プロジェクト直下のstaticディレクトリを示す）
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]


# MEDIA_URL = '/media/'

# # ファイルがアップロードされるディレクトリ。Nginxの指定と合わせる
# # MEDIA_ROOT = '/usr/share/nginx/html/media'
# MEDIA_ROOT = '/media/'

# # ファイル削除用にパスを作成
# FULL_MEDIA_ROOT = os.path.join(MEDIA_ROOT, 'uploads')

# # ファイルアップロード時のパーミッションを設定
# FILE_UPLOAD_PERMISSIONS = 0o644

# # ファイルアップロードのハンドラー
# FILE_UPLOAD_HANDLERS = [
#     'django.core.files.uploadhandler.MemoryFileUploadHandler',
#     'django.core.files.uploadhandler.TemporaryFileUploadHandler',
# ]

# DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440
# # メモリー上にストリームするまでのしきい値。これ以上のファイルはTEMP_DIRを使う
# FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440
# # アップロード時に使われる一時フォルダ
# FILE_UPLOAD_TEMP_DIR = '/tmp'

# # 動画ファイル削除用にパスを作成 FULL_MEDIA_ROOT(C:\Users\user\Dropbox\08.開発\training_pj\media\uploads)
# MOVIE_FULL_MEDIA_ROOT = os.path.join(FULL_MEDIA_ROOT, 'movie')

# # 那覇庁舎内のSMTPサーバ
# EMAIL_HOST = '172.24.1.66' #10.5.5.90
# EMAIL_PORT = 25
# EMAIL_HOST_USER = '' # アカウント
# EMAIL_HOST_PASSWORD = '' # パスワード
# EMAIL_USE_TLS = False
# EMAIL_FROM_ADDRESS = 'training-admin@city.naha.lg.jp'
# DEFAULT_FROM_EMAIL = 'training-admin@city.naha.lg.jp'


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
#             'level': 'DEBUG',
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


# 以下、ポータルで認証を行うための設定をdocker化前のまなもあから移植

# 利用するRouter, manage.pyから見ての相対パス
DATABASE_ROUTERS = [
    'routers.AuthRouter',
]

DATABASE_APPS_MAPPING = {
    # defaultには管理系のTable
    'admin'              : 'user',
    'auth'               : 'user',
    'contenttypes'       : 'user',
    'sessions'           : 'user',
    'messages'           : 'default',
    'staticfiles'        : 'default',
    # 'django_celery_beat' : 'default',
    # userにはユーザー系処理
    'accounts'          : 'user',
    'bulk'              : 'user',
    # defaultには契約関連のTable
    'training'         : 'default',
}

STATIC_URL = '/static/'

# アプリケーションに紐付かない静的ファイルの置き場所（プロジェクト直下のstaticディレクトリを示す）
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# プロジェクト直下にmediaフォルダが作成される BASE_DIR(C:\Users\user\Dropbox\08.開発\training_pj)
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ファイル削除用にパスを作成 MEDIA_ROOT(C:\Users\user\Dropbox\08.開発\training_pj\media)
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
