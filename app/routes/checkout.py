import re
import uuid
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app, g
from app.db import get_db
from app.routes.cart import get_cart_summary

checkout_bp = Blueprint('checkout', __name__)


def generate_order_number():
    """Generates a unique, friendly order tracking identifier."""
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"SS-{date_str}-{random_suffix}"


def validate_checkout_form(data):
    """Validates customer checkout inputs and returns list of error messages."""
    errors = []
    name = data.get('customer_name', '').strip()
    email = data.get('customer_email', '').strip()
    phone = data.get('customer_phone', '').strip()
    address = data.get('shipping_address', '').strip()

    if not name or len(name) < 2:
        errors.append("Please provide a valid full name (at least 2 characters).")

    email_regex = r"^[^@]+@[^@]+\.[^@]+$"
    if not email or not re.match(email_regex, email):
        errors.append("Please provide a valid email address.")

    if not phone or len(phone) < 7:
        errors.append("Please provide a valid phone number (at least 7 digits).")

    if not address or len(address) < 5:
        errors.append("Please provide a complete shipping address (at least 5 characters).")

    return errors


@checkout_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Handle demo checkout process: form validation, order creation, and cart persistence."""
    if current_app.config.get('REQUIRE_LOGIN_TO_SHOP', True):
        if 'user_id' not in session or not getattr(g, 'user', None):
            flash("Please log in first to proceed to checkout.", "warning")
            return redirect(url_for('auth.login', next=url_for('checkout.checkout')))

    cart_summary = get_cart_summary()
    
    if not cart_summary['items']:
        flash("Your shopping cart is empty. Add products to continue.", "warning")
        return redirect(url_for('cart.view_cart'))

    if request.method == 'POST':
        form_data = {
            'customer_name': request.form.get('customer_name', '').strip(),
            'customer_email': request.form.get('customer_email', '').strip(),
            'customer_phone': request.form.get('customer_phone', '').strip(),
            'shipping_address': request.form.get('shipping_address', '').strip(),
            'payment_method': request.form.get('payment_method', 'Demo Pay on Delivery')
        }

        errors = validate_checkout_form(form_data)
        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('checkout.html', cart=cart_summary, form_data=form_data)

        # Create Order in SQLite
        db = get_db()
        order_number = generate_order_number()
        total_amount = cart_summary['total']

        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO orders (order_number, customer_name, customer_email, customer_phone, shipping_address, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, 'CONFIRMED')
            """,
            (
                order_number,
                form_data['customer_name'],
                form_data['customer_email'],
                form_data['customer_phone'],
                form_data['shipping_address'],
                total_amount
            )
        )
        order_id = cursor.lastrowid

        # Insert Order Items
        for item in cart_summary['items']:
            prod = item['product']
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, product_name, unit_price, quantity, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    prod['id'],
                    prod['name'],
                    prod['price'],
                    item['quantity'],
                    item['subtotal']
                )
            )

        db.commit()

        # Clear session cart
        session['cart'] = {}
        session.modified = True

        flash(f"Order #{order_number} placed successfully!", "success")
        return redirect(url_for('checkout.order_confirmation', order_number=order_number))

    initial_form_data = {}
    if getattr(g, 'user', None):
        initial_form_data = {
            'customer_name': g.user['name'],
            'customer_email': g.user['email']
        }

    return render_template('checkout.html', cart=cart_summary, form_data=initial_form_data)


@checkout_bp.route('/order/confirmation/<order_number>')
def order_confirmation(order_number):
    """Display final order receipt, items purchased, and delivery details."""
    db = get_db()
    
    order = db.execute(
        "SELECT * FROM orders WHERE order_number = ?",
        (order_number,)
    ).fetchone()

    if not order:
        abort(404)

    items = db.execute(
        """
        SELECT oi.*, p.image_url, p.slug
        FROM order_items oi
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
        """,
        (order['id'],)
    ).fetchall()

    return render_template('order_confirmation.html', order=order, items=items)
