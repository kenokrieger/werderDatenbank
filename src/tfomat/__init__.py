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
from os import mkdir
from os.path import join, exists

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_restful import Api

from tfomat.models import db


def init_app():
    """Create Flask application."""
    app = Flask(__name__, instance_relative_config=False)
    Bootstrap(app)
    app.config.from_object('tfomat.config.Config')
    cache_path = join(app.root_path, "cache")
    if not exists(cache_path):
        mkdir(cache_path)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        from tfomat.views import nav, views, add_resources
        nav.init_app(app)
        app.register_blueprint(views)
        api = Api(app)
        add_resources(api)
        return app


def _up():
    app = init_app()
    app.run(port=app.config["PORT"])
