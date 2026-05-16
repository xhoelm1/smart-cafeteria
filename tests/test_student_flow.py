from datetime import datetime, time

from app.extensions import db
from app.models import MenuItem, TimeSlot, Order, User
from app.blueprints.student import _next_open_pickup_date, CAFETERIA_CLOSE_HOUR


def _first_open_slot():
    now = datetime.now()
    target = _next_open_pickup_date(now)
    close = time(CAFETERIA_CLOSE_HOUR, 0)
    q = TimeSlot.query.filter(
        TimeSlot.date == target,
        TimeSlot.slot_time < close,
    )
    if target == now.date():
        q = q.filter(TimeSlot.slot_time > now.time())
    return q.order_by(TimeSlot.slot_time).first()


def test_student_places_order_and_stock_decrements(app, client, login_as):
    login_as("student1@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        initial_stock = item.stock
        item_id = item.id
        slot_id = _first_open_slot().id

    client.post(
        "/cart/add", data={"item_id": item_id, "quantity": 2}, follow_redirects=True
    )
    resp = client.get("/cart")
    assert resp.status_code == 200

    resp = client.post(
        "/checkout", data={"time_slot_id": slot_id}, follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Order #" in resp.data or b"placed" in resp.data.lower()

    with app.app_context():
        refreshed = db.session.get(MenuItem, item_id)
        assert refreshed.stock == initial_stock - 2
        order = Order.query.order_by(Order.id.desc()).first()
        assert order.status == "confirmed"


def test_sold_out_item_cannot_be_added(app, client, login_as):
    login_as("student1@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        item.stock = 0
        item.is_available = False
        db.session.commit()
        item_id = item.id
    resp = client.post(
        "/cart/add", data={"item_id": item_id, "quantity": 1}, follow_redirects=True
    )
    assert b"sold out" in resp.data.lower()


def test_time_slot_capacity_enforced(app, client, login_as):
    with app.app_context():
        slot = _first_open_slot()
        slot.capacity = 1
        db.session.commit()
        slot_id = slot.id
        item = MenuItem.query.first()
        item.stock = 50
        db.session.commit()
        item_id = item.id

    login_as("student1@cafeteria.edu")
    client.post("/cart/add", data={"item_id": item_id, "quantity": 1})
    r1 = client.post("/checkout", data={"time_slot_id": slot_id}, follow_redirects=True)
    assert r1.status_code == 200

    client.get("/logout")
    login_as("student2@cafeteria.edu")
    client.post("/cart/add", data={"item_id": item_id, "quantity": 1})
    r2 = client.post("/checkout", data={"time_slot_id": slot_id}, follow_redirects=True)
    assert b"full" in r2.data.lower()


def test_cancel_before_preparing_succeeds(app, client, login_as):
    login_as("student1@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        slot_id = _first_open_slot().id
        item_id = item.id
    client.post("/cart/add", data={"item_id": item_id, "quantity": 1})
    client.post("/checkout", data={"time_slot_id": slot_id}, follow_redirects=True)
    with app.app_context():
        order = Order.query.order_by(Order.id.desc()).first()
        assert order.status == "confirmed"
        oid = order.id
    resp = client.post(f"/orders/{oid}/cancel", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(Order, oid).status == "cancelled"


def test_cancel_after_preparing_fails(app, client, login_as):
    login_as("student1@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        slot_id = _first_open_slot().id
        item_id = item.id
    client.post("/cart/add", data={"item_id": item_id, "quantity": 1})
    client.post("/checkout", data={"time_slot_id": slot_id}, follow_redirects=True)
    with app.app_context():
        order = Order.query.order_by(Order.id.desc()).first()
        order.status = "preparing"
        db.session.commit()
        oid = order.id
    resp = client.post(f"/orders/{oid}/cancel", follow_redirects=True)
    assert b"no longer be cancelled" in resp.data.lower()
    with app.app_context():
        assert db.session.get(Order, oid).status == "preparing"
