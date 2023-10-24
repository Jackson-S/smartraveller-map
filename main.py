import os
import re
import json
import argparse
import urllib.request
import requests
from jsonpath_ng.ext import parse
from dataclasses import dataclass
from typing import List

from countries import country_codes

@dataclass
class Country:
    country_id: str
    country_name: str
    overall_advice_level: str

def fetch_api():
    request = requests.get("https://www.smartraveller.gov.au/api/publishedpages")
    locations = parse("$[?(@.pageType=='location')].id").find(request.json())
    response = []
    for location in locations:
        id = location.value
        location_request = requests.get(f"https://www.smartraveller.gov.au/api/locationpages/{id}")
        title_html: str = location_request.json()[0]["title"]
        title = re.findall(">.*<", title_html)[0][1:-1]
        print(title)
        advice_html: str = location_request.json()[0]["overallAdviceLevel"]
        try:
            advice = re.findall(">.*<", advice_html)[0][1:-1]
        except IndexError:
            print(f"No advice found for {title}")
            advice = None
        response.append(Country(id, title, advice))
    return response


def convert_to_png(scale):
    try:
        import cairosvg
    except ImportError as e:
        print(e)
        print("Cairosvg is required to output a PNG file.")
        return

    cairosvg.svg2png(url="output.svg",
                     write_to="output.png",
                     parent_width=1024,
                     parent_height=660,
                     scale=scale)


def get_map_file(arguments):
    if arguments.high_quality:
        map_file = "hq.svg"
    else:
        map_file = "sq.svg"
    return os.path.join("resources", map_file)


def main(arguments):
    # The rgb vals of each warning (green, yellow, orange, red) smartraveller uses
    colours = { 
        "Exercise normal safety precautions": (152, 211, 155),
        "Reconsider your need to travel": (254, 230, 134),
        "Exercise a high degree of caution": (249, 172, 95),
        "Do not travel": (229, 117, 116),
    }

    # Find the correct JSON data in the page downloaded and read.
    countries_api: List[Country] = fetch_api()

    # Initialize a list of all countries on smartraveller
    countries = []

    # For each country in the data get the necessary fields into an array
    for item in countries_api:
        # Looks up the correct country code
        try:
            country_code = country_codes[item.country_id]
        except KeyError:
            print(f"Country '{item.country_name}' with id '{item.country_id}' not found.")
            continue

        countries.append((country_code, item.overall_advice_level))

    # Read in the entire map resource (Done early to determine map code style)
    with open(get_map_file(arguments)) as map_file:
        world_map = map_file.read()

    # Create an array that will store all override fill colours for the svg map
    code = list()

    # Replace the python string with the code array we created, prepended with
    # correct indentation to make it slightly neater
    for country_code, advisory in countries:
        if advisory != None:
            color = "rgb({},{},{})".format(*colours[advisory])
            code.append("#{} {{fill: {};}}".format(country_code, color))

    world_map = world_map.replace("<!-- PYTHON Style1 -->", "\n".join(code))

    # Write the output
    with open("output.svg", "w") as out_file:
        out_file.write(world_map)

    # If conversion to png is required
    if arguments.image:
        convert_to_png(arguments.scale)

def parse_arguments():
    args = argparse.ArgumentParser()

    args.add_argument("-q", "--high-quality",
                      action="store_true",
                      default=False,
                      help="Use a high quality map file.")

    args.add_argument("-i", "--image",
                      action="store_true",
                      default=False,
                      help="Render a png version of the output.")

    args.add_argument("-s", "--scale",
                      action="store",
                      type=int,
                      default=1,
                      help="Select the scale of the PNG output.")

    arguments = args.parse_args()
    return arguments



if __name__ == "__main__":
    main(parse_arguments())
