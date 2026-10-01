from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from db import get_db
from auth import staff_required
from domain import NEXT_STATUS

bp = Blueprint('staff', __name__, url_prefix='/staff')

@bp.route('/dashboard')
@staff_required
def dashboard():
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT o.*, u.full_name 
            FROM orders o 
            JOIN users u ON o.user_id = u.user_id 
            WHERE o.order_date = CURDATE() AND o.status NOT IN ('COLLECTED', 'CANCELLED') 
            ORDER BY o.placed_at ASC
        """)
        orders = cur.fetchall()
    return render_template('staff/dashboard.html', orders=orders)

@bp.route('/order/<int:order_id>/advance', methods=('POST',))
@staff_required
def advance_order(order_id):
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        order = cur.fetchone()

        if order and order['status'] in NEXT_STATUS:
            new_status = NEXT_STATUS[order['status']]
            cur.execute("UPDATE orders SET status = %s WHERE order_id = %s", (new_status, order_id))
            cur.execute("INSERT INTO order_status_history (order_id, status, changed_by) VALUES (%s, %s, %s)",
                        (order_id, new_status, g.user['user_id']))
            flash(f'Order #{order["token_number"]} updated to {new_status}.')

    return redirect(url_for('staff.dashboard'))
