"""Initialize Flask app."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_restful import Api
# Database setup
db = SQLAlchemy()


def init_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    Bootstrap(app)
    app.config.from_object('athletes.config.Config')
    db.init_app(app)
    with app.app_context():
        from athletes.models.models import Athlete, Performance
        db.create_all()
        from athletes.views.routes import nav, views, add_resources
        nav.init_app(app)
        app.register_blueprint(views)
        api = Api(app)
        add_resources(api)
        return app
