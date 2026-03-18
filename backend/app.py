import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from flask_cors import CORS
from backend.routes.auth_api import auth
from backend.routes.admin import admin
from backend.routes.transport_requests_api import transport_requests
from backend.routes.bookings_api import bookings
from backend.routes.ratings_api import ratings

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(auth, url_prefix="/api")
    app.register_blueprint(admin, url_prefix="/api")
    app.register_blueprint(transport_requests)
    app.register_blueprint(bookings, url_prefix="/api")
    app.register_blueprint(ratings)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)