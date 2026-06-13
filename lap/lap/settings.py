from pathlib import Path
import os
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
ALLOWED_HOSTS += [
    'lap-b9vi.onrender.com',
    '.onrender.com',
    'localhost',
    '127.0.0.1',
    '100.121.237.45',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'corsheaders',

    # Local apps
    'accounts',
    'employees',
    'leave',
    'attendance',
    'payroll',
    'utils',
    'reports',
    'notifications',
    'support_tickets',
    'affiliate',
    'leads',
    'tasks',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lap.urls'

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

WSGI_APPLICATION = 'lap.wsgi.application'

if os.getenv('LAP_USE_LOCAL_SQLITE', 'False') == 'True':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.getenv('SQLITE_DB_NAME', 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE'),
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
            'OPTIONS': {
                'ssl': {'ca': None},
            },
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==========================
# CORS & CSRF
# ==========================

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://100.121.237.45:5173',
    'https://lap-phi.vercel.app',
    'https://lapsystem.vercel.app',
    'http://100.104.235.68:5173',
    'http://100.85.146.60:5173'
]

_frontend = os.getenv('FRONTEND_URL', '')
if _frontend and _frontend not in CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS.append(_frontend)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = list(default_headers) + [
    'x-tenant',
    'x-tenant-code',
    'x-authorization',
    'x-auth-token',
    'x-access-token',
    'x-java-token',
    'x-java-permissions',
    'x-java-modules',
    'x-java-role',
    'x-java-user-id',
    'x-java-user-email',
    'x-user-email',
    'x-role',
]

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://100.121.237.45:5173',
    'https://lap-phi.vercel.app',
    'https://lapsystem.vercel.app',
    'https://lap-b9vi.onrender.com',
    'http://100.104.235.68:5173',
    'http://100.85.146.60:5173/'
]

# ==========================
# Django REST Framework
# ==========================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'utils.java_auth.JavaTokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# ==========================
# Java Auth Bridge
# ==========================

JAVA_JWT_SECRET = os.getenv(
    'JAVA_JWT_SECRET',
    'mysecretkeymysecretkeymysecretkey12345',
)

JAVA_AUTH_BASE_URL = os.getenv(
    'JAVA_AUTH_BASE_URL',
    'http://100.85.146.60:8080/api/auth',
)

JAVA_API_BASE_URL = os.getenv(
    'JAVA_API_BASE_URL',
    'http://100.85.146.60:8080',
)

JAVA_USERS_PATHS = [
    value.strip()
    for value in os.getenv(
        'JAVA_USERS_PATHS',
        'api/users,api/auth/users,users,api/user',
    ).split(',')
    if value.strip()
]

LAP_TRUST_TENANT_HEADER_AUTH = os.getenv(
    'LAP_TRUST_TENANT_HEADER_AUTH',
    'True' if DEBUG else 'False',
) == 'True'

LAP_ALLOW_UNVERIFIED_JAVA_JWT = os.getenv(
    'LAP_ALLOW_UNVERIFIED_JAVA_JWT',
    'True' if DEBUG else 'False',
) == 'True'

# ==========================
# Affiliate Settings
# ==========================

AFFILIATE_COMMISSION_RATE = float(
    os.getenv('AFFILIATE_COMMISSION_RATE', '0.10')
)

AFFILIATE_MIN_PAYOUT_AMOUNT = float(
    os.getenv('AFFILIATE_MIN_PAYOUT_AMOUNT', '500')
)

AFFILIATE_PAYMENT_MODE = os.getenv(
    'AFFILIATE_PAYMENT_MODE',
    'manual'
)
