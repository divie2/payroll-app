from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import timedelta
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # local apps
    "account",
    "employee",

    # 3rd party app
    "rest_framework",
    "rest_framework_simplejwt",
    "django_celery_beat"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "payroll.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "payroll.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv('DB_NAME'),
        "USER": os.getenv('DB_USER'),
        "PASSWORD": os.getenv('DB_PASSWORD'),
        "HOST": 'payroll-db',
        "PORT": "5432",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Lagos"

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"



REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "NON_FIELD_ERRORS_KEY": "errors",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "30/minute", "user": "70/minute"},
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 5,
    "EXCEPTION_HANDLER": "account.perms.custom_exception_handler",
     'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}

AUTH_USER_MODEL = 'account.Account'
PARALLEL_RATE_WEB_LINK = os.getenv("PARALLEL_RATE_WEB_LINK")
F_300000=os.getenv("F_300000")
N_300000=os.getenv("N_300000")
N_500000=os.getenv("N_500000")
NF_500000=os.getenv("NF_500000")
N_1600000=os.getenv("N_1600000")
A_3200000=os.getenv("A_3200000")
TRANSPORT_ALLOWANCE_RATE=os.getenv("transport_allowance_rate")
HOUSING_ALLOWANCE_RATE=os.getenv("housing_allowance_rate")
PENSION = os.getenv("pension")
NHF = os.getenv("nhf")
CRA = os.getenv("CRA")
TOP_CRA = os.getenv("top_cra")
OFFICIAL_RATE_WEB_LINK = os.getenv("OFFICIAL_RATE_WEB_LINK")
OPEN_EXCHANGE_API_KEY = os.getenv("OPEN_EXCHANGE_API_KEY")
RATE_GEN_DAY=os.getenv("RATE_GEN_DAY")
NATIONAL_MINIMUM_WAGE = os.getenv("national_minimum_wage")
ABOVE_CHARGE_TAX_AMOUNT = os.getenv("above_charge_tax_amount")


PASSWORD_RESET_TIMEOUT = 3600
EMAIL_USE_TLS = True
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT"))
EMAIL_USE_SSL = False

CELERY_BROKER_URL = "redis://payroll-redis:6379/0"
CELERY_RESULT_BACKEND = "redis://payroll-redis:6379/0"
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'verbose': {
#             'format': '{levelname} {asctime} {module} {message}',
#             'style': '{',
#         },
#         'simple': {
#             'format': '{levelname} {message}',
#             'style': '{',
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'simple',
#         },
#         'file': {
#             'level': 'WARNING',
#             'class': 'logging.FileHandler',
#             'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
#             'formatter': 'verbose',
#         },
#         'rotating_file': {
#             'level': 'WARNING',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
#             'maxBytes': 1024*1024*5,  # 5 MB
#             'backupCount': 3,
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console', 'rotating_file'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'account': {
#             'handlers': ['console', 'rotating_file'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         'employee': {
#             'handlers': ['console', 'rotating_file'],
#             'level': 'DEBUG',
#             'propagate': False,
#         },
#         'django.db.backends': {
#             'level': 'WARNING',
#             'level': 'ERROR',
#             'propagate': False,
#         },
#     },
# }

CSRF_TRUSTED_ORIGINS = ["https://a60f-102-89-75-182.ngrok-free.app", "https://real.ec2.alluvium.net"]