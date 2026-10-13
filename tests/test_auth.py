import pytest
from app.db import get_db
from werkzeug.security import check_password_hash


def get_csrf_token(client, page_url='/login'):
    """Helper to fetch a page and retrieve the session CSRF token."""
    client.get(page_url)
    with client.session_transaction() as sess:
        return sess.get('_csrf_token')


def test_login_and_register_pages_render(client):
    """1. Login and registration pages render successfully."""
    login_resp = client.get('/login')
    assert login_resp.status_code == 200
    assert 'Sign In' in login_resp.get_data(as_text=True)

    reg_resp = client.get('/register')
    assert reg_resp.status_code == 200
    assert 'Create Your Account' in reg_resp.get_data(as_text=True)


def test_successful_registration(client, app):
    """2. Successful account registration."""
    token = get_csrf_token(client, '/register')
    resp = client.post('/register', data={
        'csrf_token': token,
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert 'Account created successfully' in resp.get_data(as_text=True)

    with app.app_context():
        user = get_db().execute("SELECT * FROM users WHERE email = 'testuser@example.com'").fetchone()
        assert user is not None
        assert user['name'] == 'Test User'


def test_duplicate_email_rejection(client):
    """3. Duplicate email rejection."""
    token = get_csrf_token(client, '/register')
    client.post('/register', data={
        'csrf_token': token,
        'name': 'Original User',
        'email': 'duplicate@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })

    token2 = get_csrf_token(client, '/register')
    dup_resp = client.post('/register', data={
        'csrf_token': token2,
        'name': 'Copy User',
        'email': 'duplicate@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })
    assert dup_resp.status_code == 409
    assert 'already exists' in dup_resp.get_data(as_text=True)


def test_invalid_email_rejection(client):
    """4. Invalid email rejection."""
    token = get_csrf_token(client, '/register')
    resp = client.post('/register', data={
        'csrf_token': token,
        'name': 'Invalid Email User',
        'email': 'not-an-email',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })
    assert resp.status_code == 400
    assert 'valid email address' in resp.get_data(as_text=True)


def test_password_confirmation_mismatch(client):
    """5. Password confirmation mismatch."""
    token = get_csrf_token(client, '/register')
    resp = client.post('/register', data={
        'csrf_token': token,
        'name': 'Mismatch User',
        'email': 'mismatch@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'DifferentPassword2026!'
    })
    assert resp.status_code == 400
    assert 'Passwords do not match' in resp.get_data(as_text=True)


def test_password_hashes_stored_not_plaintext(client, app):
    """6. Password hashes are stored instead of plaintext passwords."""
    raw_pass = 'SuperSecurePass2026!'
    token = get_csrf_token(client, '/register')
    client.post('/register', data={
        'csrf_token': token,
        'name': 'Hash Check User',
        'email': 'hashcheck@example.com',
        'password': raw_pass,
        'confirm_password': raw_pass
    })

    with app.app_context():
        user = get_db().execute("SELECT * FROM users WHERE email = 'hashcheck@example.com'").fetchone()
        assert user is not None
        assert user['password_hash'] != raw_pass
        assert check_password_hash(user['password_hash'], raw_pass) is True


def test_successful_login(client):
    """7. Successful login with valid credentials and cart persistence."""
    # Pre-add item to cart
    client.post('/cart/add/1', data={'quantity': 2})
    with client.session_transaction() as sess:
        assert sess.get('cart', {}).get('1') == 2

    # Register user
    token = get_csrf_token(client, '/register')
    client.post('/register', data={
        'csrf_token': token,
        'name': 'Login User',
        'email': 'loginuser@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })

    # Log in
    token2 = get_csrf_token(client, '/login')
    login_resp = client.post('/login', data={
        'csrf_token': token2,
        'email': 'loginuser@example.com',
        'password': 'StrongPassword2026!'
    }, follow_redirects=True)

    assert login_resp.status_code == 200
    assert 'Welcome back, Login User' in login_resp.get_data(as_text=True)

    # Verify session and cart persistence
    with client.session_transaction() as sess:
        assert sess.get('user_name') == 'Login User'
        assert sess.get('cart', {}).get('1') == 2


def test_invalid_login_credentials(client):
    """8. Invalid login credentials."""
    token = get_csrf_token(client, '/login')
    resp = client.post('/login', data={
        'csrf_token': token,
        'email': 'nonexistent@example.com',
        'password': 'WrongPassword123!'
    })
    assert resp.status_code == 401
    assert 'Invalid email or password' in resp.get_data(as_text=True)


def test_account_access_unauthenticated(client):
    """9. Account access without authentication redirects to login."""
    resp = client.get('/account')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']
    assert 'next=%2Faccount' in resp.headers['Location'] or 'next=/account' in resp.headers['Location']


def test_account_access_authenticated(client):
    """10. Account access with authentication renders dashboard."""
    # Register & Login
    token = get_csrf_token(client, '/register')
    client.post('/register', data={
        'csrf_token': token,
        'name': 'Account Member',
        'email': 'accountmember@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })

    token2 = get_csrf_token(client, '/login')
    client.post('/login', data={
        'csrf_token': token2,
        'email': 'accountmember@example.com',
        'password': 'StrongPassword2026!'
    })

    resp = client.get('/account')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'Account Member' in html
    assert 'accountmember@example.com' in html
    assert 'Profile Information' in html


def test_successful_logout(client):
    """11. Successful logout and session invalidation while preserving cart."""
    # Add cart item
    client.post('/cart/add/1', data={'quantity': 1})

    # Register & Login
    token = get_csrf_token(client, '/register')
    client.post('/register', data={
        'csrf_token': token,
        'name': 'Logout User',
        'email': 'logoutuser@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })
    token2 = get_csrf_token(client, '/login')
    client.post('/login', data={
        'csrf_token': token2,
        'email': 'logoutuser@example.com',
        'password': 'StrongPassword2026!'
    })

    with client.session_transaction() as sess:
        assert sess.get('user_id') is not None
        assert sess.get('cart', {}).get('1') == 1

    # Logout via POST with CSRF
    logout_token = get_csrf_token(client, '/account')
    logout_resp = client.post('/logout', data={'csrf_token': logout_token}, follow_redirects=True)
    assert logout_resp.status_code == 200

    # User ID must be cleared, cart must remain
    with client.session_transaction() as sess:
        assert sess.get('user_id') is None
        assert sess.get('cart', {}).get('1') == 1


def test_csrf_validation(client):
    """12. CSRF validation rejects missing or invalid tokens."""
    # Missing CSRF token
    resp_missing = client.post('/register', data={
        'name': 'No CSRF',
        'email': 'nocsrf@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })
    assert resp_missing.status_code == 400

    # Invalid CSRF token
    client.get('/login')
    resp_invalid = client.post('/login', data={
        'csrf_token': 'tampered-csrf-token-12345',
        'email': 'someone@example.com',
        'password': 'StrongPassword2026!'
    })
    assert resp_invalid.status_code == 400


def test_login_throttling(client):
    """13. Login throttling engages after consecutive failed attempts."""
    target_email = 'throttle_target@example.com'

    # Make 5 failed attempts
    for _ in range(5):
        token = get_csrf_token(client, '/login')
        resp = client.post('/login', data={
            'csrf_token': token,
            'email': target_email,
            'password': 'WrongPassword123!'
        })
        assert resp.status_code == 401

    # 6th attempt should be throttled (HTTP 429)
    token = get_csrf_token(client, '/login')
    throttled_resp = client.post('/login', data={
        'csrf_token': token,
        'email': target_email,
        'password': 'WrongPassword123!'
    })
    assert throttled_resp.status_code == 429
    assert 'Too many failed login attempts' in throttled_resp.get_data(as_text=True)


def test_api_auth_me(client):
    """API endpoint /api/auth/me returns status according to session."""
    # Unauthenticated
    resp_unauth = client.get('/api/auth/me')
    assert resp_unauth.status_code == 200
    assert resp_unauth.get_json()['authenticated'] is False

    # Register & Login
    token = get_csrf_token(client, '/register')
    client.post('/register', data={
        'csrf_token': token,
        'name': 'API Member',
        'email': 'apimember@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })
    token2 = get_csrf_token(client, '/login')
    client.post('/login', data={
        'csrf_token': token2,
        'email': 'apimember@example.com',
        'password': 'StrongPassword2026!'
    })

    resp_auth = client.get('/api/auth/me')
    assert resp_auth.status_code == 200
    data = resp_auth.get_json()
    assert data['authenticated'] is True
    assert data['user']['name'] == 'API Member'
    assert data['user']['email'] == 'apimember@example.com'
    assert 'password_hash' not in data['user']


def test_first_login_then_shop_enforcement(client, app):
    """Verify that when REQUIRE_LOGIN_TO_SHOP is enabled, unauthenticated users must login first."""
    app.config['REQUIRE_LOGIN_TO_SHOP'] = True

    # 1. Homepage shows 'Login to Shop' buttons for unauthenticated visitors
    home_resp = client.get('/')
    assert home_resp.status_code == 200
    assert 'Login to Shop' in home_resp.get_data(as_text=True)

    # 2. Attempting to add product to cart redirects to login
    add_resp = client.post('/cart/add/1', data={'quantity': 1})
    assert add_resp.status_code == 302
    assert '/login' in add_resp.headers['Location']

    # 3. Attempting to access checkout redirects to login
    checkout_resp = client.get('/checkout')
    assert checkout_resp.status_code == 302
    assert '/login' in checkout_resp.headers['Location']

    # 4. Once logged in, user can add to cart and shop normally
    token = get_csrf_token(client, '/register')
    client.post('/register', data={
        'csrf_token': token,
        'name': 'Shopper User',
        'email': 'shopper@example.com',
        'password': 'StrongPassword2026!',
        'confirm_password': 'StrongPassword2026!'
    })
    token2 = get_csrf_token(client, '/login')
    client.post('/login', data={
        'csrf_token': token2,
        'email': 'shopper@example.com',
        'password': 'StrongPassword2026!'
    })

    # Now add to cart succeeds
    logged_in_add = client.post('/cart/add/1', data={'quantity': 1}, follow_redirects=True)
    assert logged_in_add.status_code == 200
    assert 'Added NovaPulse Pro Smartwatch to your cart!' in logged_in_add.get_data(as_text=True)

