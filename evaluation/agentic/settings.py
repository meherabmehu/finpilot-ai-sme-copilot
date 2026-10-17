"""Development-only evaluation settings; never imported by a production entry point."""
import getpass
import os

from config.settings import *  # noqa: F403

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
LLM_API_KEY = ''
LLM_ENABLED = False
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

# Set only by the dev CLI after it creates a randomly named database itself.
if os.environ.get('FINPILOT_EVAL_DB_NAME', '').startswith('test_finpilot_agentic_'):
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql',
                            'NAME': os.environ['FINPILOT_EVAL_DB_NAME'],
                            'HOST': os.environ['FINPILOT_EVAL_DB_SOCKET'],
                            'PORT': os.environ['FINPILOT_EVAL_DB_PORT'], 'USER': getpass.getuser()}}
