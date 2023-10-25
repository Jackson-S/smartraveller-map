import re
import os
import requests
from jsonpath_ng.ext import parse
import json
from dataclasses import dataclass
from typing import List, Dict

from countries import country_codes

@dataclass
class Country:
    country_id: str
    country_code: str
    country_name: str
    overall_advice_level: int

smartraveller_caution_levels: Dict[str, int] = {
    "Exercise normal safety precautions": 1,
    "Reconsider your need to travel": 2,
    "Exercise a high degree of caution": 3,
    "Do not travel": 4,
}

css_template = """
    :root {
        --level-1: #008655;
        --level-2: #fed42b;
        --level-3: #f7941e;
        --level-4: #d24242;
    }
"""


def save_response(title: str, response: requests.Response):
    if not os.path.exists("responses"):
        os.mkdir("responses")
    with open(f"responses/{title}.json", "w") as out_file:
        json.dump(response.json(), out_file)


def fetch_smartraveller_data():
    request = requests.get("https://www.smartraveller.gov.au/api/publishedpages")
    save_response("publishedPages", request)
    locations = parse("$[?(@.pageType=='location')].id").find(request.json())
    response = []
    for location in locations:
        id = location.value
        location_request = requests.get(f"https://www.smartraveller.gov.au/api/locationpages/{id}")
        save_response(id, location_request)
        try:
            title_html: str = location_request.json()[0]["title"]
            title = re.findall(">.*<", title_html)[0][1:-1]
            print(title, end=" ")
            advice_html: str = location_request.json()[0]["overallAdviceLevel"]
            try:
                advice = re.findall(">.*<", advice_html)[0][1:-1]
                print(advice, end=" ")
            except IndexError:
                print(f"No advice found for {title}")
                advice = None
            try:
                country_code = country_codes[id]
                print(country_code)
            except KeyError:
                continue
            response.append(Country(id, country_code, title, smartraveller_caution_levels[advice]))
        except Exception:
            continue
    return response


def main():
    countries: List[Country] = fetch_smartraveller_data()

    # Read in the entire map resource (Done early to determine map code style)
    with open("resources/map.svg") as map_file:
        world_map = map_file.read()

    countries.sort(key=lambda x: x.country_code)
    # Create an array that will store all override fill colours for the svg map
    colours = "\n".join([f".{c.country_code.lower()} {{ fill: var(--level-{c.overall_advice_level}); }}" for c in countries])
    css = f"{css_template}\n{colours}"
    world_map = world_map.replace("/* PYTHON Style1 */", css)

    # Write the output
    with open("output.svg", "w") as out_file:
        out_file.write(world_map)


if __name__ == "__main__":
    main()
