import functools
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

bp = Blueprint('auth', __name__)

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def staff_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or g.user['role'] not in ('STAFF', 'ADMIN'):
            flash('Staff access required.')
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            g.user = cur.fetchone()

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone', '')

        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (full_name, email, password_hash, role, phone) VALUES (%s, %s, %s, 'STUDENT', %s)",
                    (full_name, email, generate_password_hash(password), phone)
                )
            flash('Registration successful! Please log in.')
            return redirect(url_for('auth.login'))
        except Exception:
            flash('Registration failed. Email might already exist.')

    return render_template('login.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['user_id']
            if user['role'] in ('STAFF', 'ADMIN'):
                return redirect(url_for('staff.dashboard'))
            return redirect(url_for('orders.menu'))

        flash('Invalid email or password.')

    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
