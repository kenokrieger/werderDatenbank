import os

from datetime import datetime
import json

from flask import Blueprint, render_template, request, url_for, redirect

from athletes import db
from athletes.models.models import Athlete, Performance
from athletes.scraping.ladv import find_results, get_werder_events
from athletes.map import map_discipline

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

    meeting_info, athletes = find_results(meeting_id)

    if meeting_info is None:
        return "No results available"
    title = f"{meeting_info['title']} am {meeting_info['date']} in {meeting_info['city']}\n"

    city = meeting_info["city"]
    for name in athletes:
        athlete = Athlete.query.filter_by(name=name).first()
        if athlete is None:
            print(name)
            continue
        for performance in athletes[name]:
            performance["pborsb"] = ""
            date = performance["date"]
            value = performance["result"]
            event = map_discipline(performance["event"])
            rank = performance["rank"].replace(".", "")
            try:
                placement = int(rank)
            except ValueError:
                placement = 0

            existing_entry = Performance.query.filter_by(date=date, value=value).first()
            if existing_entry:
                if existing_entry.placement is None:
                    existing_entry.placement = placement
                entry = existing_entry
            else:
                month = int(date.split(".")[1])
                wind = performance["wind"].replace(",", ".")

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
                    indoor=2 < month < 11
                )
                db.session.add(new_performance)
                entry = new_performance

            if athlete.is_personal_best(entry.discipline, entry.value, date):
                performance["pborsb"] = "PB"
            elif athlete.is_seasons_best(entry.discipline, entry.value, date):
                performance["pborsb"] = "SB"

    db.session.commit()
    page = render_template("results.html", title=title, athletes=athletes)
    with open(cached_file, "w", encoding="utf-8") as f:
        f.write(page)
    return page


@views.route("/get_result", methods=["GET", "POST"])
def get_results():
    if request.method == "POST":
        meeting_id = request.form.get("meeting_id")
        return redirect(url_for('views.results', meeting_id=meeting_id))

    return render_template("results.html", title="", athletes=None)


@views.route("/events/<int:year>")
def events(year):
    cached_file = f"athletes/cache/events_{year}.html"
    if os.path.exists(cached_file):
        with open(cached_file, "r", encoding="utf-8") as f:
            return f.read()

    new_events = get_werder_events(year)
    page = render_template("events.html", events=new_events)
    with open(cached_file, "w", encoding="utf-8") as f:
        f.write(page)
    return page
