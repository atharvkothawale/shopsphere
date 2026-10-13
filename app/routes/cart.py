from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app, g
from app.db import get_db

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


def get_cart_summary():
    """Calculates cart items, quantities, subtotal, shipping, tax, and grand total."""
    cart = session.get('cart', {})
    if not cart:
        return {
            'items': [],
            'subtotal': 0.0,
            'shipping': 0.0,
            'tax': 0.0,
            'total': 0.0,
            'total_items': 0
        }

    db = get_db()
    product_ids = [int(pid) for pid in cart.keys() if pid.isdigit()]
    
    if not product_ids:
        session['cart'] = {}
        return {
            'items': [],
            'subtotal': 0.0,
            'shipping': 0.0,
            'tax': 0.0,
            'total': 0.0,
            'total_items': 0
        }

    placeholders = ','.join(['?'] * len(product_ids))
    products = db.execute(
        f"""
        SELECT p.*, c.name AS category_name
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.id IN ({placeholders})
        """,
        product_ids
    ).fetchall()

    items = []
    subtotal = 0.0
    total_items = 0

    for prod in products:
        pid_str = str(prod['id'])
        quantity = int(cart.get(pid_str, 1))
        item_total = round(prod['price'] * quantity, 2)
        subtotal += item_total
        total_items += quantity
        items.append({
            'product': prod,
            'quantity': quantity,
            'subtotal': item_total
        })

    subtotal = round(subtotal, 2)
    shipping = 0.0 if (subtotal == 0 or subtotal >= 999.0) else 49.0
    tax = round(subtotal * 0.05, 2)
    total = round(subtotal + shipping + tax, 2)

    return {
        'items': items,
        'cart_items': items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
        'total_items': total_items
    }


@cart_bp.route('/')
def view_cart():
    """Display shopping cart page with item list and order calculations."""
    cart_summary = get_cart_summary()
    return render_template('cart.html', cart=cart_summary)


@cart_bp.route('/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add a product to the cart or increment its quantity."""
    if current_app.config.get('REQUIRE_LOGIN_TO_SHOP', True):
        if 'user_id' not in session or not getattr(g, 'user', None):
            flash("Please log in first to shop and add products to your cart.", "warning")
            return redirect(url_for('auth.login', next=request.referrer or url_for('catalog.index')))

    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    
    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for('catalog.index'))

    qty = request.form.get('quantity', 1, type=int)
    if qty <= 0:
        qty = 1

    cart = session.get('cart', {})
    pid_str = str(product_id)
    cart[pid_str] = cart.get(pid_str, 0) + qty
    session['cart'] = cart
    session.modified = True

    flash(f"Added {product['name']} to your cart!", "success")
    
    next_url = request.form.get('next') or request.referrer or url_for('cart.view_cart')
    return redirect(next_url)


@cart_bp.route('/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    """Update the quantity of a cart item."""
    qty = request.form.get('quantity', 1, type=int)
    cart = session.get('cart', {})
    pid_str = str(product_id)

    if qty <= 0:
        cart.pop(pid_str, None)
        flash("Item removed from your cart.", "info")
    else:
        cart[pid_str] = qty
        flash("Cart updated successfully.", "success")

    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove a product completely from the cart."""
    cart = session.get('cart', {})
    pid_str = str(product_id)
    
    if pid_str in cart:
        cart.pop(pid_str)
        session['cart'] = cart
        session.modified = True
        flash("Item removed from your cart.", "info")

    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    """Clear all items from the cart."""
    session['cart'] = {}
    session.modified = True
    flash("Shopping cart cleared.", "info")
    return redirect(url_for('cart.view_cart'))
