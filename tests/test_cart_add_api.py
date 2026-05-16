from app.extensions import db
from app.models import MenuItem


def test_api_cart_add_returns_json_and_does_not_redirect(app, client, login_as):
    login_as("student1@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        item_id = item.id

    resp = client.post(
        "/api/cart/add",
        json={"item_id": item_id, "quantity": 2},
    )

    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data["ok"] is True
    assert data["item"]["id"] == item_id
    assert data["cart_qty"] == 2

    cart_resp = client.get("/cart")
    assert cart_resp.status_code == 200


def test_api_cart_add_rejects_sold_out(app, client, login_as):
    login_as("student1@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        item.stock = 0
        item.is_available = False
        db.session.commit()
        item_id = item.id

    resp = client.post("/api/cart/add", json={"item_id": item_id, "quantity": 1})
    assert resp.status_code == 409
    data = resp.get_json()
    assert data["ok"] is False
    assert "sold out" in data["error"].lower()


def test_api_cart_add_caps_at_stock(app, client, login_as):
    login_as("student1@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        item.stock = 3
        db.session.commit()
        item_id = item.id

    resp = client.post("/api/cart/add", json={"item_id": item_id, "quantity": 10})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["capped"] is True
    assert data["item"]["line_quantity"] == 3
    assert data["cart_qty"] == 3


def test_api_cart_add_requires_login(client):
    resp = client.post("/api/cart/add", json={"item_id": 1, "quantity": 1})
    assert resp.status_code in (302, 401)


def test_api_cart_add_rejects_invalid_payload(app, client, login_as):
    login_as("student1@cafeteria.edu")
    resp = client.post("/api/cart/add", json={"item_id": "abc"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False
