from glob import glob

import json


from athletes.models.models import Athlete, Performance
from athletes import init_app, db

OLD_DB_PATH = "./athlete_data/"


def main():
    app = init_app()
    data = []
    for file in glob(OLD_DB_PATH + "*.json"):
        with open(file, "r") as f:
            data.append(json.load(f))
    with app.app_context():
        for entry in data:
            athlete = Athlete.query.filter_by(name=entry["name"]).first()
            if athlete is None:
                new_athlete = Athlete(
                    name=entry["name"],
                    year_of_birth=entry["birthyear"],
                    gender=entry["gender"],
                    ladv_athlete_number=entry["athlete_number"],
                    ladv_id=entry["id"]
                )
                db.session.add(new_athlete)
                athlete_id = new_athlete.id
            else:
                athlete_id = athlete.id
            existing_performances = Performance.query.filter_by(athlete_id=athlete_id)

            performances = entry["performances"]

            for p in performances:
                for existing_p in existing_performances:
                    if existing_p.date == p["date"] and existing_p.city == p["city"]:
                        print("Performance exists!")
                        continue

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
