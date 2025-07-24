# tasks/car-registration-tasks/__init__.py
from car_registration.web.users.api import auth_bp
from car_registration.web.cars.api import cars_bp
# from process.web.visualization import visualization as visualization_blueprint


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(cars_bp)



    # app.register_blueprint(dashboard_blueprint, url_prefix="/v1/bot")