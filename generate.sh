#!/usr/bin/env bash

python3 -m venv smartraveller-map
source smartraveller-map/bin/activate

pip3 install -r requirements.txt
python3 main.py

mv output.svg "collection/$(date -u --rfc-3339 seconds).svg"

tar -c responses | xz -z9 > "collection/$(date -u --rfc-3339 seconds).tar.xz"
deactivate
rm -rf smartraveller-map
rm -rf responses
