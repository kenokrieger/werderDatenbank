"""Initialize Flask app."""
import os
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

from dotenv import load_dotenv

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


def _check_env_variables():
    load_dotenv()
    api_key = os.getenv("API-KEY")
    ladv_key = os.getenv("LADV-API-KEY")
    if not api_key:
        print(
            "Could not find a valid API key for the application. "
            "Please choose an API key by either specifying it in a "
            ".env file or by setting the 'API-KEY' environment variable.\n\n"
        )
        return False
    if not ladv_key:
        print(
            "WARNING: LADV-API-KEY not set! To integrate ladv within your "
            "application please specify a valid API key in the '.env' file "
            "or set the 'LADV-API-KEY' environment variable.\n\n"
        )
    return True


def _up():
    if not _check_env_variables():
        return -1
    app = init_app()
    app.run(port=app.config["PORT"])
