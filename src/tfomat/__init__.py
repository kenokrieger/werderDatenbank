"""Initialize Flask app."""
# Copyright (C) 2024  Keno Krieger <kriegerk@uni-bremen.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy

# Database setup
db = SQLAlchemy()


def init_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    Bootstrap(app)
    app.config.from_object('athletes.config.Config')
    db.init_app(app)
    with app.app_context():
        db.create_all()
        from tfomat.views import nav, views, add_resources
        nav.init_app(app)
        app.register_blueprint(views)
        api = Api(app)
        add_resources(api)
        return app
