from flask import Blueprint, render_template
from athletes.models.models import Athlete, Performance

views = Blueprint('views', __name__)


@views.route('/athletes')
def athlete_overview():
    athletes = Athlete.query.all()
    return render_template('athletes.html', athletes=athletes)


@views.route('/performances')
def performance_overview():
    performances = Performance.query.all()
    return render_template('performances.html', performances=performances)


@views.route("/keno")
def keno():
    keno = Athlete.query.get(236)
    pb = keno.get_personal_best("DRE")
    return render_template("keno.html", pb=pb)