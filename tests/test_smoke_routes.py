"""Smoke test: every page under every role returns < 500."""


PAGES_STUDENT = [
    "/", "/menu", "/cart", "/my-orders", "/notifications",
]
PAGES_STAFF = [
    "/", "/staff/", "/staff/menu", "/menu",
]
PAGES_ADMIN = [
    "/", "/admin/menu", "/admin/menu/new", "/admin/users", "/admin/reports",
]


def _check(client, paths):
    for p in paths:
        resp = client.get(p, follow_redirects=True)
        assert resp.status_code < 500, f"{p} returned {resp.status_code}"


def test_student_pages(client, login_as):
    login_as("student1@cafeteria.edu")
    _check(client, PAGES_STUDENT)


def test_staff_pages(client, login_as):
    login_as("staff@cafeteria.edu")
    _check(client, PAGES_STAFF)


def test_admin_pages(client, login_as):
    login_as("admin@cafeteria.edu")
    _check(client, PAGES_ADMIN)
