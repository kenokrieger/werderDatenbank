from glob import glob

from athletes.models.models import Athlete, Performance
from athletes import init_app, db


def main():
    app = init_app()
    events = []
    with app.app_context():
        performances = Performance.query.all()
        events = list(set([p.discipline for p in performances]))

    with open("events.txt", "w") as f:
        for e in events:
            f.write(e + "\n")
    print(events)

    return 0


if __name__ == "__main__":
    main()
