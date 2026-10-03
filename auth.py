from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db
import functools

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
        if g.user is None:
            flash('Please log in first.')
            return redirect(url_for('auth.login'))
        if g.user.get('role') != 'STAFF':
            flash('Access restricted to canteen staff.')
            return redirect(url_for('orders.menu'))
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
        full_name = request.form['full_name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'STUDENT')
        db = get_db()
        error = None

        if not full_name or not email or not password:
            error = 'All fields are required.'

        if error is None:
            try:
                hashed_pw = generate_password_hash(password)
                with db.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                        (full_name, email, hashed_pw, role)
                    )
                flash('Registration successful! Please log in.')
                return redirect(url_for('auth.login'))
            except Exception:
                error = 'Email already registered.'

        flash(error)

    return render_template('register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None

        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        if user is None or not check_password_hash(user['password_hash'], password):
            error = 'Invalid email or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['user_id']
            session['user_role'] = user['role']
            if user['role'] == 'STAFF':
                flash('Welcome to Staff Operations Dashboard!')
                return redirect(url_for('staff.dashboard'))
            else:
                flash(f'Welcome back, {user["full_name"]}!')
                return redirect(url_for('orders.menu'))

        flash(error)

    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('auth.login'))
