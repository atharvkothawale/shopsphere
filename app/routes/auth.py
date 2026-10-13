import re
import secrets
import time
from collections import defaultdict
from functools import wraps
from threading import Lock
from urllib.parse import urlparse

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

auth_bp = Blueprint('auth', __name__)

# In-memory login throttling tracker: key -> {'count': int, 'lock_until': float}
_login_lock = Lock()
_login_attempts = defaultdict(lambda: {'count': 0, 'lock_until': 0.0})

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes lockout

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')


# ------------------- Security Helpers -------------------

def generate_csrf_token():
    """Generate or retrieve a cryptographically secure CSRF token for the session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf():
    """Verify submitted CSRF token against current session token."""
    if not current_app.config.get('CSRF_ENABLED', True):
        return True
    token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    expected = session.get('_csrf_token')
    if not expected or not token or not secrets.compare_digest(str(expected), str(token)):
        return False
    return True


def is_safe_url(target):
    """Ensure target redirect URL is internal and safe from open redirect vulnerabilities."""
    if not target:
        return False
    if target.startswith('//') or '\\' in target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and not parsed.scheme and target.startswith('/')


def is_throttled(email, ip):
    """Check if login attempts for (email, ip) exceed maximum allowed threshold."""
    key = f"{email}:{ip}"
    with _login_lock:
        data = _login_attempts[key]
        now = time.time()
        if data['lock_until'] > now:
            return True, int(data['lock_until'] - now)
        elif data['lock_until'] > 0 and data['lock_until'] <= now:
            data['count'] = 0
            data['lock_until'] = 0.0
        return False, 0


def record_failed_attempt(email, ip):
    """Increment failed login counter and engage lockout if threshold reached."""
    key = f"{email}:{ip}"
    with _login_lock:
        data = _login_attempts[key]
        data['count'] += 1
        if data['count'] >= MAX_ATTEMPTS:
            data['lock_until'] = time.time() + LOCKOUT_SECONDS


def clear_attempts(email, ip):
    """Reset failed attempts on successful login."""
    key = f"{email}:{ip}"
    with _login_lock:
        if key in _login_attempts:
            del _login_attempts[key]


def login_required(view):
    """Decorator to require authenticated session before viewing a page."""
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session or not g.user:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return view(**kwargs)
    return wrapped_view


# ------------------- Authentication Routes -------------------

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User account registration with strict input and password validation."""
    if 'user_id' in session and g.user:
        return redirect(url_for('auth.account'))

    if request.method == 'POST':
        if not validate_csrf():
            abort(400, description="Invalid or missing CSRF token.")

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        if not name or len(name) < 2 or len(name) > 100:
            errors.append("Please enter your full name (2–100 characters).")

        if not email or not EMAIL_REGEX.match(email) or len(email) > 120:
            errors.append("Please enter a valid email address.")

        if not password or len(password) < 12:
            errors.append("Password must be at least 12 characters long.")

        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('register.html', name=name, email=email), 400

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("An account with this email address already exists. Please log in.", "warning")
            return render_template('register.html', name=name, email=email), 409

        password_hash = generate_password_hash(password)
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        db.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with brute-force rate limiting and session rotation."""
    if 'user_id' in session and g.user:
        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('auth.account'))

    if request.method == 'POST':
        if not validate_csrf():
            abort(400, description="Invalid or missing CSRF token.")

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        ip = request.remote_addr or '127.0.0.1'

        throttled, wait_sec = is_throttled(email, ip)
        if throttled:
            flash(f"Too many failed login attempts. Please wait {wait_sec} seconds before trying again.", "danger")
            return render_template('login.html', email=email), 429

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template('login.html', email=email), 400

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        if user is None or not check_password_hash(user['password_hash'], password):
            record_failed_attempt(email, ip)
            flash("Invalid email or password.", "danger")
            return render_template('login.html', email=email), 401

        # Successful authentication: clear throttle records
        clear_attempts(email, ip)

        # Preserve shopping cart items across session regeneration
        cart_data = session.get('cart', {})
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['cart'] = cart_data
        session['_csrf_token'] = secrets.token_hex(32)

        flash(f"Welcome back, {user['name']}!", "success")

        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        return redirect(url_for('auth.account'))

    return render_template('login.html')


@auth_bp.route('/account')
@login_required
def account():
    """Protected user account dashboard displaying profile details and order history."""
    db = get_db()
    # Fetch orders associated with this user's email
    user_orders = db.execute(
        "SELECT * FROM orders WHERE customer_email = ? ORDER BY id DESC",
        (g.user['email'],)
    ).fetchall()

    return render_template('account.html', user=g.user, orders=user_orders)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out current user, preserve cart items, and terminate authenticated session."""
    if not validate_csrf():
        abort(400, description="Invalid or missing CSRF token.")

    cart_data = session.get('cart', {})
    session.clear()
    session['cart'] = cart_data
    session['_csrf_token'] = secrets.token_hex(32)

    flash("You have been logged out successfully.", "info")
    return redirect(url_for('catalog.index'))


@auth_bp.route('/api/auth/me')
def me():
    """Minimal endpoint returning authenticated user identity (excludes password hash)."""
    if 'user_id' in session and g.user:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": g.user['id'],
                "name": g.user['name'],
                "email": g.user['email'],
                "created_at": g.user['created_at']
            }
        }), 200
    return jsonify({
        "authenticated": False,
        "user": None
    }), 200
