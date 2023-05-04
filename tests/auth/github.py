# tests/github.py

# log in to github
# which is used for auth with chipy (more on that later.  maybe)
# so that comes next

# curl --request GET --url "https://api.github.com/octocat" --header "Authorization: Bearer $gh_token" --header "X-GitHub-Api-Version: 2022-11-28"

import os

import requests

from bs4 import BeautifulSoup

# https://www.chipy.org/login/github/?next=
# url="https://www.chipy.org/login/github/"

gh_token = os.getenv('gh_token')
gh_url = "https://api.github.com/octocat"
headers = {"Authorization": f"Bearer {gh_token}", "X-GitHub-Api-Version": "2022-11-28"}
session = requests.session()
response = requests.get(
        gh_url,
        headers=headers)

print(f"{response.status_code}=")
print(response.text)


# http://www.chipy.org/api/meetings/?format=json
chipy_url = "http://www.chipy.org/api/meetings/?format=json"

session = requests.session()
response = requests.get(
        chipy_url,
        headers=headers)

print(f"{response.status_code}=")
print(response.text[:50])


