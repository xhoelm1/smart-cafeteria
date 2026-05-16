import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["FLASK_ENV"] = "testing"

from app import create_app
from app.extensions import db
from app.seed import seed_all, DEMO_PASSWORD


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def demo_password():
    return DEMO_PASSWORD


def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


@pytest.fixture
def login_as(client, demo_password):
    def _login(email):
        return login(client, email, demo_password)
    return _login
