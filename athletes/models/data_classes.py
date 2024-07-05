class Athlete:
    def __init__(self, name, birthyear, gender, id, athlete_number,
                 personal_bests=None, seasons_bests=None,
                 performances=None):
        self.name = name
        self.birthyear = birthyear
        self.gender = gender
        self.id = id
        self.athlete_number = athlete_number
        if personal_bests is None:
            self.personal_bests = dict()
        else:
            self.personal_bests = personal_bests
        if seasons_bests is None:
            self.seasons_bests = dict()
        else:
            self.seasons_bests = seasons_bests
        if performances is None:
            self.performances = list()
        else:
            self.performances = performances

    def add_personal_best(self, performance):
        self.personal_bests[performance["discipline"]] = performance

    def add_seasons_best(self, season, best):
        this_seasons_bests = self.seasons_bests.get(season)

        if this_seasons_bests is None:
            self.seasons_bests[season] = {best["discipline"]: best}
        else:
            this_seasons_bests[best["discipline"]] = best

    def add_performance(self, discipline):
        self.performances.append(discipline)

    def to_dict(self):
        return {
            "name": self.name,
            "birthyear": self.birthyear,
            "gender": self.gender,
            "id": self.id,
            "athlete_number": self.athlete_number,
            "personal_bests": self.personal_bests,
            "seasons_bests": self.seasons_bests,
            "performances": self.performances
        }


if __name__ == "__main__":
    Keno = Athlete("Keno Krieger", 2000, "m", 1, 361)
    Keno.add_seasons_best("2022 indoor",
                          {
                              "discipline": "Triple Jump",
                              "value": 14.91,
                              "city": "Leipzig",
                              "date": "2022-02-26",
                              "indoor": "True",
                              "wind": None,
                              "ascending": True
                          }
                          )

    print(Keno.seasons_bests)
