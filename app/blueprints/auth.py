from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from app.extensions import db
from app.models import User, ROLE_STUDENT


bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Log in")


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
    )
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("That email is already registered.")


def _redirect_for_role(user: User):
    if user.role == "admin":
        return redirect(url_for("admin.menu_list"))
    if user.role == "staff":
        return redirect(url_for("staff.dashboard"))
    return redirect(url_for("student.menu"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html", form=form), 401
        if not user.is_active:
            flash("This account has been disabled.", "error")
            return render_template("auth/login.html", form=form), 403
        login_user(user)
        flash(f"Welcome back, {user.name}!", "success")
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return _redirect_for_role(user)
    return render_template("auth/login.html", form=form)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return _redirect_for_role(current_user)
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role=ROLE_STUDENT,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Account created. Welcome!", "success")
        return _redirect_for_role(user)
    return render_template("auth/register.html", form=form)


@bp.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
