import json
import os
from datetime import datetime
from hmac import compare_digest

from flask import Blueprint, render_template, request, url_for, redirect, \
    send_from_directory, current_app, abort
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from flask_restful import Resource
from tfomat import db
from tfomat.ladv_scraper import find_results, get_werder_results, \
    get_werder_events, get_athlete_info, get_ladv_id
from tfomat.map import map_discipline, DISCIPLINE_MAPPER, map_to_number, \
    INVERSE_DISCIPLINE_MAPPER
from tfomat.models import Athlete, Performance, ASCENDING, \
    QualificationNorm
from tfomat.print import make_pdf

nav = Nav()
views = Blueprint('views', __name__)


@nav.navigation()
def navbar():
    """
    Create a navigation menu for the application.

    Returns:
        Navbar: If the user is authenticated return the navigation menu with
            links for the different features of the application else return
            the navigation menu with links for sign up and sign in.

    """
    return Navbar(
        View("Werder Datenbank", "views.index"),
        View("Athleten", "views.athlete_overview"),
        View("Wettkampfergebnisse", "views.event_results"),
        View("Anstehende Wettkämpfe", "views.coming_events"),
        View("Bestenlisten", "views.rankings")
    )


@views.route("/")
def index():
    return render_template("index.html")


@views.route('/athletes')
def athlete_overview():
    athletes = Athlete.query.all()
    return render_template('athletes.html', athletes=athletes)


@views.route('/performances')
def performance_overview():
    performances = Performance.query.all()
    return render_template('performances.html', performances=performances)


@views.route("/results/<int:meeting_id>")
def show_results(meeting_id):
    cached_file = "athletes/cache/{}.html".format(meeting_id)

    if os.path.exists(cached_file):
        with open(cached_file, "r", encoding="utf-8") as f:
            return f.read()

    meeting_info, results = find_results(meeting_id)

    if meeting_info is None:
        return "Keine Ergebnisse verfügbar, vielleicht kannst du sie hier finden: https://ladv.de/veranstaltung/detail/{}/".format(meeting_id)
    title = f"{meeting_info['title']} am {meeting_info['date']}" \
            f" in {meeting_info['city']}\n"

    city = meeting_info["city"]
    _update_database(city, results, championship=request.args.get("championship"))

    medals = {"&#129351;": 0, "&#129352;": 0, "&#129353;": 0}
    for medal in medals:
        medal_count = sum(medal in r.get("medal", "") for r in results)
        medals[medal] = medal_count
    page = render_template("results.html", title=title, results=results, len=len, medals=medals)
    with open(cached_file, "w", encoding="utf-8") as f:
        f.write(page)
    return page


def _move_nans_to_bottom(results):
    contains_digits = lambda s: any(d in s for d in "1 2 3 4 5 6 7 8 9".split())

    real_results = [r for r in results if contains_digits(r["result"])]
    nan_results = [r for r in results if
                   not contains_digits(r["result"])]
    return real_results + nan_results


def _sort_by_result(value):
    digits = "".join(c for c in value["result"] if c.isdigit())
    if not digits:
        return 0
    return int(digits)


@views.route("/results/print-view/<int:meeting_id>")
def print_results(meeting_id):
    cached_file = "athletes/cache/{}.pdf".format(meeting_id)
    wdir = os.path.join(current_app.root_path, "cache/")
    if os.path.exists(cached_file):
        return send_from_directory(directory=wdir,
                                   path=f"./{meeting_id}.pdf")

    meeting_info, results = find_results(meeting_id)
    title = f"{meeting_info['title']}"
    subtitle = f"am {meeting_info['date']} in {meeting_info['city']}"
    _update_database(meeting_info['city'], results, championship=request.args.get("championship"))

    agegroups = sorted(list(set(r["agegroup"] for r in results)))
    print_view = dict()
    for agegroup in agegroups:
        events = [r for r in results if r["agegroup"] == agegroup]
        disc = sorted(list(set(e["event"] for e in events)))
        print_view[agegroup] = {}
        for d in disc:
            matches = [e for e in events if e["event"] == d]
            matches.sort(key=_sort_by_result)
            is_sprint = any(digit in d for digit in "123456789")
            if not is_sprint:
                matches.reverse()
            matches = _move_nans_to_bottom(matches)
            print_view[agegroup][d] = matches
    make_pdf(print_view, title, subtitle, name=f"athletes/cache/{meeting_id}")
    return send_from_directory(directory=wdir,
                               path=f"./{meeting_id}.pdf")


def _update_database(city, results, championship=None):
    medals = {"1": r"&#129351;", "2": r"&#129352;", "3": r"&#129353;"}
    for result in results:
        result["athlete_id"] = None
        athlete = Athlete.query.filter_by(name=result["name"]).first()
        if athlete is None:
            result["pborsb"] = "?"
            result["tooltip"] = "Athlet nicht in der Datenbank"
            continue
        result["athlete_id"] = athlete.id
        result["pborsb"] = ""
        date = result["date"]
        value = result["result"]
        event = map_discipline(result["event"])
        rank = result["rank"].replace(".", "")
        if any([a in result["subtitle"] for a in ("Final", "Rangfolge")]):
            result["medal"] = medals.get(rank, "")
        try:
            placement = int(rank)
        except ValueError:
            placement = 0

        existing_entry = Performance.query.filter_by(date=date, value=value,
                                                     athlete_id=athlete.id).first()
        if existing_entry:
            if existing_entry.placement is None:
                existing_entry.placement = placement
            existing_entry.championship = championship
            entry = existing_entry
        else:
            month = int(date.split(".")[1])
            wind = result["wind"].replace(",", ".")

            new_performance = Performance(
                date=date,
                city=city,
                athlete_id=athlete.id,
                discipline=event,
                value=value,
                unit=None,
                wind=float(wind) if wind else None,
                placement=placement,
                championship=championship,
                indoor=not 2 < month < 11
            )
            db.session.add(new_performance)
            entry = new_performance

        record_detail = athlete.is_record(entry.discipline, entry.value, date)
        result["pborsb"] = record_detail[0]
        p = record_detail[1]
        if p is None:
            result["tooltip"] = ""
        else:
            result["tooltip"] = f"{p.value} - {p.city}, den {p.date}"
    db.session.commit()
    return results


@views.route("/clear-results/<int:meeting_id>")
def clear_result_cache(meeting_id):
    cached_file_base = f"athletes/cache/{meeting_id}"
    for ext in (".html", ".pdf", ".tex"):
        cached_file = cached_file_base + ext
        if os.path.exists(cached_file):
            os.remove(cached_file)

    return redirect(url_for('views.get_results'))


@views.route("/get_result", methods=["GET", "POST"])
def get_results():
    if request.method == "POST":
        meeting_id = int(request.form.get("meeting_id"))
        return redirect(url_for('views.show_results', meeting_id=meeting_id))

    return render_template("results.html", title="", results=None)


@views.route("/events/<int:year>")
def events(year):
    return render_template("events.html", year=year, max_year=datetime.now().year)


@views.route("/events/")
def event_results():
    return events(datetime.now().year)


@views.route("/upcoming-events/")
def coming_events():
    new_events = get_werder_events()
    page = render_template("coming_events.html", events=new_events)
    return page


@views.route("/add-athlete/<name>")
def add_athlete(name):
    existing_athletes = Athlete.query.all()
    if name in [a.name for a in existing_athletes]:
        return "AthletIn existiert bereits in der Datenbank."

    ladv_id = get_ladv_id(name)
    start_year = 2010
    end_year = datetime.now().year
    athlete_info = get_athlete_info(ladv_id, start_year, end_year)
    new_athlete = Athlete(
        name=athlete_info["forename"] + " " + athlete_info["surname"],
        year_of_birth=athlete_info["birthyear"],
        gender=athlete_info["sex"],
        ladv_athlete_number=athlete_info["athletnumber"],
        ladv_id=ladv_id
    )
    db.session.add(new_athlete)
    db.session.commit()

    new_athlete.add_performances(athlete_info["leistungen"])

    return "AthletIn zur Datenbank hinzugefügt."


@views.route("/athletes/<athlete_id>")
def athlete_profile(athlete_id):
    athlete = Athlete.query.get(athlete_id)
    if athlete is None:
        return abort(404)
    return render_template("profile.html", athlete=athlete)


@views.route("/rankings")
def rankings():
    disciplines = DISCIPLINE_MAPPER.keys()
    years = [str(y) for y in range(2010, datetime.now().year + 1)] + ["Ewige"]
    return render_template("rankings.html", disciplines=disciplines, years=years)


@views.route("/database")
def manipulate_database():
    cities = [c[0] for c in db.session.query(Performance.city).distinct()]
    athletes = [a.name for a in Athlete.query.all()]
    form = [
        {"id": "date", "label": "Date", "list_id": "", "options": ""},
        {"id": "city", "label": "City", "list_id": "cities", "options": cities},
        {"id": "athlete", "label": "Athlete", "list_id": "athletes", "options": athletes},
        {"id": "discipline", "label": "Discipline", "list_id": "disciplines", "options": DISCIPLINE_MAPPER.keys()},
        {"id": "value", "label": "Value", "list_id": "", "options": ""},
        {"id": "unit", "label": "Unit", "list_id": "", "options": ""},
        {"id": "wind", "label": "Wind", "list_id": "", "options": ""},
        {"id": "placement", "label": "Placement", "list_id": "", "options": ""},
        {"id": "championship", "label": "Championship", "list_id": "championships", "options": ["DM", "NDM", "LM"]},
        {"id": "indoor", "label": "Indoor", "list_id": "indoor-select", "options": ["true", "false"]},
    ]
    return render_template("add_database_entry.html", form=form)


class AthleteInfo(Resource):
    """
    API Endpoint for getting data from a sensor.
    """

    def get(self):
        """GET method of the API"""
        athlete_id = request.args.get("id")
        if athlete_id is None:
            return {"error": "Missing parameters."}

        athlete = Athlete.query.get(athlete_id)
        return athlete.get_athlete_info()


class AthleteLastCompetitions(Resource):
    def get(self):
        athlete_id = request.args.get("id")
        if athlete_id is None:
            return {"error": "Missing parameters."}
        athlete = Athlete.query.get(athlete_id)
        return athlete.get_last_competitions()


class AthleteUpcomingCompetitions(Resource):
    def get(self):
        athlete_id = request.args.get("id")
        if athlete_id is None:
            return {"error": "Missing parameters."}
        athlete = Athlete.query.get(athlete_id)
        return athlete.get_upcoming_competitions()


class AthleteDisciplines(Resource):
    def get(self):
        athlete_id = request.args.get("id")
        if athlete_id is None:
            return {"error": "Missing parameters."}
        athlete = Athlete.query.get(athlete_id)
        return athlete.get_disciplines()


class AddDatabaseEntry(Resource):
    """
    API Endpoint for getting data from a sensor.
    """

    def post(self):
        """POST method of the API"""
        token = request.args.get("token")
        if not compare_digest(token, "lebenslanggruenweiss"):
            return {"status": "failed", "value": "forbidden"}

        overwrite = request.args.get("overwrite", False)
        required_keys = ["date", "city", "athlete", "discipline", "value",
                         "indoor"]

        payload = request.json
        if not all([k in payload for k in required_keys]):
            return {"status": "failed", "value": "Missing required values"}

        try:
            datetime.strptime(payload["date"], "%d.%m.%Y")
        except ValueError:
            return {"status": "failed", "value": "Could not interpret date. Expected format: dd.mm.yyyy"}

        athlete = Athlete.query.filter_by(name=payload["athlete"]).first()
        if not athlete:
            return {"status": "failed", "value": "Athlete does not exist"}
        payload["athlete_id"] = athlete.id

        if payload["discipline"] not in DISCIPLINE_MAPPER.items() and not DISCIPLINE_MAPPER.get(payload["discipline"]):
            return {"status": "failed", "value": "Discipline not recognized"}
        payload["discipline"] = DISCIPLINE_MAPPER.get(payload["discipline"], payload["discipline"])

        if map_to_number(payload["value"]) < 0:
            reason = "Value format not recognized. Expected formats: long distance: {}, sprint or technical event: {}, multievent: {}".format(
                "[0-9]*:[0-9][0-9],[0-9][0-9]",  # long distance
                "[0-9]*,[0-9]*",  # sprint or technical event
                "[0-9].[0-9][0-9][0-9]"  # multi-event"
            )
            return {"status": "failed", "value": reason}

        unit = payload.get("unit")
        if not unit:
            payload["unit"] = None

        wind = payload.get("wind")
        if wind:
            try:
                payload["wind"] = float(wind.replace(",", "."))
            except ValueError:
                return {"status": "failed", "value": "Wind format not recognized"}
        else:
            payload["wind"] = None

        placement = payload.get("placement")
        if placement:
            try:
                payload["placement"] = int(placement.replace(".", ""))
            except ValueError:
                return {"status": "failed", "value": "Placement format not recognized"}
        else:
            payload["placement"] = None

        championship = payload.get("championship")
        if not championship:
            payload["championship"] = None

        if payload["indoor"] not in ("true", "false"):
            return {"status": "failed", "value": "Indoor needs to be 'true' or 'false'"}
        payload["indoor"] = True if payload["indoor"] == "true" else False

        existing_performances = Performance.query.filter_by(
            date=payload["date"],
            city=payload["city"],
            athlete_id=payload["athlete_id"],
            discipline=payload["discipline"],
            value=payload["value"],
        ).all()
        if not existing_performances:
            performance_info = {
                k: payload[k] for k in ("date", "city", "athlete_id",
                                        "discipline", "value", "unit",
                                        "wind", "placement", "championship",
                                        "indoor")
            }
            new_performance = Performance(**performance_info)
            db.session.add(new_performance)
            db.session.commit()
            return {"status": "success", "value": new_performance.to_dict()}

        if not overwrite:
            return {"status": "pending", "value": [p.to_dict() for p in existing_performances]}

        payload["id"] = int(payload["id"])
        performance = Performance.query.get(payload["id"])
        performance.update(payload)
        return {"status": "success", "value": performance.to_dict()}


class AddQualificationNorm(Resource):
    """
    API Endpoint for getting data from a sensor.
    """

    def post(self):
        """POST method of the API"""
        token = request.args.get("token")
        if not compare_digest(token, "lebenslanggruenweiss"):
            return {"status": "failed", "value": "forbidden"}

        overwrite = request.args.get("overwrite", False)
        required_keys = ["title", "agegroup", "gender", "discipline", "value",
                         "indoor"]

        payload = request.json
        if not all([k in payload for k in required_keys]):
            return {"status": "failed", "value": "Missing required values"}

        if payload["discipline"] not in DISCIPLINE_MAPPER.items() and not DISCIPLINE_MAPPER.get(payload["discipline"]):
            return {"status": "failed", "value": "Discipline not recognized"}
        payload["discipline"] = DISCIPLINE_MAPPER.get(payload["discipline"], payload["discipline"])

        if map_to_number(payload["value"]) < 0:
            reason = "Value format not recognized. Expected formats: long distance: {}, sprint or technical event: {}, multievent: {}".format(
                "[0-9]*:[0-9][0-9],[0-9][0-9]",  # long distance
                "[0-9]*,[0-9]*",  # sprint or technical event
                "[0-9].[0-9][0-9][0-9]"  # multi-event"
            )
            return {"status": "failed", "value": reason}

        if payload["indoor"] not in ("true", "false"):
            return {"status": "failed", "value": "Indoor needs to be 'true' or 'false'"}
        payload["indoor"] = True if payload["indoor"] == "true" else False

        existing_norms = QualificationNorm.query.filter_by(
            agegroup=payload["agegroup"],
            gender=payload["gender"],
            discipline=payload["discipline"],
            value=payload["value"],
            indoor=payload["indoor"]
        ).all()
        if not existing_norms:
            norm_info = {
                k: payload[k] for k in ("title", "agegroup", "gender",
                                        "discipline", "value", "indoor")
            }
            new_norm = QualificationNorm(**norm_info)
            db.session.add(new_norm)
            db.session.commit()
            return {"status": "success", "value": new_norm.to_dict()}

        if not overwrite:
            return {"status": "pending", "value": [n.to_dict() for n in existing_norms]}

        payload["id"] = int(payload["id"])
        qualification_norm = QualificationNorm.query.get(payload["id"])
        qualification_norm.update(payload)
        return {"status": "success", "value": qualification_norm.to_dict()}


class Rankings(Resource):
    """
    API Endpoint for getting data from a sensor.
    """

    def get(self):
        """GET method of the API"""
        discipline = request.args.get("disc")
        year = request.args.get("year")
        agegroup = request.args.get("age")
        where = request.args.get("where")
        if not year or not discipline:
            return [["1", "Bitte Disziplin und Jahr auswählen", "", "", ""]]
        if not agegroup:
            agegroup = "Alle"
        if not where:
            where = "Halle + Freiluft"
        return self._get_rankings(agegroup, discipline, year, where)

    def _get_rankings(self, agegroup, discipline, year, where):
        agegroup_offset = {
            "U23": 22, "JU20": 19, "JU18": 17, "JU16": 15
        }.get(agegroup[1:], 100)
        if agegroup != "Alle":
            query_gender = "M" if agegroup[0] == "M" else "W"
            athletes = Athlete.query.filter_by(gender=query_gender).all()
        else:
            athletes = Athlete.query.all()
        performances = dict()
        athlete_dict = {a.id: a for a in athletes}

        query_disc = DISCIPLINE_MAPPER.get(discipline)

        query = Performance.query.filter_by(discipline=query_disc).filter(
            ~Performance.value.contains("a"),
            ~Performance.value.contains("d"),
            ~Performance.value.contains("o")
        )
        if year != "Ewige":
            query = query.filter(Performance.date.contains(year))
        if where != "Halle + Freiluft":
            query = query.filter_by(indoor=where == "Halle")
        for athlete in athletes:
            performances[athlete.id] = query.filter_by(athlete_id=athlete.id).all()

        ranking_performances = []
        for athlete_key in performances:
            athlete = athlete_dict[athlete_key]
            age = athlete.year_of_birth

            valid_performances = []
            for p in performances[athlete_key]:
                pyear = int(p.date.split(".")[-1])
                if pyear - age > agegroup_offset:
                    continue
                valid_performances.append(p)

            if not valid_performances:
                continue

            valid_performances.sort(
                key=lambda x: map_to_number(x.value),
                reverse=ASCENDING.get(DISCIPLINE_MAPPER[discipline], False)
            )
            best_performance = valid_performances[0]
            best_performance_year = int(best_performance.date.split(".")[-1])
            if year == "Ewige":
                athlete_age = datetime.now().year - age
            else:
                athlete_age = best_performance_year - age
            if athlete_age < 16:
                athlete_agegroup = "JU16"
            elif athlete_age < 18:
                athlete_agegroup = "JU18"
            elif athlete_age < 20:
                athlete_agegroup = "JU20"
            elif athlete_age < 23:
                athlete_agegroup = "U23"
            else:
                athlete_agegroup = ""

            if best_performance.wind is not None:
                value = f"{best_performance.value} ({'+' if best_performance.wind > 0.0 else ''}{best_performance.wind:.1f})"
            else:
                value = best_performance.value

            ranking_performance = [
                best_performance.value,
                athlete.name,
                athlete.gender + athlete_agegroup,
                value,
                f"{best_performance.city}, den {best_performance.date}"
            ]
            ranking_performances.append(ranking_performance)

        ranking_performances.sort(
            key=lambda x: map_to_number(x[0]),
            reverse=ASCENDING.get(DISCIPLINE_MAPPER[discipline], False)
        )

        return [[i + 1] + l[1:] for i, l in enumerate(ranking_performances)]


class AthletePerformances(Resource):
    def get(self):
        athlete_id = request.args.get("id")
        if not athlete_id:
            return {}

        performances = Performance.query.filter_by(athlete_id=athlete_id).all()
        fmt_performances = []
        for p in performances:
            if map_to_number(p.value) < 0:
                continue
            if not p.wind:
                value = p.value
            else:
                value = f"{p.value} ({'+' if p.wind > 0 else ''}{p.wind:.1f})"
            fmt_performances.append(
                [p.date, p.city, INVERSE_DISCIPLINE_MAPPER.get(p.discipline, p.discipline), value]
            )
        discipline_options = list(set([fp[2] for fp in fmt_performances]))
        year_options = list(set([fp[0].split(".")[-1] for fp in fmt_performances]))
        return {
            "discipline_options": discipline_options,
            "year_options": year_options,
            "table_data": fmt_performances
        }


class Events(Resource):
    def get(self):
        year = request.args.get("year")
        if not year:
            return {"status": "failed", "value": "parameter 'year' was not specified"}

        cached_file = f"athletes/cache/events_{year}.json"
        if os.path.exists(cached_file):
            with open(cached_file, "r") as f:
                cache = json.load(f)
        else:
            cache = None
        if int(year) == datetime.now().year or not cache:
            new_events = get_werder_results(year, cache=cache)
        else:
            new_events = cache

        fmt_events = [
            [
                e["datumText"].split("/")[-1],
                e["ort"],
                '<a href="{}">{}</a>'.format(
                    url_for("views.show_results", meeting_id=e["id"]),
                    e["name"]
                )
            ]
            for e in new_events
        ]
        return {"status": "success", "value": fmt_events}


def add_resources(api):
    """
    Add the API endpoints to the Flask app.

    Args:
        api (flask_restful.Api): The flask API object to add the endpoints to.

    Returns:
        None.
    """
    api.add_resource(AthleteInfo, "/api/athlete-info")
    api.add_resource(Rankings, "/api/ranking")
    api.add_resource(AddDatabaseEntry, "/api/add-database-entry")
    api.add_resource(AthletePerformances, "/api/athlete-performances")
    api.add_resource(Events, "/api/events")
    api.add_resource(AthleteDisciplines, "/api/athlete-disciplines")
    api.add_resource(AthleteUpcomingCompetitions, "/api/athlete-upcoming-competitions")
    api.add_resource(AthleteLastCompetitions, "/api/athlete-last-competitions")
    api.add_resource(AddQualificationNorm, "/api/add-qualification-norm")
