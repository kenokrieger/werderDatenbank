from datetime import datetime

from athletes.models.models import Athlete
from athletes import init_app, db

from athletes.scraping import ladv


def main():
    app = init_app()
    with app.app_context():
        athletes = Athlete.query.all()

        for athlete in athletes:
            if athlete.ladv_id is None:
                try:
                    athlete.ladv_id = ladv.get_ladv_id(athlete.name)
                    db.session.commit()
                except:
                    continue
            athlete_info = ladv.get_athlete_info(
                athlete.ladv_id, datetime.now().year, datetime.now().year
            )
            if athlete_info.get("vereinname") != "SV Werder Bremen":
                continue
            if athlete_info.get("birthyear") != athlete.year_of_birth:
                continue
            athlete.add_performances(athlete_info.get("leistungen", []))

    return 0


if __name__ == "__main__":
    main()
