import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'shopsphere-devops-secret-key-2026')
    DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'instance', 'shopsphere.db'))
    TESTING = False
    
    # Session Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() in ('true', '1')
    
    # CSRF Protection
    CSRF_ENABLED = True

    # Shop Authentication Policy: Require login before shopping
    REQUIRE_LOGIN_TO_SHOP = os.environ.get('REQUIRE_LOGIN_TO_SHOP', 'true').lower() in ('true', '1')


class TestingConfig(Config):
    TESTING = True
    DATABASE = ':memory:'
    CSRF_ENABLED = True
    REQUIRE_LOGIN_TO_SHOP = os.environ.get('REQUIRE_LOGIN_TO_SHOP', 'false').lower() in ('true', '1')


