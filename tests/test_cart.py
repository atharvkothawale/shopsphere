def test_cart_empty_state(client):
    """Test cart page when no items have been added."""
    response = client.get('/cart/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Your Shopping Cart is Empty' in html


def test_add_to_cart_and_summary(client):
    """Test adding an item to the shopping cart and checking INR totals."""
    # Product ID 1: NovaPulse Pro Smartwatch (₹2,999)
    response = client.post('/cart/add/1', data={'quantity': 1}, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'NovaPulse Pro Smartwatch' in html
    assert '₹2,999' in html
    # Over ₹999 -> Free shipping
    assert 'FREE' in html
    assert '$' not in html


def test_cart_shipping_calculation_under_threshold(client):
    """Test cart shipping calculation when subtotal is under ₹999 threshold."""
    # Product ID 9: BaristaCraft Ceramic Pour-Over Dripper (₹749)
    client.post('/cart/add/9', data={'quantity': 1}, follow_redirects=True)
    response = client.get('/cart/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert '₹749' in html
    assert '₹49' in html  # Standard delivery fee under threshold
    assert 'more for FREE delivery!' in html
    assert '$' not in html


def test_cart_update_quantity(client):
    """Test updating product quantity in the cart with proper INR arithmetic."""
    # Add product 1 (₹2,999) with quantity 1
    client.post('/cart/add/1', data={'quantity': 1}, follow_redirects=True)
    # Update quantity to 3
    response = client.post('/cart/update/1', data={'quantity': 3}, follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Cart updated successfully.' in html
    # Subtotal: 3 * 2999 = 8,997
    assert '₹8,997' in html
    assert '$' not in html


def test_cart_remove_item(client):
    """Test removing an individual item from the cart."""
    client.post('/cart/add/1', data={'quantity': 1}, follow_redirects=True)
    response = client.post('/cart/remove/1', follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Item removed from your cart.' in html
    assert 'Your Shopping Cart is Empty' in html


def test_cart_clear(client):
    """Test clearing all items from the cart."""
    client.post('/cart/add/1', data={'quantity': 1}, follow_redirects=True)
    client.post('/cart/add/2', data={'quantity': 2}, follow_redirects=True)
    response = client.post('/cart/clear', follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Shopping cart cleared.' in html
    assert 'Your Shopping Cart is Empty' in html
def test_add_to_cart_with_zero_quantity_adds_one_item(client):
    """Adding a product with quantity zero should default to one item."""
    response = client.post(
        '/cart/add/1',
        data={'quantity': 0},
        follow_redirects=True
    )

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert session['cart']['1'] == 1