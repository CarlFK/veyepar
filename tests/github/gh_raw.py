
# get_github.py

import os
import requests

from pprint import pprint

url="https://raw.githubusercontent.com/pyohio/pyohio-static-website/main/2024/src/content/json/talks.json"
response=requests.get( url )
o = response.json()
pprint(o)

print(f"{o[0].keys()=}")



