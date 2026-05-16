from datetime import date
from decimal import Decimal

from flask import (
    Blueprint, render_template, redirect, url_for, request, flash, session, abort
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange

from app.extensions import db
from app.models import MenuItem, TimeSlot, Order, OrderItem
from app.utils.decorators import role_required


bp = Blueprint("student", __name__)


CART_KEY = "cart"


def _get_cart() -> dict[str, int]:
    cart = session.get(CART_KEY) or {}
    return {str(k): int(v) for k, v in cart.items()}


def _save_cart(cart: dict[str, int]) -> None:
    session[CART_KEY] = cart
    session.modified = True


def _cart_items_with_totals():
    cart = _get_cart()
    rows = []
    subtotal = Decimal(0)
    for item_id, qty in cart.items():
        item = db.session.get(MenuItem, int(item_id))
        if item is None:
            continue
        line = Decimal(item.price) * qty
        subtotal += line
        rows.append({"item": item, "quantity": qty, "line_total": line})
    return rows, subtotal


class EmptyForm(FlaskForm):
    submit = SubmitField("Submit")


class AddToCartForm(FlaskForm):
    item_id = HiddenField(validators=[DataRequired()])
    quantity = IntegerField("Quantity", default=1, validators=[NumberRange(min=1, max=20)])
    submit = SubmitField("Add to cart")


class UpdateCartForm(FlaskForm):
    item_id = HiddenField(validators=[DataRequired()])
    quantity = IntegerField("Quantity", validators=[NumberRange(min=0, max=20)])
    submit = SubmitField("Update")


class CheckoutForm(FlaskForm):
    time_slot_id = HiddenField(validators=[DataRequired()])
    submit = SubmitField("Place order")


@bp.route("/menu")
@login_required
@role_required("student", "staff", "admin")
def menu():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    add_form = AddToCartForm()
    return render_template("student/menu.html", items=items, add_form=add_form)


@bp.route("/cart", methods=["GET"])
@login_required
@role_required("student")
def cart():
    rows, subtotal = _cart_items_with_totals()
    update_form = UpdateCartForm()
    clear_form = EmptyForm()
    return render_template(
        "student/cart.html",
        rows=rows,
        subtotal=subtotal,
        update_form=update_form,
        clear_form=clear_form,
    )


@bp.route("/cart/add", methods=["POST"])
@login_required
@role_required("student")
def cart_add():
    form = AddToCartForm()
    if not form.validate_on_submit():
        flash("Invalid request.", "error")
        return redirect(url_for("student.menu"))
    item = db.session.get(MenuItem, int(form.item_id.data))
    if item is None:
        abort(404)
    if not item.is_available or item.stock <= 0:
        flash(f"{item.name} is sold out.", "error")
        return redirect(url_for("student.menu"))
    cart = _get_cart()
    new_qty = cart.get(str(item.id), 0) + int(form.quantity.data or 1)
    if new_qty > item.stock:
        flash(f"Only {item.stock} of {item.name} left.", "error")
        new_qty = item.stock
    cart[str(item.id)] = new_qty
    _save_cart(cart)
    flash(f"Added {item.name} to your cart.", "success")
    return redirect(url_for("student.menu"))


@bp.route("/cart/update", methods=["POST"])
@login_required
@role_required("student")
def cart_update():
    form = UpdateCartForm()
    if not form.validate_on_submit():
        flash("Invalid request.", "error")
        return redirect(url_for("student.cart"))
    cart = _get_cart()
    item_id = str(form.item_id.data)
    qty = int(form.quantity.data or 0)
    if qty <= 0:
        cart.pop(item_id, None)
    else:
        item = db.session.get(MenuItem, int(item_id))
        if item is None:
            cart.pop(item_id, None)
        else:
            cart[item_id] = min(qty, item.stock)
    _save_cart(cart)
    return redirect(url_for("student.cart"))


@bp.route("/cart/clear", methods=["POST"])
@login_required
@role_required("student")
def cart_clear():
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    session.pop(CART_KEY, None)
    flash("Cart cleared.", "info")
    return redirect(url_for("student.cart"))


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
@role_required("student")
def checkout():
    rows, subtotal = _cart_items_with_totals()
    if not rows:
        flash("Your cart is empty.", "info")
        return redirect(url_for("student.menu"))

    today = date.today()
    slots = (
        TimeSlot.query.filter(TimeSlot.date >= today)
        .order_by(TimeSlot.date, TimeSlot.slot_time)
        .all()
    )

    form = CheckoutForm()
    if form.validate_on_submit():
        slot = db.session.get(TimeSlot, int(form.time_slot_id.data))
        if slot is None or slot.date < today:
            flash("Please pick a valid pickup time.", "error")
            return render_template(
                "student/checkout.html", rows=rows, subtotal=subtotal,
                slots=slots, form=form,
            )
        if slot.is_full:
            flash("That time slot is now full. Please pick another.", "error")
            return render_template(
                "student/checkout.html", rows=rows, subtotal=subtotal,
                slots=slots, form=form,
            )

        for row in rows:
            item = row["item"]
            if not item.is_available or item.stock < row["quantity"]:
                flash(f"{item.name} is no longer available in that quantity.", "error")
                return redirect(url_for("student.cart"))

        order = Order(
            user_id=current_user.id,
            time_slot_id=slot.id,
            status="confirmed",
            total=subtotal,
        )
        db.session.add(order)
        db.session.flush()
        for row in rows:
            item = row["item"]
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    menu_item_id=item.id,
                    quantity=row["quantity"],
                    unit_price=item.price,
                )
            )
            item.stock = item.stock - row["quantity"]
        db.session.commit()

        session.pop(CART_KEY, None)
        flash(f"Order #{order.id} placed for {slot.label}.", "success")
        return redirect(url_for("student.order_detail", order_id=order.id))

    return render_template(
        "student/checkout.html",
        rows=rows, subtotal=subtotal, slots=slots, form=form,
    )


@bp.route("/my-orders")
@login_required
@role_required("student")
def my_orders():
    orders = (
        Order.query.filter_by(user_id=current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("student/my_orders.html", orders=orders)


@bp.route("/orders/<int:order_id>")
@login_required
@role_required("student", "staff", "admin")
def order_detail(order_id: int):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    if current_user.role == "student" and order.user_id != current_user.id:
        abort(403)
    cancel_form = EmptyForm()
    return render_template(
        "student/order_detail.html", order=order, cancel_form=cancel_form
    )


@bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
@role_required("student")
def cancel_order(order_id: int):
    form = EmptyForm()
    if not form.validate_on_submit():
        abort(400)
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    if order.user_id != current_user.id:
        abort(403)
    if not order.can_cancel():
        flash("This order can no longer be cancelled.", "error")
        return redirect(url_for("student.order_detail", order_id=order.id))
    for oi in order.items:
        oi.menu_item.stock = oi.menu_item.stock + oi.quantity
    order.status = "cancelled"
    db.session.commit()
    flash(f"Order #{order.id} cancelled.", "info")
    return redirect(url_for("student.my_orders"))


@bp.route("/notifications")
@login_required
def notifications():
    from app.models import Notification
    notes = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    for n in notes:
        n.is_read = True
    db.session.commit()
    return render_template("student/notifications.html", notes=notes)
