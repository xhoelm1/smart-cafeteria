from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from wtforms.validators import DataRequired

from app.extensions import db
from app.models import Order, MenuItem
from app.utils.decorators import role_required
from app.utils.notifications import notify


bp = Blueprint("staff", __name__, url_prefix="/staff")


class AdvanceForm(FlaskForm):
    order_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Advance")


class ToggleAvailabilityForm(FlaskForm):
    item_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Toggle")


STATUS_ORDER = ["pending", "confirmed", "preparing", "ready", "completed"]


@bp.route("/")
@login_required
@role_required("staff", "admin")
def dashboard():
    active = (
        Order.query.filter(Order.status.in_(["pending", "confirmed", "preparing", "ready"]))
        .order_by(Order.created_at)
        .all()
    )
    columns = {
        "pending": [o for o in active if o.status in ("pending", "confirmed")],
        "preparing": [o for o in active if o.status == "preparing"],
        "ready": [o for o in active if o.status == "ready"],
    }
    form = AdvanceForm()
    return render_template("staff/dashboard.html", columns=columns, form=form)


@bp.route("/advance", methods=["POST"])
@login_required
@role_required("staff", "admin")
def advance():
    form = AdvanceForm()
    if not form.validate_on_submit():
        abort(400)
    order = db.session.get(Order, int(form.order_id.data))
    if order is None:
        abort(404)
    next_status = order.can_advance()
    if next_status is None:
        flash("Order is already completed.", "info")
        return redirect(url_for("staff.dashboard"))
    order.status = next_status
    db.session.commit()
    if next_status == "ready":
        notify(order.user_id, f"Your order #{order.id} is ready for pickup!")
    flash(f"Order #{order.id} → {next_status}.", "success")
    return redirect(url_for("staff.dashboard"))


@bp.route("/menu")
@login_required
@role_required("staff", "admin")
def menu_view():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    form = ToggleAvailabilityForm()
    return render_template("staff/menu.html", items=items, form=form)


@bp.route("/menu/toggle", methods=["POST"])
@login_required
@role_required("staff", "admin")
def toggle_availability():
    form = ToggleAvailabilityForm()
    if not form.validate_on_submit():
        abort(400)
    item = db.session.get(MenuItem, int(form.item_id.data))
    if item is None:
        abort(404)
    item.is_available = not item.is_available
    db.session.commit()
    state = "available" if item.is_available else "unavailable"
    flash(f"{item.name} is now {state}.", "success")
    return redirect(url_for("staff.menu_view"))
