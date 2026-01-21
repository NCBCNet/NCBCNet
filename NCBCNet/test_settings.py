"""
Test settings for NCBCNet project.
Inherits from main settings but uses SQLite for testing.
"""
from .settings import *

# Use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable debug mode for tests
DEBUG = False

# Disable SSL redirect for tests
SECURE_SSL_REDIRECT = False

# Disable CSRF and session cookie secure for tests
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Disable HSTS for tests
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Use simple password hashers for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()
