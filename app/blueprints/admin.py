from datetime import date, datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, DecimalField, IntegerField,
    BooleanField, SelectField, SubmitField, PasswordField,
)
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Email, ValidationError

from app.extensions import db
from app.models import MenuItem, User, Order, OrderItem, TimeSlot, VALID_ROLES
from app.utils.decorators import role_required
from sqlalchemy import func


bp = Blueprint("admin", __name__, url_prefix="/admin")


CATEGORIES = ["Main", "Snack", "Drink", "Dessert"]


class MenuItemForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=500)])
    price = DecimalField("Price", validators=[DataRequired(), NumberRange(min=0, max=99999)], places=2)
    stock = IntegerField("Stock", validators=[DataRequired(), NumberRange(min=0, max=99999)])
    category = SelectField("Category", choices=[(c, c) for c in CATEGORIES])
    image_url = StringField("Image URL (optional)", validators=[Optional(), Length(max=255)])
    is_available = BooleanField("Available", default=True)
    submit = SubmitField("Save")


class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField("Role", choices=[("student", "Student"), ("staff", "Staff"), ("admin", "Admin")])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Create user")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("Email already exists.")


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


class ToggleUserForm(FlaskForm):
    submit = SubmitField("Toggle")


@bp.route("/menu")
@login_required
@role_required("admin")
def menu_list():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    delete_form = EmptyForm()
    return render_template("admin/menu.html", items=items, delete_form=delete_form)


@bp.route("/menu/new", methods=["GET", "POST"])
@login_required
@role_required("admin")
def menu_new():
    form = MenuItemForm()
    if form.validate_on_submit():
        item = MenuItem(
            name=form.name.data.strip(),
            description=form.description.data or "",
            price=Decimal(form.price.data),
            stock=int(form.stock.data),
            category=form.category.data,
            image_url=(form.image_url.data or "").strip(),
            is_available=bool(form.is_available.data),
        )
        db.session.add(item)
        db.session.commit()
        flash(f"Created {item.name}.", "success")
        return redirect(url_for("admin.menu_list"))
    return render_template("admin/menu_form.html", form=form, item=None)


@bp.route("/menu/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def menu_edit(item_id: int):
    item = db.session.get(MenuItem, item_id)
    if item is None:
        abort(404)
    form = MenuItemForm(obj=item)
    if form.validate_on_submit():
        item.name = form.name.data.strip()
        item.description = form.description.data or ""
        item.price = Decimal(form.price.data)
        item.stock = int(form.stock.data)
        item.category = form.category.data
        item.image_url = (form.image_url.data or "").strip()
        item.is_available = bool(form.is_available.data)
        db.session.commit()
        flash(f"Updated {item.name}.", "success")
        return redirect(url_for("admin.menu_list"))
    return render_template("admin/menu_form.html", form=form, item=item)


@bp.route("/menu/<int:item_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def menu_delete(item_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    item = db.session.get(MenuItem, item_id)
    if item is None:
        abort(404)
    name = item.name
    db.session.delete(item)
    db.session.commit()
    flash(f"Deleted {name}.", "info")
    return redirect(url_for("admin.menu_list"))


@bp.route("/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def users():
    form = UserForm()
    toggle_form = ToggleUserForm()
    if form.validate_on_submit():
        u = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role=form.role.data,
        )
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        flash(f"Created user {u.email}.", "success")
        return redirect(url_for("admin.users"))
    all_users = User.query.order_by(User.role, User.name).all()
    return render_template(
        "admin/users.html", users=all_users, form=form, toggle_form=toggle_form
    )


@bp.route("/users/toggle", methods=["POST"])
@login_required
@role_required("admin")
def users_toggle():
    form = ToggleUserForm()
    if not form.validate_on_submit():
        abort(400)
    raw_uid = (request.form.get("user_id") or "").strip()
    try:
        uid = int(raw_uid)
    except ValueError:
        abort(400)
    user = db.session.get(User, uid)
    if user is None:
        abort(404)
    user.is_active_flag = not user.is_active_flag
    db.session.commit()
    state = "enabled" if user.is_active_flag else "disabled"
    flash(f"User {user.email} {state}.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/reports")
@login_required
@role_required("admin")
def reports():
    qdate = request.args.get("date")
    try:
        report_date = date.fromisoformat(qdate) if qdate else date.today()
    except ValueError:
        report_date = date.today()

    start = datetime.combine(report_date, datetime.min.time())
    end = start + timedelta(days=1)

    todays_orders = (
        Order.query.filter(Order.created_at >= start, Order.created_at < end).all()
    )
    paid_orders = [o for o in todays_orders if o.status != "cancelled"]
    total_orders = len(todays_orders)
    revenue = sum((Decimal(o.total) for o in paid_orders), Decimal(0))

    by_status: dict[str, int] = {}
    for o in todays_orders:
        by_status[o.status] = by_status.get(o.status, 0) + 1

    item_totals: dict[int, dict] = {}
    for o in paid_orders:
        for oi in o.items:
            row = item_totals.setdefault(
                oi.menu_item_id,
                {"name": oi.menu_item.name if oi.menu_item else f"#{oi.menu_item_id}", "qty": 0},
            )
            row["qty"] += oi.quantity
    top_items = sorted(item_totals.values(), key=lambda r: r["qty"], reverse=True)[:5]

    return render_template(
        "admin/reports.html",
        report_date=report_date,
        total_orders=total_orders,
        revenue=revenue,
        top_items=top_items,
        by_status=by_status,
    )
