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
import os

from dotenv import load_dotenv

load_dotenv()





class Config:
    ENV = "development"
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(__file__.replace('config.py', ''), 'database/database.db')}"
    API_KEY = os.getenv("API-KEY")
    LADV_API_KEY = os.getenv("LADV-API-KEY")
    CLUB_NAME = "SV Werder Bremen"
    CLUB_ID = 25
