"""
MatChatX - Django Settings
Real-time ephemeral match-based chat system.

All sensitive credentials managed via .env file.
"""

import os
from pathlib import Path
from decouple import config, Csv

# =============================================================================
# BASE CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    # Daphne MUST be before django.contrib.staticfiles
    "daphne",
    # Django core
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    # Third-party
    "channels",
    "corsheaders",
    # Local apps
    "matches",
    "chat",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

# =============================================================================
# DATABASE (PostgreSQL - Match metadata ONLY, no chat messages)
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================

REDIS_HOST = config("REDIS_HOST", default="localhost")
REDIS_PORT = config("REDIS_PORT", default=6379, cast=int)
REDIS_DB = config("REDIS_DB", default=0, cast=int)
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CHANNEL_REDIS_URL = config("CHANNEL_REDIS_URL", default="redis://localhost:6379/1")

# =============================================================================
# DJANGO CHANNELS (ASGI + WebSocket)
# =============================================================================

ASGI_APPLICATION = "core.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [CHANNEL_REDIS_URL],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}

# =============================================================================
# CORS CONFIGURATION (for frontend clients)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# =============================================================================
# CHAT CONFIGURATION
# =============================================================================

CHAT_MAX_MESSAGES = config("CHAT_MAX_MESSAGES", default=15, cast=int)
MATCH_BUFFER_MINUTES = config("MATCH_BUFFER_MINUTES", default=30, cast=int)

# =============================================================================
# RATE LIMITING
# =============================================================================

RATE_LIMIT_MESSAGES = config("RATE_LIMIT_MESSAGES", default=10, cast=int)
RATE_LIMIT_WINDOW_SECONDS = config("RATE_LIMIT_WINDOW_SECONDS", default=10, cast=int)

# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# DEFAULT AUTO FIELD
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "matchatx.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "chat": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "matches": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "django.channels": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
