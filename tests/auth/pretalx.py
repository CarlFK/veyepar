
# get_email.py

# docs:
# https://docs.pretalx.org/api/fundamentals.html#authentication
# api token stored to env pretalx_token
# https://pretalx.northbaypython.org/nbpy-2023/me/

# I should see "email" in the keys.


import os
import requests

from pprint import pprint

# url="https://pretalx.northbaypython.org/api/events/nbpy-2023/speakers/"
# url="https://pretalx.com/api/events/pyohio-2024/talks/"
url="https://pretalx.com/api/events/pyohio-2024/speakers/"
api_token=os.getenv('pretalx_token')

headers = {'Authorization': f'Token {api_token}'}

response=requests.get( url, headers=headers )
pprint(response.json())

print(f"{response.json().keys()=}")



