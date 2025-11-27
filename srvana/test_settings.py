"""
Test settings for technician verification workflow tests
Uses SQLite for faster test execution and avoids PostgreSQL setup issues
"""
import os
from .settings import *

# Use SQLite for testing - much faster than PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations during tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
TESTING = True

# Disable logging during tests
LOGGING_CONFIG = None
LOGGING = {
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'CRITICAL',
    },
}

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable email backend during tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use local file storage for tests instead of Cloudinary
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Test timeout (some tests may take time to set up)
TEST_TIMEOUT = 300
