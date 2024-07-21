from athletes.models.models import Athlete, Performance
from athletes import init_app, db
import numpy as np


def identify_duplicates():
    app = init_app()

    with app.app_context():

        performances = Performance.query.all()
        print("#Performances: ", len(performances))
        performances.sort(key=lambda x: int(x.id))
        dates = [p.date for p in performances]
        cities = [p.city for p in performances]
        values = [p.value for p in performances]
        athlete_ids = [p.athlete_id for p in performances]
        ids = [p.id for p in performances]

        duplicated_ids = []
        for pidx, performance in enumerate(performances):
            if performance.id in duplicated_ids:
                continue
            performance_info = (
                performance.athlete_id, performance.date,
                performance.city, performance.value
            )
            existing_performance_infos = zip(
                athlete_ids[pidx + 1:], dates[pidx + 1:],
                cities[pidx + 1:], values[pidx + 1:],
                ids[pidx + 1:]
            )
            for existing_info in existing_performance_infos:
                if performance_info == existing_info[:-1]:
                    duplicated_ids.append(existing_info[-1])

        np.savetxt("duplicated_ids.txt", duplicated_ids)
    return 0


def clear_duplicates():
    duplicated_ids = np.loadtxt("duplicated_ids.txt").astype(int)
    print("# Duplicates: ", duplicated_ids.shape[0])

    app = init_app()

    with app.app_context():
        print("# Total Performances: ", len(Performance.query.all()))
        for performance in Performance.query.all():
            if performance.id in duplicated_ids:
                db.session.delete(performance)
        db.session.commit()


def clear_duplicated_names():
    app = init_app()

    with app.app_context():
        athletes = Athlete.query.all()

        for athlete in athletes:
            for a in athletes[athlete.id:]:
                if athlete.name == a.name:
                    db.session.delete(a)
        db.session.commit()
    return 0


if __name__ == "__main__":
    # identify_duplicates()
    clear_duplicates()
    # clear_duplicated_names()
