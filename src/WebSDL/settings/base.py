"""
Django settings for WebSDL project.

Generated by 'django-admin startproject' using Django 1.9.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import json
import getpass
import logging

# Set application logging level
logging.basicConfig(level=logging.INFO)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Loads settings configuration data from settings.json file
data = {}
try:
    with open(os.path.join(BASE_DIR, 'WebSDL','settings', 'settings.json')) as data_file:
        data = json.load(data_file)
except IOError:
    print("You need to setup the settings data file (see instructions in base.py file.)")


# SECURITY WARNING: keep the secret key used in production secret!
try:
    SECRET_KEY = data["secret_key"]
except KeyError:
    print("The secret key is required in the settings.json file.")
    exit(1)

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    # 'debug_toolbar',
    'rest_framework',
    'accounts.apps.AccountsConfig',
    'dataloader.apps.DataloaderConfig',
    'dataloaderservices.apps.DataloaderservicesConfig',
    'dataloaderinterface.apps.DataloaderinterfaceConfig',
    'hydroshare',
    'leafpack',
    'streamwatch',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'requests',
    'reset_migrations',
    'timeseries_visualization'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'hydroshare_util.middleware.AuthMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django_cprofile_middleware.middleware.ProfilerMiddleware',
]

DJANGO_CPROFILE_MIDDLEWARE_REQUIRE_STAFF = False

REST_FRAMEWORK = {
   'DEFAULT_RENDERER_CLASSES': (
       'rest_framework.renderers.JSONRenderer',
       'rest_framework.renderers.BrowsableAPIRenderer',
#       'rest_framework.renderers.AdminRenderer',
   )
}

ROOT_URLCONF = 'WebSDL.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'hydroshare')]
        ,
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

#WSGI_APPLICATION = 'WebSDL.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {}
for database in data['databases']:
    DATABASES[database['name']] = {
        'ENGINE': database['engine'],
        'NAME': database['schema'],
        'USER': database['user'] if 'user' in database else '',
        'PASSWORD': database['password'] if 'password' in database else '',
        'HOST': database['host'] if 'host' in database else '',
        'PORT': database['port'] if 'port' in database else '',
        'OPTIONS': database['options'] if 'options' in database else {},
        'CONN_MAX_AGE': 0,
        'TEST': database['test'] if 'test' in database else {},
    }
DATAMODELCACHE = os.path.join(BASE_DIR, 'odm2', 'modelcache.pkl')

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
LOGIN_URL = '/login/'

# Security and SSL
#
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#
# SECURE_SSL_REDIRECT = True

RECAPTCHA_KEY = data["recaptcha_secret_key"] if "recaptcha_secret_key" in data else ""
RECAPTCHA_USER_KEY = data["recaptcha_user_key"] if "recaptcha_user_key" in data else ""
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

EMAIL_SENDER = data['email_from'] if 'email_from' in data else '',
NOTIFY_EMAIL = data['notify_email_sender'] if 'notify_email_sender' in data else ''
DEFAULT_FROM_EMAIL = EMAIL_SENDER[0] if isinstance(EMAIL_SENDER, tuple) else EMAIL_SENDER
NOTIFY_EMAIL_SENDER = NOTIFY_EMAIL[0] if isinstance(NOTIFY_EMAIL, tuple) else NOTIFY_EMAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_SERVER = data['email_host'] if 'email_host' in data else '',
EMAIL_HOST = EMAIL_SERVER[0] if isinstance(EMAIL_SERVER, tuple) else EMAIL_SERVER
EMAIL_PORT = data['email_port']
EMAIL_HOST_USER = data['email_username'] if 'email_username' in data else ''
EMAIL_HOST_PASSWORD = data['email_password'] if 'email_password' in data else ''
EMAIL_USE_TLS = True

DATETIME_FORMAT = "N j, Y g:i a"

HYDROSHARE_UTIL_CONFIG = {
    'CLIENT_ID': data["hydroshare_oauth"]["client_id"],
    'CLIENT_SECRET': data["hydroshare_oauth"]["client_secret"],
    'REDIRECT_URI': data['hydroshare_oauth']['redirect_uri']
}

# This data period is measured in days
SENSOR_DATA_PERIOD = data['sensor_data_period'] if 'sensor_data_period' in data else '2'

# crontab job settings
CRONTAB_USER = data.get('crontab_user', getpass.getuser())
CRONTAB_LOGFILE_PATH = data.get('crontab_log_file', '/var/log/odm2websdl-cron.log')
CRONTAB_EXECUTE_DAILY_AT_HOUR = 5

GOOGLE_API_CONF = data.get('google_api_conf', None)

AUTH_USER_MODEL = 'accounts.User'

#Static cache busting
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

DEBUG = True if 'debug_mode' in data and data['debug_mode'] == "True" else False
