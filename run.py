import os
from app import create_app
from app.seed import seed_if_empty

app = create_app()

with app.app_context():
    seed_if_empty()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port, host="127.0.0.1")
