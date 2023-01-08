"""Initialize Flask app."""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Database setup
db = SQLAlchemy()


def init_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)

    app.config.from_object('athletes.config.Config')  # configure app using the Config class defined in src/config.py

    db.init_app(app)  # initialise the database for the app

    with app.app_context():
        # this import allows us to create the table if it does not exist
        from athletes.models.models import Athlete, Performance
        db.create_all()

        from athletes.views.routes import views
        app.register_blueprint(views)

        return app
