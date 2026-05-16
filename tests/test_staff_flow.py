from app.extensions import db
from app.models import Order, MenuItem, Notification, User


def test_staff_can_advance_order_through_statuses(app, client, login_as):
    with app.app_context():
        order = Order.query.first()
        order.status = "confirmed"
        db.session.commit()
        oid = order.id
        user_id = order.user_id

    login_as("staff@cafeteria.edu")
    expected = ["preparing", "ready", "completed"]
    for status in expected:
        resp = client.post(
            "/staff/advance", data={"order_id": oid}, follow_redirects=True
        )
        assert resp.status_code == 200
        with app.app_context():
            assert db.session.get(Order, oid).status == status
            if status == "ready":
                notes = Notification.query.filter_by(user_id=user_id).all()
                assert any(f"#{oid}" in n.message for n in notes)


def test_staff_cannot_advance_completed(app, client, login_as):
    with app.app_context():
        order = Order.query.first()
        order.status = "completed"
        db.session.commit()
        oid = order.id

    login_as("staff@cafeteria.edu")
    resp = client.post(
        "/staff/advance", data={"order_id": oid}, follow_redirects=True
    )
    assert b"already completed" in resp.data.lower()


def test_staff_toggle_availability(app, client, login_as):
    with app.app_context():
        item = MenuItem.query.first()
        item.is_available = True
        db.session.commit()
        iid = item.id

    login_as("staff@cafeteria.edu")
    client.post("/staff/menu/toggle", data={"item_id": iid}, follow_redirects=True)
    with app.app_context():
        assert db.session.get(MenuItem, iid).is_available is False


def test_student_cannot_access_staff_dashboard(client, login_as):
    login_as("student1@cafeteria.edu")
    resp = client.get("/staff/")
    assert resp.status_code == 403
