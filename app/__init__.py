from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('instance.config.Config')
    app.config.from_pyfile('instance.config.py', silent=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # with app.app_context():
    #     db.create_all()

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes import main as main_routes
    app.register_blueprint(main_routes)

    return app