from datetime import datetime, timedelta

from athletes import db
from athletes.map import map_to_number, get_season_start


class Athlete(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    year_of_birth = db.Column(db.Integer)
    gender = db.Column(db.String(150))
    ladv_athlete_number = db.Column(db.Integer)
    ladv_id = db.Column(db.Integer)

    def get_personal_best(self, discipline, date=None):
        if date is None:
            date = datetime.today()
        if type(date) == str:
            date = datetime.strptime(date, "%d.%m.%Y")
        performances = Performance.query.filter_by(
            athlete_id=self.id, discipline=discipline)
        performances = [p for p in performances if datetime.strptime(
            p.date, "%d.%m.%Y") <= date]
        for pb in sorted([p.value for p in performances], key=map_to_number,
                         reverse=ASCENDING.get(discipline, False)):
            if map_to_number(pb) > 0:
                return pb
        return ""

    def get_seasons_best(self, discipline, date=None):
        if date is None:
            date = datetime.today()
        if type(date) == str:
            date = datetime.strptime(date, "%d.%m.%Y")
        season_start = get_season_start(date)
        performances = Performance.query.filter_by(
            athlete_id=self.id, discipline=discipline)
        season_performances = []
        for p in performances:
            pdate = datetime.strptime(p.date, "%d.%m.%Y")
            if season_start <= pdate <= date:
                season_performances.append(p.value)
        for sb in sorted(season_performances, key=map_to_number,
                         reverse=ASCENDING.get(discipline, False)):
            if map_to_number(sb) > 0:
                return sb
        return ""

    def is_personal_best(self, discipline, value, date=None):
        return value == self.get_personal_best(discipline, date)

    def is_seasons_best(self, discipline, value, date=None):
        return value == self.get_seasons_best(discipline, date)

    def is_record(self, discipline, value, date=None):
        if date is None:
            date = datetime.today()
        if type(date) == str:
            date = datetime.strptime(date, "%d.%m.%Y")
        date -= timedelta(days=1)
        previous_pb = self.get_personal_best(discipline, date)
        previous_sb = self.get_seasons_best(discipline, date)

        pb_rating = map_to_number(previous_pb)
        sb_rating = map_to_number(previous_sb)
        performance_rating = map_to_number(value)

        if performance_rating < 0:
            return ""

        if not previous_pb:
            return "PB"

        ascending = ASCENDING.get(discipline, False)

        if ascending:
            if performance_rating > pb_rating:
                return "PB"
            if value == previous_pb:
                return "=PB"
            if not previous_sb:
                return "SB"
            if performance_rating > sb_rating:
                return "SB"
            if value == previous_sb:
                return "=SB"
        else:
            if performance_rating < pb_rating:
                return "PB"
            if value == previous_pb:
                return "=PB"
            if not previous_sb:
                return "SB"
            if performance_rating < sb_rating:
                return "SB"
            if value == previous_sb:
                return "=SB"

        return ""


class Performance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(150))
    city = db.Column(db.String(150))
    athlete_id = db.Column(db.Integer, db.ForeignKey('athlete.id'))
    discipline = db.Column(db.String(150))
    value = db.Column(db.String(150))
    unit = db.Column(db.String(150))
    wind = db.Column(db.Float)
    placement = db.Column(db.Integer)
    championship = db.Column(db.String(150))
    indoor = db.Column(db.Boolean)


ASCENDING = {
    "60H": False,
    "80H": False,
    "100H": False,
    "110H": False,
    "300H": False,
    "400H": False,
    "HOC": True,
    "4-K": True,
    "SPE": True,
    "BLL": True,
    "DRE": True,
    "9-K": True,
    "600": False,
    "60": False,
    "BLM": True,
    "4-M": True,
    "WEI": True,
    "1KO": False,
    "3KO": False,
    "10S": False,
    "HALM": True,
    "3x1": False,
    "75": False,
    "5S": False,
    "MAR": False,
    "30": False,
    "7-M": True,
    "3-M": True,
    "400": False,
    "HAL": False,
    "KUG": True,
    "BLS": True,
    "5KO": False,
    "100": False,
    "DIS": True,
    "2KO": False,
    "BLB": True,
    "50": False,
    "4X7": False,
    "200": False,
    "9-M": True,
    "10K": False,
    "3-K": True,
    "4X1": False,
    "BAL": True,
    "3X8": False,
    "WEZ": True,
    "4X4": False,
    "15S": False,
    "MEI": False,
    "800": False,
    "7-K": True,
    "STA": True,
    "1K5": False,
    "5-K": True,
    "10-K": True,
    "SCH": False,
    "4X5": False,
    "BLW": True,
    "300": False,
    "4X2": False
}
