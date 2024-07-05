from datetime import datetime, timedelta
from collections import namedtuple
from athletes.scraping import ladv

from athletes import db
from athletes.map import map_to_number, get_season_start, INVERSE_DISCIPLINE_MAPPER


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
        if type(date) is str:
            date = datetime.strptime(date, "%d.%m.%Y")
        performances = Performance.query.filter_by(
            athlete_id=self.id, discipline=discipline)
        start_date = _get_valid_pb_start_date(discipline, date,
                                              self.year_of_birth, self.gender)
        performances = [
            p for p in performances
            if start_date <= datetime.strptime(p.date, "%d.%m.%Y") <= date
        ]
        for pb in sorted(performances, key=lambda x: map_to_number(x.value),
                         reverse=ASCENDING.get(discipline, False)):
            if map_to_number(pb.value) > 0:
                return pb
        performance = namedtuple("Performance", ["value"])
        return performance(value=None)

    def get_seasons_best(self, discipline, date=None):
        if date is None:
            date = datetime.today()
        if type(date) is str:
            date = datetime.strptime(date, "%d.%m.%Y")
        season_start = get_season_start(date)
        performances = Performance.query.filter_by(
            athlete_id=self.id, discipline=discipline)
        season_performances = []
        for p in performances:
            pdate = datetime.strptime(p.date, "%d.%m.%Y")
            if season_start <= pdate <= date:
                season_performances.append(p)
        for sb in sorted(season_performances, key=lambda x: map_to_number(x.value),
                         reverse=ASCENDING.get(discipline, False)):
            if map_to_number(sb.value) > 0:
                return sb
        performance = namedtuple("Performance", ["value"])
        return performance(value=None)

    def is_personal_best(self, discipline, value, date=None):
        return value == self.get_personal_best(discipline, date).value

    def is_seasons_best(self, discipline, value, date=None):
        return value == self.get_seasons_best(discipline, date).value

    def is_record(self, discipline, value, date=None):
        if date is None:
            date = datetime.today()
        if type(date) is str:
            date = datetime.strptime(date, "%d.%m.%Y")
        date -= timedelta(days=1)
        previous_pb = self.get_personal_best(discipline, date)
        previous_sb = self.get_seasons_best(discipline, date)

        pb_rating = map_to_number(previous_pb.value)
        sb_rating = map_to_number(previous_sb.value)
        performance_rating = map_to_number(value)

        if performance_rating < 0:
            return "", None

        if not previous_pb.value:
            return "PB", None

        ascending = ASCENDING.get(discipline, False)

        if ascending:
            if performance_rating > pb_rating:
                return "PB", previous_pb
            if value == previous_pb.value:
                return "=PB", previous_pb
            if not previous_sb.value:
                return "SB", None
            if performance_rating > sb_rating:
                return "SB", previous_sb
            if value == previous_sb.value:
                return "=SB", previous_sb
        else:
            if performance_rating < pb_rating:
                return "PB", previous_pb
            if value == previous_pb.value:
                return "=PB", previous_pb
            if not previous_sb.value:
                return "SB", None
            if performance_rating < sb_rating:
                return "SB", previous_sb
            if value == previous_sb.value:
                return "=SB", previous_sb

        return "", None

    def get_disciplines(self):
        performances = Performance.query.filter_by(athlete_id=self.id).all()
        disciplines = [p.discipline for p in performances]

        common_disciplines = []
        for discipline in set(disciplines):
            entry = {"discipline": discipline, "pb": None, "sb": None,
                     "count": disciplines.count(discipline)}
            pb = self.get_personal_best(discipline)
            sb = self.get_seasons_best(discipline)
            if pb.value is not None:
                entry["pb"] = pb.to_dict()
            if sb.value is not None:
                entry["sb"] = sb.to_dict()
            common_disciplines.append(entry)

        common_disciplines.sort(key=lambda x: -x["count"])

        for discipline in common_disciplines:
            discipline["discipline"] = INVERSE_DISCIPLINE_MAPPER.get(
                discipline["discipline"], discipline["discipline"])

        return common_disciplines

    def get_upcoming_competitions(self):
        if self.ladv_id is None:
            try:
                self.ladv_id = ladv.get_ladv_id(self.name)
                db.session.commit()
            except:
                pass
        upcoming_competitions = ladv.get_upcoming_competitions(self.ladv_id)

        for competition in upcoming_competitions:
            for discipline in competition["wettbewerbe"]:
                discipline["disziplin"] = INVERSE_DISCIPLINE_MAPPER.get(
                    discipline["disziplin"], discipline["disziplin"])

        return upcoming_competitions

    def get_last_competitions(self):
        performances = Performance.query.filter_by(athlete_id=self.id).all()
        dates = sorted(
            list(set([p.date for p in performances])),
            key=lambda x: datetime.strptime(x, "%d.%m.%Y").timestamp()
        )
        date_threshold = dates[-min(3, len(dates))]
        datetime_threshold = datetime.strptime(date_threshold, "%d.%m.%Y")
        last_competitions = [
            p.to_dict() for p in performances
            if datetime.strptime(p.date, "%d.%m.%Y") >= datetime_threshold
        ]
        last_competitions.sort(
            key=lambda x: datetime.strptime(x["date"], "%d.%m.%Y").timestamp()
        )
        for competition in last_competitions:
            competition["discipline"] = INVERSE_DISCIPLINE_MAPPER.get(
                competition["discipline"], competition["discipline"])
        last_competitions.reverse()

        for competition in last_competitions:
            wind = competition["wind"]
            if competition["wind"] is None:
                continue
            wind_fmt = ("+" if wind > 0 else "") + f"{wind:.1f}"
            competition["wind"] = wind_fmt
        return last_competitions

    def get_athlete_info(self):
        return {
            "upcoming_competitions": self.get_upcoming_competitions(),
            "last_competitions": self.get_last_competitions(),
            "disciplines": self.get_disciplines()
        }

    def add_performances(self, performances):
        for p in performances:
            existing_performance = Performance.query.filter_by(date=p["datum"],
                                                               city=p["ort"],
                                                               athlete_id=self.id,
                                                               value=p["leistung"]
                                                               )
            if existing_performance.first() is not None:
                continue

            wind = p.get("wind")
            if wind:
                wind = float(wind.replace(",", "."))

            new_performance = Performance(
                date=p["datum"],
                city=p["ort"],
                athlete_id=self.id,
                discipline=p["disziplin"],
                value=p["leistung"],
                unit=None,
                wind=wind,
                placement=None,
                championship=None,
                indoor=True if p["halle"] == "true" else False
            )
            db.session.add(new_performance)
        db.session.commit()
        return None


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

    def update(self, data):
        self.date = data.get("date", self.date)
        self.city = data.get("city", self.city)
        self.athlete_id = data.get("athlete_id", self.athlete_id)
        self.discipline = data.get("discipline", self.discipline)
        self.value = data.get("value", self.value)
        self.unit = data.get("unit", self.unit)
        self.wind = data.get("wind", self.wind)
        self.placement = data.get("placement", self.placement)
        self.championship = data.get("championship", self.championship)
        self.indoor = data.get("indoor", self.indoor)
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "city": self.city,
            "athlete_id": self.athlete_id,
            "discipline": self.discipline,
            "value": self.value,
            "unit": self.unit,
            "wind": self.wind,
            "placement": self.placement,
            "indoor": self.indoor
        }


def _get_valid_pb_start_date(discipline, date, year_of_birth, gender):
    #  60 m Hurdles (60H): WU14, WU16, WU18, WU20 + W, MU14, MU16, MU18, MU20, M
    # 100 m Hurdles (100H): WU18, WU20 + W
    # 110 m Hurdles (110H): MU18, MU20, M
    # Shot Put      (KUG): WU14-U18, WU20, W, MU14, MU16, MU18, MU20, M
    # Javelin       (SPE): WU14, WU16-U18, WU20 + W, MU14, MU16, MU18, MU20 + M
    # Discus        (DIS): WU14, WU16-W, MU14, MU16, MU18, MU20, M
    # Hammer
    # This function is not readable but makes sense
    changing_events = ["60H", "100H", "110H", "KUG", "SPE", "DIS"]
    if discipline not in changing_events:
        return datetime(1900, 1, 1)

    infinity = datetime(1900, 1, 1)
    athlete_age = date.year - year_of_birth
    if athlete_age < 14:
        return infinity

    if discipline == "60H":
        if gender == "W" and athlete_age > 19:
            return datetime(date.year - (athlete_age - 18), 1, 1)
        if athlete_age > 19:
            return datetime(date.year - (athlete_age - 20), 1, 1)

    elif discipline == "100H":
        if gender == "M" or athlete_age < 18:
            return infinity
        if athlete_age > 19:
            return datetime(date.year - (athlete_age - 18), 1, 1)

    elif discipline == "110H":
        if athlete_age > 19:
            return datetime(date.year - (athlete_age - 20), 1, 1)

    elif discipline == "KUG":
        if gender == "W" and athlete_age < 18:
            return infinity
        if athlete_age > 19:
            return datetime(date.year - (athlete_age - 20), 1, 1)

    elif discipline == "SPE":
        if gender == "W" and athlete_age < 18:
            return datetime(date.year - (athlete_age - 14), 1, 1)
        if athlete_age > 19:
            return datetime(date.year - (athlete_age - 18), 1, 1)

    elif discipline == "DIS":
        if gender == "W":
            return datetime(date.year - (athlete_age - 14), 1, 1)
        if gender == "M" and athlete_age > 19:
            return datetime(date.year - (athlete_age - 20), 1, 1)

    return datetime(date.year - (athlete_age % 2), 1, 1)


class QualificationNorm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    agegroup = db.Column(db.String(150))
    gender = db.Column(db.String(150))
    discipline = db.Column(db.String(150))
    value = db.Column(db.String(150))
    indoor = db.Column(db.Boolean)

    def update(self, data):
        self.title = data.get("title", self.title)
        self.agegroup = data.get("agegroup", self.agegroup)
        self.gender = data.get("gender", self.gender)
        self.discipline = data.get("discipline", self.discipline)
        self.value = data.get("value", self.value)
        self.indoor = data.get("indoor", self.indoor)
        db.session.commit()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "agegroup": self.agegroup,
            "gender": self.gender,
            "discipline": self.discipline,
            "value": self.value,
            "indoor": self.indoor
        }


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
