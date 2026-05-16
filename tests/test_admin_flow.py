from app.extensions import db
from app.models import MenuItem, User


def test_admin_creates_menu_item(app, client, login_as):
    login_as("admin@cafeteria.edu")
    resp = client.post(
        "/admin/menu/new",
        data={
            "name": "Test Burger",
            "description": "Tasty",
            "price": "499.50",
            "stock": "10",
            "category": "Main",
            "image_url": "",
            "is_available": "y",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert MenuItem.query.filter_by(name="Test Burger").first() is not None


def test_admin_edits_menu_item(app, client, login_as):
    login_as("admin@cafeteria.edu")
    with app.app_context():
        item = MenuItem.query.first()
        iid = item.id
    resp = client.post(
        f"/admin/menu/{iid}/edit",
        data={
            "name": "Renamed",
            "description": "Updated",
            "price": "123.45",
            "stock": "7",
            "category": "Drink",
            "image_url": "",
            "is_available": "y",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(MenuItem, iid).name == "Renamed"


def test_admin_deletes_menu_item(app, client, login_as):
    login_as("admin@cafeteria.edu")
    with app.app_context():
        item = MenuItem(name="ToDelete", price=1, stock=1, category="Main", is_available=True)
        db.session.add(item)
        db.session.commit()
        iid = item.id
    resp = client.post(f"/admin/menu/{iid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(MenuItem, iid) is None


def test_admin_reports_returns_valid_html(client, login_as):
    login_as("admin@cafeteria.edu")
    resp = client.get("/admin/reports")
    assert resp.status_code == 200
    assert b"Daily Report" in resp.data


def test_student_cannot_access_admin(client, login_as):
    login_as("student1@cafeteria.edu")
    resp = client.get("/admin/menu")
    assert resp.status_code == 403


def test_admin_creates_staff_user(app, client, login_as):
    login_as("admin@cafeteria.edu")
    resp = client.post(
        "/admin/users",
        data={
            "name": "New Staff",
            "email": "newstaff@cafeteria.edu",
            "role": "staff",
            "password": "Demo1234!",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        u = User.query.filter_by(email="newstaff@cafeteria.edu").first()
        assert u is not None and u.role == "staff"
