import re
from datetime import datetime

DISCIPLINE_MAPPER = {
    "60 m Hürden": "60H",
    "80 m Hürden": "80H",
    "100 m Hürden": "100H",
    "110 m Hürden": "110H",
    "300 m Hürden": "300H",
    "400 m Hürden": "400H",
    "Hochsprung": "HOC",
    "4-Kampf": "4-K",
    "Speer": "SPE",
    "Ball": "BLL",
    "Dreisprung": "DRE",
    "9-Kampf": "9-K",
    "600 m": "600",
    "60 m": "60",
    "blm": "BLM",
    "4-M": "4-M",
    "Weitsprung": "WEI",
    "1KO": "1KO",
    "3KO": "3KO",
    "10 km Straße": "10S",
    "HALM": "HALM",
    "3 x 1000 m": "3X1",
    "75 m": "75",
    "5 km Straße": "5S",
    "MAR": "MAR",
    "30 m": "30",
    "7-M": "7-M",
    "3-M": "3-M",
    "400 m": "400",
    "HAL": "HAL",
    "Kugel": "KUG",
    "BLS": "BLS",
    "5KO": "5KO",
    "100 m": "100",
    "Diskus": "DIS",
    "2KO": "2KO",
    "BLB": "BLB",
    "50 m": "50",
    "4 x 75 m": "4X7",
    "200 m": "200",
    "9-M": "9-M",
    "10 km": "10K",
    "3-Kampf": "3-K",
    "4 x 100 m": "4X1",
    "BAL": "BAL",
    "3 x 800 m": "3X8",
    "Zonenweitsprung": "WEZ",
    "4 x 400 m": "4X4",
    "15 km Straße": "15S",
    "MEI": "MEI",
    "800 m": "800",
    "Siebenkampf": "7-K",
    "Stabhochsprung": "STA",
    "1500 m": "1K5",
    "Fünfkampf": "5-K",
    "Zehnkampf": "10-K",
    "SCH": "SCH",
    "4 x 5000 m": "4X5",
    "BLW": "BLW",
    "300 m": "300",
    "4 x 200 m": "4X2"
}


def map_discipline(disc):
    for discipline in DISCIPLINE_MAPPER:
        if discipline in disc:
            return DISCIPLINE_MAPPER[discipline]
    print("No mapping found")
    return disc


def map_to_number(value):
    expr = None
    cases = [
        "[0-9]*:[0-9][0-9],[0-9][0-9]",  # long distance
        "[0-9]*,[0-9][0-9]",  # sprint or technical event
        "[0-9].[0-9][0-9][0-9]"  # multi-event
    ]
    case_nr = -1
    for idx, case in enumerate(cases):
        expr = re.search(case, value)
        if expr is not None:
            expr = expr.group(0)
            case_nr = idx
            break

    if case_nr == 0:
        fields = expr.split(":")
        hours = int(fields[0])
        fields = fields[1].split(",")
        minutes = int(fields[0])
        seconds = int(fields[1])
        return 3600 * hours + 60 * minutes + seconds

    if case_nr == 1:
        return int(expr.replace(",", ""))

    if case_nr == 2:
        return int(expr.replace(".", ""))

    return -1


def get_season_start(date):
    if 3 < date.month < 11:
        # summer season
        return datetime(date.year, 3, 31)

    if date.month <= 3:
        # winter season that began last year
        return datetime(date.year - 1, 11, 1)

    # winter season this year
    return datetime(date.year, 11, 1)
