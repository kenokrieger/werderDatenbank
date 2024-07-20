# Copyright (C) 2024  Keno Krieger <kriegerk@uni-bremen.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import json
import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

LADV_RESULT_URL = "https://ladv.de/ergebnisse/{}/"
CLUB_NAME = "SV Werder Bremen"
CLUB_NUMBER = 25
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
                    "rank": rank.text.strip(),
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


def get_werder_results(year, cache_path, cache=None):
    load_dotenv()
    api_key = os.getenv('LADV-API-KEY')
    WERDER_NUMBER = 25
    LV = "BR"
    url = f"https://ladv.de/api/{api_key}/veaList?vereinnumber={WERDER_NUMBER}&limit=200&datayear={year}&lv={LV}"
    r = requests.get(url)
    events = r.json()

    new_events = []
    if cache is not None:
        event_urls = [c["url"] for c in cache]
    else:
        event_urls = []

    for event in events:
        if event["url"] in event_urls:
            continue
        r = requests.get(event["url"])
        soup = BeautifulSoup(r.content, 'html.parser')
        link = soup.find("a", class_="ergxml")
        if link is None:
            pass
        else:
            result_id = re.search("(?<=/ergebnisse/)[0-9]*", link.attrs["href"]).group(0)
            event["id"] = result_id
        new_events.append(event)

    if cache:
        events = cache + new_events
    with open(os.path.join(cache_path, f"events_{year}.json", "w")) as f:
        json.dump(events, f)
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


def get_upcoming_competitions(athlete_id):
    load_dotenv()
    api_key = os.getenv('LADV-API-KEY')
    this_year = requests.get(f"https://ladv.de/api/{api_key}/athletDetail?id={athlete_id}&datayear={datetime.today().year}&meld=true")
    next_year = requests.get(f"https://ladv.de/api/{api_key}/athletDetail?id={athlete_id}&datayear={datetime.today().year + 1}&meld=true")
    if this_year.status_code != 200 or next_year.status_code != 200:
        return {"error": "ladv returned an error"}

    listings = this_year.json()[0].get("meldungen", [])
    if next_year.json():
        listings += next_year.json()[0].get("meldungen", [])
    listings.sort(key=lambda x: x["datum"])
    return [l for l in listings if datetime.strptime(l["datumText"], "%d.%m.%Y") >= datetime.today()]


def get_ladv_id(athlete_name):
    load_dotenv()
    api_key = os.getenv("LADV-API-KEY")
    r = requests.get(f"https://ladv.de/api/{api_key}/athletQuery?query={athlete_name}")
    return r.json()[0]["id"]


def get_athlete_info(athlete_id, start_year, end_year=datetime.now().year):
    load_dotenv()
    api_key = os.getenv("LADV-API-KEY")

    response = {}
    for year in range(start_year, end_year + 1):
        r = requests.get(
            f"https://ladv.de/api/{api_key}/athletDetail?id={athlete_id}&datayear={year}&leistung=true"
        )
        content = r.json()
        if not content:
            continue
        previous_performances = response.get("leistungen", [])
        new_performances = content[0]["leistungen"]
        response.update(content[0])
        response["leistungen"] = previous_performances
        if content[0].get("vereinnumber") == CLUB_NUMBER:
            response["leistungen"] += new_performances
    return response


if __name__ == "__main__":
    # main()
    # print(get_werder_results(2022))
    print(get_upcoming_competitions(450047))
