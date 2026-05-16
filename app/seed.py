from datetime import date, time, timedelta
from decimal import Decimal

from app.extensions import db
from app.models import (
    User, MenuItem, TimeSlot, Order, OrderItem,
    ROLE_ADMIN, ROLE_STAFF, ROLE_STUDENT,
)


DEMO_PASSWORD = "Demo1234!"


DEMO_USERS = [
    ("admin@cafeteria.edu", "Xhesilda Kullolli", ROLE_ADMIN),
    ("staff@cafeteria.edu", "Cafeteria Staff", ROLE_STAFF),
    ("student1@cafeteria.edu", "Erisilda Zhaboli", ROLE_STUDENT),
    ("student2@cafeteria.edu", "Megi Bicaku", ROLE_STUDENT),
    ("student3@cafeteria.edu", "Xhoel Merkuli", ROLE_STUDENT),
]


MENU_ITEMS = [
    # (name, description, price, stock, category, image)
    ("Byrek me Spinaq", "Flaky Albanian pastry with spinach and feta.", 150, 12, "Main", ""),
    ("Suxhuk Sandwich", "Grilled spiced sausage in a fresh baguette.", 250, 8, "Main", ""),
    ("Caesar Salad", "Crisp romaine, parmesan, croutons, classic dressing.", 320, 6, "Main", ""),
    ("Pizza Slice Margherita", "Wood-fired tomato, mozzarella, basil.", 200, 15, "Main", ""),
    ("Pasta Bolognese", "Slow-cooked beef ragu over al dente pasta.", 380, 10, "Main", ""),
    ("Chicken Wrap", "Grilled chicken, lettuce, garlic yogurt sauce.", 290, 9, "Main", ""),
    ("Greek Salad", "Tomato, cucumber, olives, feta, oregano.", 300, 7, "Main", ""),
    ("Espresso", "Single shot of Italian-style espresso.", 80, 30, "Drink", ""),
    ("Cappuccino", "Espresso with steamed milk foam.", 150, 25, "Drink", ""),
    ("Orange Juice", "Freshly squeezed local oranges.", 180, 14, "Drink", ""),
    ("Water Bottle 0.5L", "Still mineral water.", 70, 50, "Drink", ""),
    ("Lemonade", "Homemade lemonade with mint.", 160, 12, "Drink", ""),
    ("Chocolate Croissant", "Buttery croissant with dark chocolate.", 180, 10, "Snack", ""),
    ("Tiramisu", "Layered mascarpone, coffee, cocoa.", 260, 6, "Dessert", ""),
    ("Brownie", "Rich dark chocolate brownie.", 200, 8, "Dessert", ""),
]


def _ensure_users() -> dict[str, User]:
    out = {}
    for email, name, role in DEMO_USERS:
        existing = User.query.filter_by(email=email).first()
        if existing:
            if not existing.is_active_flag:
                existing.is_active_flag = True
            out[email] = existing
            continue
        u = User(email=email, name=name, role=role)
        u.set_password(DEMO_PASSWORD)
        db.session.add(u)
        out[email] = u
    db.session.commit()
    return out


def _ensure_menu() -> list[MenuItem]:
    out = []
    for name, desc, price, stock, category, img in MENU_ITEMS:
        existing = MenuItem.query.filter_by(name=name).first()
        if existing:
            out.append(existing)
            continue
        item = MenuItem(
            name=name,
            description=desc,
            price=Decimal(price),
            stock=stock,
            category=category,
            is_available=True,
            image_url=img,
        )
        db.session.add(item)
        out.append(item)
    db.session.commit()
    return out


def _ensure_time_slots() -> list[TimeSlot]:
    out = []
    today = date.today()
    days = [today + timedelta(days=i) for i in range(7)]
    minutes = [(h, m) for h in range(9, 18) for m in (0, 15, 30, 45)]
    for d in days:
        for h, m in minutes:
            t = time(h, m)
            existing = TimeSlot.query.filter_by(date=d, slot_time=t).first()
            if existing:
                out.append(existing)
                continue
            slot = TimeSlot(date=d, slot_time=t, capacity=10)
            db.session.add(slot)
            out.append(slot)
    db.session.commit()
    return out


def _ensure_sample_orders(users: dict[str, User], slots: list[TimeSlot], menu: list[MenuItem]) -> None:
    if Order.query.count() > 0:
        return
    today = date.today()
    today_slots = [s for s in slots if s.date == today][:6] or slots[:6]
    student1 = users["student1@cafeteria.edu"]
    student2 = users["student2@cafeteria.edu"]
    student3 = users["student3@cafeteria.edu"]

    def mk_order(student, slot, items, status):
        order = Order(user_id=student.id, time_slot_id=slot.id, status=status, total=0)
        db.session.add(order)
        db.session.flush()
        total = Decimal(0)
        for item, qty in items:
            oi = OrderItem(
                order_id=order.id,
                menu_item_id=item.id,
                quantity=qty,
                unit_price=item.price,
            )
            total += Decimal(item.price) * qty
            db.session.add(oi)
        order.total = total
        return order

    mk_order(student1, today_slots[0], [(menu[0], 1), (menu[7], 1)], "pending")
    mk_order(student2, today_slots[1], [(menu[3], 2), (menu[9], 1)], "preparing")
    mk_order(student3, today_slots[2], [(menu[5], 1), (menu[11], 1)], "ready")
    db.session.commit()


def seed_all() -> None:
    users = _ensure_users()
    menu = _ensure_menu()
    slots = _ensure_time_slots()
    _ensure_sample_orders(users, slots, menu)


def seed_if_empty() -> None:
    if User.query.count() == 0:
        seed_all()
        return
    _ensure_users()
    _ensure_menu()
    _ensure_time_slots()
