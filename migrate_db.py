from glob import glob

import json


from athletes.models.models import Athlete, Performance
from athletes import init_app, db

OLD_DB_PATH = "/home/keno/Projects/Athlete_Database/database/raw/"


def main():
    app = init_app()
    data = []
    for file in glob(OLD_DB_PATH + "*.json"):
        with open(file, "r") as f:
            data.append(json.load(f))
    with app.app_context():
        for entry in data:
            athlete_id = Athlete.query.filter_by(name=entry["name"]).first().id
            performances = entry["performances"]
            for p in performances:
                new_performance = Performance(
                    date=p["date"],
                    city=p["city"],
                    athlete_id=athlete_id,
                    discipline=p["discipline"],
                    value=p["value"],
                    unit=None,
                    wind=p["wind"],
                    placement=None,
                    championship=None,
                    indoor=True if p["indoor"] == "true" else False
                )
                db.session.add(new_performance)
        db.session.commit()
    return 0


if __name__ == "__main__":
    main()
