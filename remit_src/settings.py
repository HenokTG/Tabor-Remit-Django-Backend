import os
import environ
from pathlib import Path

import dj_database_url
import django_heroku

# Initialise environment variables
env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DJANGO_DEBUG", False)

# NGROK is used exposes local server port [8000] to the Internet to recieve paypal webhook response
ALLOWED_HOSTS = ["tabor-remit-backend.herokuapp.com",
                 "f2d9-197-156-103-213.eu.ngrok.io", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = [
    "https://tabor-remit-backend.herokuapp.com", "http://localhost:3000", "https://f2d9-197-156-103-213.eu.ngrok.io"]

CORS_ORIGIN_ALLOW_ALL = True

# Application definition
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
THIRD_PARTY_APPS = [
    'corsheaders',
    'rest_framework',
]

LOCAL_APPS = [
    'agent_api',
    'remit_api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'remit_src.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'remit_src.wsgi.application'


# Database

db_config = dj_database_url.config(
    default=env('DATABASE_URL'))
db_config['ATOMIC_REQUESTS'] = True

DATABASES = {
    'default': db_config,
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_psycopg2',
#         'NAME': env('DATABASE_NAME'),
#         'USER': env('DATABASE_USER'),
#         'PASSWORD': env('DATABASE_PASS'),
#         'HOST': env('DATABASE_HOST'),
#         'PORT': env('DATABASE_PORT'),
#     }
# }


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Addis_Ababa'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Enable WhiteNoise's GZip compression of static assets.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Agent profile Image upload location helper function
UPLOAD_TO_OPTIONS = {
    "black_listed_extensions": ["php", "html", "htm", "js", "vbs", "py", "pyc", "asp", "aspx", "pl"],
    "max_filename_length": 40,
    "file_name_template": "{model_name}/%Y/%m/%d/{instance.agent_name}.{extension}"
}

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = "agent_api.AgentProfile"

# REST FRAMEWORK SETTEINGS
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}

# PayPal Settings ...REMEMBER TO HIDE THIS IN ENVIRONMENT VARIEABLE WHEN DEPLOY OR COMMIT
PAYPAL_CLIENT_ID = env("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = env("PAYPAL_CLIENT_SECRET")
PAYPAL_WEBHOOK_ID = env("PAYPAL_WEBHOOK_ID")

# Configure Django App for Heroku.
django_heroku.settings(locals())
