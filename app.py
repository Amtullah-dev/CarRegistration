from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from config import Config
from car_registration.models.database import db
from car_registration.web import register_routes

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
register_routes(app)

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, host='0.0.0.0', port=5000)
