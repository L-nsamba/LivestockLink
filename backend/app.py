from flask import Flask
from flask_cors import CORS
from backend.routes.auth_api import auth

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(auth, url_prefix="/api")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)