import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import re

LADV_RESULT_URL = "https://ladv.de/ergebnisse/{}/"
CLUB_NAME = "SV Werder Bremen"
MEETING_ID = 63362

# html classes for the respective fields
CLASSES = {
    "tables": "erg_runde",
    "event": "erg_headline_left",
    "club": "club",
    "row": "erg_row",
    "rank": "platz",
    "name": "erg_athlet",
    "result": "performance",
    "wind": "wind",
    "date": "erg_headline_right"
}


def main():
    meeting_info, athletes = find_results(MEETING_ID)
    print_out = show_results(athletes, meeting_info)
    with open("results.txt", "w") as f:
        f.write(print_out)
    print(print_out)


def get_meeting_info(soup):
    meeting_info = dict()
    meeting_info["title"] = soup.find("div", class_="title").text
    city_and_date = soup.find("div", class_="titleortdatum").text
    meeting_info["date"] = re.search("(?<=am).* ", city_and_date).group(0).replace("in", "").strip()
    meeting_info["city"] = re.search("(?<=in).*", city_and_date).group(0).strip()
    return meeting_info


def find_results(meeting_id):
    results = []
    url = LADV_RESULT_URL.format(meeting_id)
    response = requests.get(url)

    if response.status_code != 200:
        return None, None

    content = response.content
    # with open("content.html", "r") as f:
    #     content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all("div", class_=CLASSES["tables"])
    meeting_info = get_meeting_info(soup)
    for table in tables:
        heading = table.find("div", class_=CLASSES["event"])
        if heading is None:
            continue
        event = re.search(".*(?=\()", heading.text).group(0).strip()
        subtitle = re.search("(?<=\().*(?=\))", heading.text).group(0).strip()
        agegroup = heading.text.split("-")[-1].strip()
        date = table.find("div", class_=CLASSES["date"])

        for row in table.find_all("div", class_=CLASSES["row"]):
            club = row.find("div", class_=CLASSES["club"])

            if club and club.text != CLUB_NAME:
                continue

            name_div = row.find("div", class_=CLASSES["name"])
            if name_div is None:
                continue
            names = [c.strip() for c in name_div.text.split(",")]
            surname = names[-1]
            family_name = names[0]
            name = f"{surname} {family_name}"
            rank = row.find("div", class_=CLASSES["rank"])
            result = row.find("div", class_=CLASSES["result"])
            wind = row.find("div", class_=CLASSES["wind"])

            break_loop = False
            for div in (rank, result, wind, date):
                if div is None:
                    break_loop = True

            if break_loop:
                continue

            results.append(
                {
                    "name": name,
                    "surname": surname,
                    "familyname": family_name,
                    "event": event,
                    "agegroup": agegroup,
                    "subtitle": subtitle,
                    "result": result.text,
                    "rank": rank.text,
                    "date": date.text,
                    "wind": wind.text.strip()
                }
            )

    return meeting_info, results


def show_results(athletes, meeting_info):
    print_out = f"{meeting_info['title']} am {meeting_info['date']} in {meeting_info['city']}\n"
    print_out += "-------------------------------------------------------\n"
    for athlete in athletes:
        name = athlete
        print_out += name + "\n"
        for event in athletes[name]:
            if event["wind"].strip():
                result = f'{event["result"]} ({event["wind"]})'
            else:
                result = event["result"]

            print_out += f'{event["event"]} {event["agegroup"]} ({event["subtitle"]}): {event["rank"]} {result}\n'
        print_out += "-------------------------------------------------------\n"
    return print_out


def get_werder_results(year):
    load_dotenv()
    api_key = os.getenv('LADV-API-KEY')
    WERDER_NUMBER = 25
    LV = "BR"
    url = f"https://ladv.de/api/{api_key}/veaList?vereinnumber={WERDER_NUMBER}&limit=200&datayear={year}&lv={LV}"
    r = requests.get(url)
    events = r.json()
    return events


def get_werder_events():
    load_dotenv()
    api_key = os.getenv('LADV-API-KEY')
    WERDER_NUMBER = 25
    LV = "BR"
    url = f"https://ladv.de/api/{api_key}/meldList?vereinnumber={WERDER_NUMBER}&limit=200&lv={LV}"
    r = requests.get(url)
    events = r.json()
    return events


if __name__ == "__main__":
    # main()
    print(get_werder_events())
