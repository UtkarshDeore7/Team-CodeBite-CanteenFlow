from flask import Blueprint, render_template, request, redirect, url_for, flash, g, Response, jsonify, make_response
from db import get_db
from auth import login_required
import csv
import io

bp = Blueprint('staff', __name__, url_prefix='/staff')

@bp.route('/dashboard')
@login_required
def dashboard():
    if g.user['role'] != 'STAFF':
        flash('Access denied. Staff only.')
        return redirect(url_for('orders.menu'))
    
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT o.*, u.full_name, 
                   GROUP_CONCAT(CONCAT(oi.quantity, 'x ', m.name) SEPARATOR ', ') AS items_summary
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN menu_items m ON oi.item_id = m.item_id
            WHERE o.order_date = CURDATE() AND o.status NOT IN ('COLLECTED', 'CANCELLED')
            GROUP BY o.order_id
            ORDER BY o.placed_at ASC
        """)
        active_orders = cur.fetchall()

    return render_template('staff_dashboard.html', orders=active_orders)

@bp.route('/order/<int:order_id>/status', methods=('POST',))
@login_required
def update_status(order_id):
    if g.user['role'] != 'STAFF':
        flash('Access denied.')
        return redirect(url_for('orders.menu'))

    new_status = request.form['status']
    db = get_db()
    with db.cursor() as cur:
        cur.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
    
    flash(f'Order #{order_id} status updated to {new_status}')
    return redirect(url_for('staff.dashboard'))

@bp.route('/menu', methods=('GET', 'POST'))
@login_required
def manage_menu():
    if g.user['role'] != 'STAFF':
        flash('Access denied.')
        return redirect(url_for('orders.menu'))

    db = get_db()
    if request.method == 'POST':
        item_id = request.form['item_id']
        is_available = True if request.form.get('is_available') == 'on' else False
        with db.cursor() as cur:
            cur.execute("UPDATE menu_items SET is_available = %s WHERE item_id = %s", (is_available, item_id))
        flash('Menu item stock status updated.')
        return redirect(url_for('staff.manage_menu'))

    with db.cursor() as cur:
        cur.execute("SELECT * FROM menu_items ORDER BY category_id, name")
        items = cur.fetchall()
    return render_template('staff_menu.html', items=items)

@bp.route('/analytics')
@login_required
def analytics():
    if g.user['role'] != 'STAFF':
        flash('Access denied.')
        return redirect(url_for('orders.menu'))

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total_orders, COALESCE(SUM(total_amount), 0) AS total_revenue FROM orders WHERE order_date = CURDATE() AND status != 'CANCELLED'")
        summary = cur.fetchone()

        cur.execute("""
            SELECT m.name, SUM(oi.quantity) AS total_qty, SUM(oi.quantity * oi.unit_price) AS total_sales
            FROM order_items oi
            JOIN menu_items m ON oi.item_id = m.item_id
            JOIN orders o ON oi.order_id = o.order_id
            WHERE o.order_date = CURDATE() AND o.status != 'CANCELLED'
            GROUP BY m.item_id
            ORDER BY total_qty DESC
        """)
        item_sales = cur.fetchall()

    return render_template('staff_analytics.html', summary=summary, item_sales=item_sales)

@bp.route('/export_sales_csv')
@login_required
def export_sales_csv():
    if g.user['role'] != 'STAFF':
        flash('Access denied.')
        return redirect(url_for('orders.menu'))

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT o.order_id, o.order_date, o.token_number, u.full_name, o.total_amount, o.status, o.placed_at
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.order_date = CURDATE()
            ORDER BY o.placed_at ASC
        """)
        orders = cur.fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Date', 'Token Number', 'Customer', 'Total Amount (INR)', 'Status', 'Placed At'])

    for row in orders:
        writer.writerow([row['order_id'], row['order_date'], row['token_number'], row['full_name'], row['total_amount'], row['status'], row['placed_at']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=canteen_daily_sales.csv'}
    )

# Public TV Counter Screen Endpoints
@bp.route('/tv')
def tv_queue():
    return render_template('queue.html')

@bp.route('/queue_data.json')
def queue_data():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT token_number, status 
            FROM orders 
            WHERE order_date = CURDATE() AND status IN ('PLACED', 'ACCEPTED', 'PREPARING', 'READY') 
            ORDER BY token_number ASC
        """)
        orders = cur.fetchall()

    preparing = [o['token_number'] for o in orders if o['status'] in ('PLACED', 'ACCEPTED', 'PREPARING')]
    ready = [o['token_number'] for o in orders if o['status'] == 'READY']

    res = make_response(jsonify({'preparing': preparing, 'ready': ready}))
    res.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Expires'] = '0'
    return res
