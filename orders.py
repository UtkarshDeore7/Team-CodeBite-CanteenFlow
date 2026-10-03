from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g, jsonify
from db import get_db
from auth import login_required
from datetime import date
import json

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
        cur.execute("SELECT COUNT(*) AS active_count FROM orders WHERE order_date = CURDATE() AND status IN ('PLACED', 'ACCEPTED', 'PREPARING')")
        active_count = cur.fetchone()['active_count']

    if active_count <= 3:
        rush_info = {'label': '🟢 Low Rush (~5 min wait)', 'color': '#059669', 'bg': '#ecfdf5'}
    elif active_count <= 8:
        rush_info = {'label': '🟡 Moderate Rush (~12 min wait)', 'color': '#d97706', 'bg': '#fef3c7'}
    else:
        rush_info = {'label': '🔴 Peak Rush (~20 min wait)', 'color': '#dc2626', 'bg': '#fef2f2'}

    with db.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) AS total_spent FROM orders WHERE user_id = %s", (g.user['user_id'],))
        spent = cur.fetchone()['total_spent']
        food_coins = int(spent // 10)

    cart_data = session.get('cart', {})
    return render_template('menu.html', categories=categories, items=items, active_queue=active_count, rush_info=rush_info, food_coins=food_coins, cart_data=cart_data)

@bp.route('/cart/update_ajax', methods=('POST',))
@login_required
def update_cart_ajax():
    data = request.get_json() or {}
    item_id = str(data.get('item_id'))
    action = data.get('action', 'add')

    cart_data = session.get('cart', {})
    current_qty = cart_data.get(item_id, 0)

    if action == 'add':
        if current_qty < 5:
            cart_data[item_id] = current_qty + 1
    elif action == 'remove':
        if current_qty > 1:
            cart_data[item_id] = current_qty - 1
        else:
            cart_data.pop(item_id, None)

    session['cart'] = cart_data
    session.modified = True

    db = get_db()
    total_items = sum(cart_data.values())
    total_price = 0.0

    if cart_data:
        ids = list(cart_data.keys())
        format_strings = ','.join(['%s'] * len(ids))
        with db.cursor() as cur:
            cur.execute(f"SELECT item_id, price, name FROM menu_items WHERE item_id IN ({format_strings})", ids)
            db_items = cur.fetchall()
            for item in db_items:
                qty = cart_data[str(item['item_id'])]
                total_price += float(item['price']) * qty

    item_qty = cart_data.get(item_id, 0)
    return jsonify({
        'success': True,
        'cart': cart_data,
        'item_qty': item_qty,
        'total_items': total_items,
        'total_price': round(total_price, 2)
    })

@bp.route('/cart', methods=('GET', 'POST'))
@login_required
def cart():
    cart_data = session.get('cart', {})
    promo_code = session.get('promo_code', '')
    use_coins = session.get('use_coins', False)
    db = get_db()
    items = []
    subtotal = 0.0

    if cart_data:
        ids = list(cart_data.keys())
        format_strings = ','.join(['%s'] * len(ids))
        with db.cursor() as cur:
            cur.execute(f"SELECT * FROM menu_items WHERE item_id IN ({format_strings})", ids)
            db_items = cur.fetchall()
            for item in db_items:
                qty = cart_data[str(item['item_id'])]
                line_total = float(item['price']) * qty
                subtotal += line_total
                items.append({'item': item, 'qty': qty, 'line_total': line_total})

    with db.cursor() as cur:
        cur.execute("SELECT COALESCE(SUM(total_amount), 0) AS total_spent FROM orders WHERE user_id = %s", (g.user['user_id'],))
        spent = cur.fetchone()['total_spent']
        food_coins = int(spent // 10)

    promo_discount = (subtotal * 0.10) if promo_code == 'CODEBITE10' else 0.0
    coin_discount = float(min(food_coins, subtotal - promo_discount)) if use_coins else 0.0
    total_discount = promo_discount + coin_discount
    total = max(0.0, subtotal - total_discount)

    if request.method == 'POST':
        if 'apply_promo' in request.form:
            code = request.form.get('promo_code', '').strip().upper()
            if code == 'CODEBITE10':
                session['promo_code'] = 'CODEBITE10'
                flash('Promo code CODEBITE10 applied! 10% OFF')
            else:
                session.pop('promo_code', None)
                flash('Invalid promo code.')
            return redirect(url_for('orders.cart'))

        if 'toggle_coins' in request.form:
            session['use_coins'] = not session.get('use_coins', False)
            flash('Food Coins preference updated!')
            return redirect(url_for('orders.cart'))

        if not items:
            flash('Your cart is empty.')
            return redirect(url_for('orders.menu'))

        with db.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS user_active_orders 
                FROM orders 
                WHERE user_id = %s AND status IN ('PLACED', 'ACCEPTED', 'PREPARING', 'READY')
            """, (g.user['user_id'],))
            user_active_orders = cur.fetchone()['user_active_orders']

        if user_active_orders >= 2:
            flash('⚠️ Anti-Spam Protection: You have 2 active orders in progress! Please collect or cancel them before placing a new order.')
            return redirect(url_for('orders.my_orders'))

        time_slot = request.form.get('time_slot', 'Express Immediate')
        today = date.today()

        with db.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(token_number), 0) + 1 AS next_token FROM orders WHERE order_date = %s", (today,))
            token_num = cur.fetchone()['next_token']

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

        session['cart'] = {}
        session.pop('promo_code', None)
        session.pop('use_coins', None)
        flash(f'Order Scheduled for {time_slot}! Token #{token_num}')
        return redirect(url_for('orders.order_detail', order_id=order_id))

    return render_template('cart.html', items=items, subtotal=subtotal, discount=total_discount, coin_discount=coin_discount, total=total, promo_code=promo_code, food_coins=food_coins, use_coins=use_coins)

@bp.route('/cart/add', methods=('POST',))
@login_required
def add_to_cart():
    item_id = str(request.form['item_id'])
    cart_data = session.get('cart', {})
    current_qty = cart_data.get(item_id, 0)
    if current_qty < 5:
        cart_data[item_id] = current_qty + 1
        session['cart'] = cart_data
        flash('Item added to cart.')
    else:
        flash('Maximum limit of 5 units per item reached.')
    return redirect(request.referrer or url_for('orders.menu'))

@bp.route('/order/<int:order_id>/cancel', methods=('POST',))
@login_required
def cancel_order(order_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT status FROM orders WHERE order_id = %s AND user_id = %s", (order_id, g.user['user_id']))
        order = cur.fetchone()
        
        if not order:
            flash('Order not found.')
            return redirect(url_for('orders.my_orders'))
            
        if order['status'] != 'PLACED':
            flash('Cannot cancel order! The kitchen has already started preparing your food.')
            return redirect(url_for('orders.order_detail', order_id=order_id))

        cur.execute("UPDATE orders SET status = 'CANCELLED' WHERE order_id = %s", (order_id,))

    flash(f'Order #{order_id} has been successfully cancelled.')
    return redirect(url_for('orders.my_orders'))

@bp.route('/order/<int:order_id>/reorder', methods=('POST',))
@login_required
def reorder(order_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE order_id = %s AND user_id = %s", (order_id, g.user['user_id']))
        order = cur.fetchone()
        if not order:
            flash('Order not found.')
            return redirect(url_for('orders.my_orders'))

        cur.execute("SELECT item_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        past_items = cur.fetchall()

    cart_data = session.get('cart', {})
    for item in past_items:
        item_id_str = str(item['item_id'])
        cart_data[item_id_str] = min(5, cart_data.get(item_id_str, 0) + item['quantity'])

    session['cart'] = cart_data
    flash('Previous meal items added to your cart!')
    return redirect(url_for('orders.cart'))

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

        cur.execute("SELECT oi.*, m.name, m.prep_minutes FROM order_items oi JOIN menu_items m ON oi.item_id = m.item_id WHERE oi.order_id = %s", (order_id,))
        items = cur.fetchall()

        cur.execute("SELECT COUNT(*) AS ahead_count FROM orders WHERE order_date = CURDATE() AND status IN ('PLACED', 'ACCEPTED', 'PREPARING') AND order_id < %s", (order_id,))
        ahead_count = cur.fetchone()['ahead_count']
        max_prep = max([item['prep_minutes'] for item in items]) if items else 5
        estimated_wait = max_prep + (ahead_count * 2)

        cur.execute("SELECT * FROM order_reviews WHERE order_id = %s", (order_id,))
        review = cur.fetchone()

    return render_template('order.html', order=order, items=items, estimated_wait=estimated_wait, ahead_count=ahead_count, review=review)

@bp.route('/order/<int:order_id>/review', methods=('POST',))
@login_required
def add_review(order_id):
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment', '')
    db = get_db()
    with db.cursor() as cur:
        cur.execute("INSERT INTO order_reviews (order_id, user_id, rating, comment) VALUES (%s, %s, %s, %s)",
                    (order_id, g.user['user_id'], rating, comment))
    flash('Thank you for rating your meal!')
    return redirect(url_for('orders.order_detail', order_id=order_id))

@bp.route('/order/<int:order_id>/status.json')
@login_required
def order_status_json(order_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT status FROM orders WHERE order_id = %s AND user_id = %s", (order_id, g.user['user_id']))
        order = cur.fetchone()
    if not order:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'status': order['status']})

@bp.route('/orders')
@login_required
def my_orders():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT o.*, 
                   GROUP_CONCAT(CONCAT(oi.quantity, 'x ', m.name) SEPARATOR ', ') AS items_summary
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN menu_items m ON oi.item_id = m.item_id
            WHERE o.user_id = %s
            GROUP BY o.order_id
            ORDER BY o.placed_at DESC
        """, (g.user['user_id'],))
        orders = cur.fetchall()
    return render_template('my_orders.html', orders=orders)
