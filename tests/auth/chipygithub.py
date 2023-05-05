# tests/chipygithub.py

# log in to chipy using github

# set your github user/pw in env vars: gh_user, gh_password

import json
import os

from pprint import pprint
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

session = requests.session()

# chipy website login:
url = "http://www.chipy.org/login/github"
response = session.get(url)
print(f"{url=} {response.status_code=}")

gh_url = response.url
print(f"{gh_url=}")

# find the login form
# <form data-turbo="false" action="/session" accept-charset="UTF-8" method="post">
soup = BeautifulSoup(response.text, features="lxml")
login_form = soup.find('form', dict(action="/session"))

# make a dictionary of all the form inputs (including csrf and other hidden things)
form_data = {}
for i in login_form.find_all('input'):
    form_data[i.get('name')] = i.get('value')
# pprint(form_data)

# fill in the user/passowrd fields
form_data['login'] = os.getenv('gh_user')
form_data['password'] = os.getenv('gh_password')
# pprint(form_data)

# assemble the url to post to:
# it will be https://github.com/session

gh = urlparse(gh_url)
gh_path = login_form.get('action')

url = f"{gh.scheme}://{gh.netloc}/{gh_path}"
print(f"{url=}")

response = session.post(url, data=form_data)
print(f"{url=} {response.status_code=}")

# write out the page for viewing with a browser
open('result.html','w').write(response.text)

soup = BeautifulSoup(response.text, features="lxml")
rsvp_form = soup.find('form', {"id":"rsvp-form"})

f_name = soup.find('input', {"id":"id_first_name"}).get('value')
l_name = soup.find('input', {"id":"id_last_name"}).get('value')
email = soup.find('input', {"id":"id_email"}).get('value')

print(f"{f_name=} {l_name=} {email=}")

url="http://www.chipy.org/api/meetings/?format=json"
response = session.get(url)
print(f"{url=} {response.status_code=}")

print(response.text[:200])
open('chipy.json','w').write(response.text)
meetings = json.loads(response.text)

meeting_id=223
meeting = [s for s in meetings if s['id']==meeting_id][0]
# pprint(meeting)
pprint(meeting["topics"])

import code; code.interact(local=locals())


