import json
import os
from datetime import datetime

from flask import Blueprint, render_template, request, url_for, redirect, \
    send_from_directory, current_app

from athletes import db
from athletes.models.models import Athlete, Performance
from athletes.scraping.ladv import find_results, get_werder_results, \
    get_werder_events
from athletes.map import map_discipline
from athletes.latex import make_pdf

views = Blueprint('views', __name__)


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
    _update_database(city, results)
    page = render_template("results.html", title=title, results=results,
                           json_results=json.dumps(results))
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
    subtitle = "am {meeting_info['date']} in {meeting_info['city']}"
    _update_database(meeting_info['city'], results)

    agegroups = sorted(list(set(r["agegroup"] for r in results)))
    print_view = dict()
    for agegroup in agegroups:
        events = [r for r in results if r["agegroup"] == agegroup]
        disc = sorted(list(set(e["event"] for e in events)))
        print_view[agegroup] = {}
        for d in disc:
            matches = [e for e in events if e["event"] == d]
            matches.sort(key=_sort_by_result)
            is_sprint = any(digit in d for digit in "1 2 3 4 5 6 7 8 9".split())
            if not is_sprint:
                matches.reverse()
            matches = _move_nans_to_bottom(matches)
            print_view[agegroup][d] = matches
    make_pdf(print_view, title, subtitle, name=f"athletes/cache/{meeting_id}")
    return send_from_directory(directory=wdir,
                               path=f"./{meeting_id}.pdf")


def _update_database(city, results):
    for result in results:
        athlete = Athlete.query.filter_by(name=result["name"]).first()
        if athlete is None:
            result["pborsb"] = "?"
            continue

        result["pborsb"] = ""
        date = result["date"]
        value = result["result"]
        event = map_discipline(result["event"])
        rank = result["rank"].replace(".", "")
        try:
            placement = int(rank)
        except ValueError:
            placement = 0

        existing_entry = Performance.query.filter_by(date=date, value=value,
                                                     athlete_id=athlete.id).first()
        if existing_entry:
            if existing_entry.placement is None:
                existing_entry.placement = placement
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
                championship=None,
                indoor=not 2 < month < 11
            )
            db.session.add(new_performance)
            entry = new_performance

        result["pborsb"] = athlete.is_record(entry.discipline, entry.value,
                                             date)
    db.session.commit()
    return results


@views.route("/clear-results/<int:meeting_id>")
def clear_result_cache(meeting_id):
    cached_file_base = f"athletes/cache/{meeting_id}"
    for ext in (".html", ".pdf", ".tex"):
        cached_file = cached_file_base + ext
        if os.path.exists(cached_file):
            os.remove(cached_file)
    cached_file = "athletes/cache/{}.html".format(meeting_id)

    return redirect(url_for('views.get_results'))


@views.route("/get_result", methods=["GET", "POST"])
def get_results():
    if request.method == "POST":
        meeting_id = int(request.form.get("meeting_id"))
        return redirect(url_for('views.show_results', meeting_id=meeting_id))

    return render_template("results.html", title="", results=None)


@views.route("/events/<int:year>")
def events(year):
    cached_file = f"athletes/cache/events_{year}.html"
    if os.path.exists(cached_file):
        with open(cached_file, "r", encoding="utf-8") as f:
            return f.read()

    new_events = get_werder_results(year)
    page = render_template("events.html", events=new_events)
    if year < datetime.now().year:
        with open(cached_file, "w", encoding="utf-8") as f:
            f.write(page)
    return page


@views.route("/coming-events/")
def coming_events():
    new_events = get_werder_events()
    page = render_template("events.html", events=new_events)
    return page


@views.route("/profile/<id>")
def athlete_profile(id):
    return ""
