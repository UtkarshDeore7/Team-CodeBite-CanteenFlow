import click
from flask import Flask, render_template
from werkzeug.security import generate_password_hash
from config import Config
from db import close_db, get_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.teardown_appcontext(close_db)

    import auth
    import orders
    import staff

    app.register_blueprint(auth.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(staff.bp)

    @app.route('/queue')
    def queue():
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM v_live_queue")
            queue_items = cur.fetchall()
        return render_template('queue.html', queue_items=queue_items)

    @app.cli.command('create-staff')
    @click.argument('name')
    @click.argument('email')
    @click.argument('password')
    def create_staff(name, email, password):
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "INSERT INTO users (full_name, email, password_hash, role) VALUES (%s, %s, %s, 'STAFF')",
                (name, email, generate_password_hash(password))
            )
        click.echo(f"Staff account created for {email}")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
