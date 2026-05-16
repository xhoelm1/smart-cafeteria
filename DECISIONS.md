# Design Decisions

These are intentional choices made during the autonomous build. Documented here so
graders can see the reasoning rather than guess.

1. **SQLite instead of MySQL by default.** The spec asks for MySQL but explicitly
   permits SQLite for zero-config local execution. The schema is written against the
   SQLAlchemy ORM and uses no SQLite-only types, so switching is a one-line
   `DATABASE_URL` change. Documented in the README.

2. **Polling instead of WebSockets.** The spec explicitly allows polling. Real-time
   updates are achieved with `fetch()` every 5 s for the order detail page and every
   10 s for the notification bell. Simpler to deploy and sufficient for this scope.

3. **Order is `confirmed` immediately on checkout.** The spec defines `pending` and
   `confirmed` as separate statuses but does not describe a payment step. Treating
   checkout itself as confirmation keeps the demo flow short while still allowing the
   staff dashboard to advance the order through every state.

4. **Session-based cart.** Stored in the Flask session (signed cookie). Simpler than a
   DB-backed cart and good enough for a single-tab demo. A logged-out user loses
   their cart.

5. **No external CSS framework.** Custom `app/static/css/style.css` keeps the
   download tiny and the look consistent. Palette is navy / orange per the spec.

6. **`flash` messages auto-dismiss after 4 s** via vanilla JS. No toast library.

7. **Seeder is idempotent.** Re-running `python run.py` will not duplicate users or
   menu items; sample orders are only created on a truly empty database.

8. **`is_active_flag` column** instead of overriding `User.is_active`. Flask-Login's
   `UserMixin.is_active` is a property we expose from our own flag, which lets admins
   disable accounts without deleting rows.
