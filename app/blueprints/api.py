from flask import Blueprint, jsonify, abort, request

from flask_login import login_required, current_user

from app.extensions import db
from app.models import Order, MenuItem, Notification
from app.blueprints.student import _get_cart, _save_cart


bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/menu")
@login_required
def menu():
    items = MenuItem.query.order_by(MenuItem.category, MenuItem.name).all()
    return jsonify(
        [
            {
                "id": i.id,
                "name": i.name,
                "price": float(i.price),
                "stock": i.stock,
                "is_available": i.is_available,
                "category": i.category,
                "stock_status": i.stock_status,
            }
            for i in items
        ]
    )


@bp.route("/orders/<int:order_id>/status")
@login_required
def order_status(order_id: int):
    order = db.session.get(Order, order_id)
    if order is None:
        abort(404)
    if current_user.role == "student" and order.user_id != current_user.id:
        abort(403)
    return jsonify(
        {
            "id": order.id,
            "status": order.status,
            "total": float(order.total),
            "slot": order.time_slot.label if order.time_slot else None,
        }
    )


@bp.route("/notifications/unread_count")
@login_required
def unread_count():
    count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    return jsonify({"count": count})


@bp.route("/cart/add", methods=["POST"])
@login_required
def cart_add():
    if current_user.role != "student":
        return jsonify({"ok": False, "error": "Only students can add to cart."}), 403

    data = request.get_json(silent=True) or {}
    try:
        item_id = int(data.get("item_id"))
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid payload."}), 400

    if quantity < 1 or quantity > 20:
        return jsonify(
            {"ok": False, "error": "Quantity must be between 1 and 20."}
        ), 400

    item = db.session.get(MenuItem, item_id)
    if item is None:
        return jsonify({"ok": False, "error": "Item not found."}), 404
    if not item.is_available or item.stock <= 0:
        return jsonify({"ok": False, "error": f"{item.name} is sold out."}), 409

    cart = _get_cart()
    current_qty = cart.get(str(item.id), 0)
    new_qty = current_qty + quantity
    capped = False
    if new_qty > item.stock:
        new_qty = item.stock
        capped = True
    cart[str(item.id)] = new_qty
    _save_cart(cart)

    cart_total_qty = sum(cart.values())
    message = (
        f"Only {item.stock} of {item.name} left — cart capped."
        if capped
        else f"Added {item.name} to your cart."
    )
    return jsonify(
        {
            "ok": True,
            "message": message,
            "capped": capped,
            "cart_qty": cart_total_qty,
            "item": {
                "id": item.id,
                "name": item.name,
                "stock": item.stock,
                "line_quantity": new_qty,
                "stock_status": item.stock_status,
            },
        }
    )
