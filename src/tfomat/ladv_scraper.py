"""Module for scraping meeting results from ladv."""
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

LADV_RESULT_URL = "https://ladv.de/ergebnisse/{}/"

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


def get_meeting_info(soup):
    """
    Get the metadata of a meeting such as the city and date it took place.

    Args:
        soup (bs4.BeautifulSoup): A HTML object containing the results of
            a meeting.

    Returns:
        dict: The title, date and city of the meeting.

    """
    meeting_info = dict()
    meeting_info["title"] = soup.find("div", class_="title").text
    city_and_date = soup.find("div", class_="titleortdatum").text
    meeting_info["date"] = re.search("(?<=am).* ", city_and_date).group(0).replace("in", "").strip()
    meeting_info["city"] = re.search("(?<=in).*", city_and_date).group(0).strip()
    return meeting_info


def find_results(meeting_id, club_name):
    """
    Find individual results of all members of `club_name`.

    Args:
        meeting_id (int): The id of the meeting at ladv.
        club_name (str): The name of the club that appears in the results.

    Returns:
        tuple: Meeting metadata and the individual's results.

    """
    soup = _get_from_ladv(meeting_id)
    if soup is None:
        return None, None
    meeting_info = get_meeting_info(soup)
    tables = soup.find_all("div", class_=CLASSES["tables"])

    results = []
    for table in tables:
        heading = table.find("div", class_=CLASSES["event"])
        if heading is None:
            continue
        event_data = _get_event_data(heading, table)
        if event_data is None:
            continue

        rows = table.find_all("div", class_=CLASSES["row"])
        _get_event_results(rows, event_data, club_name, results)
    return meeting_info, results


def _get_event_results(rows, event_data, club_name, results):
    """
    Get results from athletes that took part in an event and append it to
    a results list.

    Args:
        rows (list): A list of HTML entity containing event results of athletes.
        event_data (dict): Metadata of the event.
        club_name (str): The name of athlete's club.
        results (list): The list to append the results to.

    Returns:
        None.

    """
    for row in rows:
        club = row.find("div", class_=CLASSES["club"])
        if club and club.text != club_name:
            continue

        name_div = row.find("div", class_=CLASSES["name"])
        if name_div is None:
            continue

        result = _get_individual_result(name_div, row)
        if result is None:
            continue

        results.append(result.update(event_data))


def _get_from_ladv(meeting_id):
    """
    Get the meeting results from ladv.

    Args:
        meeting_id (int): The id of the meeting at ladv.

    Returns:
        bs4.BeautifulSoup or None: The HTML contents of the result page.

    """
    url = LADV_RESULT_URL.format(meeting_id)
    response = requests.get(url)
    if response.status_code != 200:
        return None
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')
    return soup


def _get_individual_result(name_div, row):
    """
    Get the one individual's result of an event.

    Args:
        name_div (bs4.tag): A HTML entity containing the name of an athlete.
        row (bs4.tag): A HTML entity containing the results of an athlete in
            an event.

    Returns:
        dict: The result of the individual.

    """
    rank = row.find("div", class_=CLASSES["rank"])
    result = row.find("div", class_=CLASSES["result"])
    wind = row.find("div", class_=CLASSES["wind"])

    if any(a is None for a in (rank, result, wind)):
        return None

    names = [c.strip() for c in name_div.text.split(",")]
    surname = names[-1]
    family_name = names[0]
    name = f"{surname} {family_name}"

    return {"name": name, "surname": surname, "familyname": family_name,
            "result": result, "wind": wind.text.strip(),
            "rank": rank.text.strip()}


def _get_event_data(heading, table):
    """
    Extract the event name, qualifying round, agegroup and date from the
    heading of a result.

    Args:
        heading (str): The heading of the result entry.
        table (bs4.tag): A HTML entity of meeting results.

    Returns:
         dict: The name, qualifying round, agegroup and date of the event.

    """
    date = table.find("div", class_=CLASSES["date"])
    if date is None:
        return None

    event = re.search(".*(?=\()", heading.text).group(0).strip()
    subtitle = re.search("(?<=\().*(?=\))", heading.text).group(0).strip()
    age_group = heading.text.split("-")[-1].strip()
    return {"agegroup": age_group, "date": date, "event": event,
            "subtitle": subtitle}


def get_club_results(club_nr, lv, api_key, year, cache_path, cache=None):
    """
    Get a list of events that athletes from a specific club competed in.

    Args:
        club_nr (int): The ladv id of the club.
        lv (str): The short name of the federal association.
        api_key (str): An API key for ladv.
        year (int): The year that the events took place.
        cache_path (str): The path to the cache directory.
        cache (list): Cached known events.

    Returns:
        list: Events that athletes competed in.

    """
    url = f"https://ladv.de/api/{api_key}/veaList?vereinnumber={club_nr}&limit=200&datayear={year}&lv={lv}"
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
    with open(os.path.join(cache_path, f"events_{year}.json"), "w") as f:
        json.dump(events, f)
    return events


def get_upcoming_events(api_key, club_nr, lv):
    url = f"https://ladv.de/api/{api_key}/meldList?vereinnumber={club_nr}&limit=200&lv={lv}"
    r = requests.get(url)
    events = r.json()
    return events


def get_upcoming_competitions(athlete_id, api_key):
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


def get_athlete_info(athlete_id, api_key, start_year, end_year=datetime.now().year):
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
