from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from db import get_db
from auth import login_required
from datetime import date

bp = Blueprint('orders', __name__)

@bp.route('/')
@bp.route('/menu')
@login_required
def menu():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM categories ORDER BY display_order")
        categories = cur.fetchall()
        cur.execute("SELECT * FROM menu_items WHERE is_available = TRUE")
        items = cur.fetchall()
    return render_template('menu.html', categories=categories, items=items)

@bp.route('/cart', methods=('GET', 'POST'))
@login_required
def cart():
    cart_data = session.get('cart', {})
    db = get_db()
    items = []
    total = 0.0

    if cart_data:
        ids = list(cart_data.keys())
        format_strings = ','.join(['%s'] * len(ids))
        with db.cursor() as cur:
            cur.execute(f"SELECT * FROM menu_items WHERE item_id IN ({format_strings})", ids)
            db_items = cur.fetchall()
            for item in db_items:
                qty = cart_data[str(item['item_id'])]
                line_total = float(item['price']) * qty
                total += line_total
                items.append({'item': item, 'qty': qty, 'line_total': line_total})

    if request.method == 'POST':
        if not items:
            flash('Your cart is empty.')
            return redirect(url_for('orders.menu'))

        today = date.today()
        with db.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(token_number), 0) + 1 AS next_token FROM orders WHERE order_date = %s", (today,))
            row = cur.fetchone()
            token_num = row['next_token']

            cur.execute(
                "INSERT INTO orders (user_id, order_date, token_number, total_amount, status) VALUES (%s, %s, %s, %s, 'PLACED')",
                (g.user['user_id'], today, token_num, total)
            )
            order_id = cur.lastrowid

            for cart_item in items:
                cur.execute(
                    "INSERT INTO order_items (order_id, item_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                    (order_id, cart_item['item']['item_id'], cart_item['qty'], cart_item['item']['price'])
                )

            cur.execute(
                "INSERT INTO order_status_history (order_id, status, changed_by) VALUES (%s, 'PLACED', %s)",
                (order_id, g.user['user_id'])
            )

        session['cart'] = {}
        flash(f'Order placed successfully! Token #{token_num}')
        return redirect(url_for('orders.order_detail', order_id=order_id))

    return render_template('cart.html', items=items, total=total)

@bp.route('/cart/add', methods=('POST',))
@login_required
def add_to_cart():
    item_id = str(request.form['item_id'])
    qty = int(request.form.get('quantity', 1))
    cart_data = session.get('cart', {})
    cart_data[item_id] = cart_data.get(item_id, 0) + qty
    session['cart'] = cart_data
    flash('Item added to cart.')
    return redirect(url_for('orders.menu'))

@bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE order_id = %s AND user_id = %s", (order_id, g.user['user_id']))
        order = cur.fetchone()
        if not order:
            flash('Order not found.')
            return redirect(url_for('orders.menu'))

        cur.execute(
            "SELECT oi.*, m.name FROM order_items oi JOIN menu_items m ON oi.item_id = m.item_id WHERE oi.order_id = %s",
            (order_id,)
        )
        items = cur.fetchall()

    return render_template('order.html', order=order, items=items)

@bp.route('/orders')
@login_required
def my_orders():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY placed_at DESC", (g.user['user_id'],))
        orders = cur.fetchall()
    return render_template('my_orders.html', orders=orders)
