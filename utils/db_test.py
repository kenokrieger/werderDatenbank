from datetime import datetime

from athletes.models.models import Athlete, Performance
from athletes import init_app, db

from athletes.scraping import ladv


def main():
    app = init_app()
    with app.app_context():
        keno = Athlete.query.get(236)
        keno.add_performances([{"datum": "18.06.2023", "ort": "Essen", "leistung": "14,53"}])
        existing_performance = Performance.query.filter_by(
            date="18.06.2023", city="Essen", athlete_id=236, value="14,53")
        print(existing_performance.first())
    return 0


if __name__ == "__main__":
    main()
