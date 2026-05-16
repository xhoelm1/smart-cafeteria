def test_register_creates_student(client):
    resp = client.post(
        "/register",
        data={
            "name": "New Student",
            "email": "new@cafeteria.edu",
            "password": "Demo1234!",
            "confirm": "Demo1234!",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Menu" in resp.data or b"menu" in resp.data


def test_register_rejects_duplicate_email(client):
    resp = client.post(
        "/register",
        data={
            "name": "Dup",
            "email": "student1@cafeteria.edu",
            "password": "Demo1234!",
            "confirm": "Demo1234!",
        },
    )
    assert b"already registered" in resp.data


def test_login_wrong_password(client, demo_password):
    resp = client.post(
        "/login",
        data={"email": "student1@cafeteria.edu", "password": "wrongpass1!"},
    )
    assert resp.status_code == 401
    assert b"Invalid" in resp.data


def test_login_and_logout(client, login_as):
    r = login_as("student1@cafeteria.edu")
    assert r.status_code == 200
    r = client.get("/logout", follow_redirects=True)
    assert b"Log in" in r.data
