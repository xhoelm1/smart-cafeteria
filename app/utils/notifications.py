from app.extensions import db
from app.models import Notification


def notify(user_id: int, message: str) -> Notification:
    n = Notification(user_id=user_id, message=message)
    db.session.add(n)
    db.session.commit()
    return n
