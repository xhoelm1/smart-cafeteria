from datetime import datetime, date, time
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


ROLE_STUDENT = "student"
ROLE_STAFF = "staff"
ROLE_ADMIN = "admin"
VALID_ROLES = {ROLE_STUDENT, ROLE_STAFF, ROLE_ADMIN}

ORDER_STATUSES = ["pending", "confirmed", "preparing", "ready", "completed", "cancelled"]


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_STUDENT)
    is_active_flag = db.Column(db.Boolean, default=True, nullable=False)

    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")
    notifications = db.relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        return bool(self.is_active_flag)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


class MenuItem(TimestampMixin, db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Numeric(8, 2), nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    category = db.Column(db.String(60), nullable=False, default="Main")
    image_url = db.Column(db.String(255), default="")

    @property
    def stock_status(self) -> str:
        if not self.is_available or self.stock <= 0:
            return "sold_out"
        if self.stock < 5:
            return "low"
        return "in_stock"

    def __repr__(self) -> str:
        return f"<MenuItem {self.name}>"


class TimeSlot(TimestampMixin, db.Model):
    __tablename__ = "time_slots"

    id = db.Column(db.Integer, primary_key=True)
    slot_time = db.Column(db.Time, nullable=False)
    date = db.Column(db.Date, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=10)

    orders = db.relationship("Order", back_populates="time_slot")

    __table_args__ = (UniqueConstraint("date", "slot_time", name="uq_date_slot"),)

    @property
    def booked_count(self) -> int:
        return sum(1 for o in self.orders if o.status != "cancelled")

    @property
    def is_full(self) -> bool:
        return self.booked_count >= self.capacity

    @property
    def label(self) -> str:
        return f"{self.date.isoformat()} {self.slot_time.strftime('%H:%M')}"

    def __repr__(self) -> str:
        return f"<TimeSlot {self.label}>"


class Order(TimestampMixin, db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey("time_slots.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    user = db.relationship("User", back_populates="orders")
    time_slot = db.relationship("TimeSlot", back_populates="orders")
    items = db.relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def can_cancel(self) -> bool:
        return self.status in ("pending", "confirmed")

    def can_advance(self) -> str | None:
        order = ["pending", "confirmed", "preparing", "ready", "completed"]
        if self.status in order and self.status != "completed":
            return order[order.index(self.status) + 1]
        return None

    def __repr__(self) -> str:
        return f"<Order #{self.id} {self.status}>"


class OrderItem(TimestampMixin, db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(8, 2), nullable=False, default=0)

    order = db.relationship("Order", back_populates="items")
    menu_item = db.relationship("MenuItem")

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.unit_price) * self.quantity


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship("User", back_populates="notifications")
