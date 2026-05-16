from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Order, MenuItem, Notification


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
