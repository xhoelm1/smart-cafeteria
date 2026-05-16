from flask import Flask, redirect, url_for
from flask_login import current_user

from config import get_config
from app.extensions import db, login_manager, csrf, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(config_name))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.student import bp as student_bp
    from app.blueprints.staff import bp as staff_bp
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.api import bp as api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role == "admin":
            return redirect(url_for("admin.menu_list"))
        if current_user.role == "staff":
            return redirect(url_for("staff.dashboard"))
        return redirect(url_for("student.menu"))

    @app.context_processor
    def inject_globals():
        from app.models import Notification
        unread = 0
        if current_user.is_authenticated:
            unread = Notification.query.filter_by(
                user_id=current_user.id, is_read=False
            ).count()
        return {"unread_notifications": unread}

    with app.app_context():
        db.create_all()

    return app
