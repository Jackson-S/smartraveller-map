from re import findall
from urllib.request import urlretrieve
from os import path
from PIL import Image
import pycountry
from tqdm import tqdm
import datetime

# The rgb vals of each warning (green, yellow, orange, red) smartraveller uses
colours = ((152, 211, 155), (254, 230, 134), (249, 172, 95), (229, 117, 116))

# for when smartraveller uses the wrong names or something goes wrong
country_fixes = {
    "Former Yugoslav Republic Of Macedonia": "MK","Russia":"RU","Laos":"LA",
    "Democratic Republic Of The Congo":"CD","Syria":"SY","Vietnam":"VN",
    "Israel Gaza Strip And West Bank": "IL","Macau":"MO","Kosovo":"XK","Iran":"IR",
    "Timor Leste":"TL","North Korea":"KP","South Korea":"KR","Ivory Coast":"CI"
}

# Gets the colour of a pixel
def get_color(r, g, b):
    for i in range(4):
        # Checks for the colour in a range (for dithering and compression)
        if colours[i][0] - 20 <= r <= colours[i][0] + 20 and\
           colours[i][1] - 20 <= g <= colours[i][1] + 20 and\
           colours[i][2] - 20 <= b <= colours[i][2] + 20:
           return i
    return None

# Check for the pre-parsed urls, if not there, create it
if not path.exists("resources/urls.txt"):
    with open("resources/countries.html") as in_file:
        # Regex to extract all countrie's pages from the file
        urls = findall(r'/Countries/.*?/Pages/.*?.aspx', in_file.read())
        with open("resources/urls.txt", "w") as out_file:
            out_file.write("\n".join(urls))

# Open the list of country page urls
with open("resources/urls.txt") as in_file:
    urls = in_file.read().split("\n")

map_locations = list()
ansi_name = list()
for index, url in enumerate(tqdm(urls)):
    # Get the country name from the URL by finding the final slash, and
    # removing 5 characters from the end (.aspx)
    country_name = url[url.rfind("/")+1:-5]
    out_location = "images/{}.gif".format(country_name)
    img_url = "http://smartraveller.gov.au/Maps/{}.gif".format(country_name)
    # Check if the image already exists, and if not retrieve it
    if not path.exists(out_location):
        try:
            urlretrieve(img_url, out_location)
        except:
            continue
    # Attempt to create an ANSI country name from the image title
    # This doesn't always work, so there's a fallback list of fixes
    # country_fixes that is used to supplement at a later stage
    # in case of failure
    ansi_name.append(country_name.replace("_", " ").title())
    map_locations.append(out_location)

# Create an array that will store all our override fill colours for the svg map
code = ["#AU{fill: rgb(0, 0, 0);}"]
for name, item in zip(ansi_name, tqdm(map_locations)):
    # Create a counter for green, yellow, orange, red to count the pixels
    # matching these colours in the image
    count = [0,0,0,0]
    img = Image.open(item)
    rgb_img = img.convert("RGB")
    x, y = img.size
    for i in range(y):
        for j in range(x):
            pixel = rgb_img.getpixel((j, i))
            # Gets the index relating to count for the pixel
            pix_index = get_color(*pixel)
            if pix_index != None:
                count[pix_index] += 1
    # Attempt to get the ANSI country code for the current country, which
    # is the css id name to later append into the SVG file.
    try:
        ccode = pycountry.countries.lookup(name).alpha_2
    except:
        ccode = country_fixes[name]
    code.append("#{}{{fill: rgb({}, {}, {});}}".format(
        ccode, *colours[count.index(max(count))])
    )

# Read in the entire map resource
with open("resources/map.svg") as map_file:
    world_map = map_file.read()

# Replace the python string with the code array we created, prepended with
# correct indentation to make it slightly neater
world_map = world_map.replace("<!-- PYTHON -->", "\n\t\t\t".join(sorted(code)))

# Get the current date to output as the new file name
name = datetime.datetime.now().strftime("%Y.%m.%d %X")
with open("{}.svg".format(name), "w") as out_file:
    out_file.write(world_map)
