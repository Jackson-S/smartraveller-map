from sys import argv
from re import search
from io import BytesIO
import json
import pycountry
import pycurl

# Attempt to import cairosvg to output a png file
world_map = "resources/map.svg"
try:
    import cairosvg
    cairo = True
    # Use the first argument if supplied as a scale for the png output
    if len(argv) == 1:
        scale = 2
    else:
        scale = int(argv[1])
        # Set the world map to be a higher detail one if the scale is > 4x
        if scale > 4:
            world_map = "resources/map_hq.svg"
        # If 0 is supplied disable png output
        elif scale == 0:
            cairo = False
except ImportError:
    cairo = False

# for when smartraveller uses the wrong names or something goes wrong
country_fixes = {
    "Democratic Republic of the Congo": "CD", "Republic of Korea": "KR",
    "Netherlands Antilles": "AN", "Reunion": "RE", "The Bahamas": "BS",
    "Iran": "IR", "Israel, the Gaza Strip and the West Bank": "IL",
    "Kosovo": "XK", "Laos": "LA", "Macau": "MO", "Syria": "SY", "Russia": "RU",
    "The Gambia": "GM", "Vietnam": "VN", "The Republic of the Congo": "CG"
}

# The rgb vals of each warning (green, yellow, orange, red) smartraveller uses
colours = dict(normal=(152, 211, 155), caution=(254, 230, 134),
               warning=(249, 172, 95), danger=(229, 117, 116))

# Retrieve the master list from smartraveller.gov.au using curl
with BytesIO() as response:
    c = pycurl.Curl()
    c.setopt(c.URL, "http://smartraveller.gov.au/countries/pages/list.aspx")
    c.setopt(c.WRITEDATA, response)
    c.perform()
    c.close()
    utf8_response = response.getvalue().decode("UTF-8")

# Parse the JSON data supplied by the url
countries_json = search(r"CountryGrid.render\(.*\)", utf8_response)[0]
countries_json = json.loads(countries_json[60:countries_json.rfind(")")])

countries = list()

# For each country in scraped JSON get the necessary fields into a nice array
for index, item in enumerate(countries_json):
    advisory = json.loads(item["Smartraveller_x0020_Advice_x0020_Levels"])
    try:
        ccode = pycountry.countries.lookup(item["Title"]).alpha_2
    except LookupError:
        ccode = country_fixes[item["Title"]]
    advisory = advisory["items"]
    if len(advisory) > 0:
        for item in advisory:
            if "overall" in item['text']:
                advisory = item['level']
                break
    else:
        advisory = None
    countries.append((ccode, advisory))

# Create an array that will store all our override fill colours for the svg map
code = ["#AU{fill: rgb(0, 0, 0);}"]
for ccode, advisory in countries:
    if advisory != None:
        code.append("#{}{{fill:rgb({},{},{});}}".format(ccode, *colours[advisory]))

# Read in the entire map resource
with open(world_map) as map_file:
    world_map = map_file.read()

# Replace the python string with the code array we created, prepended with
# correct indentation to make it slightly neater
world_map = world_map.replace("<!-- PYTHON -->", "\n\t\t\t".join(code))

with open("output.svg", "w") as out_file:
    out_file.write(world_map)

# Checks if cairosvg is installed and if so outputs a png version
if cairo:
    cairosvg.svg2png(url="output.svg",
                     write_to="output.png",
                     parent_width=1024,
                     parent_height=660,
                     scale=scale)
