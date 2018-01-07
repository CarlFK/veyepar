# lca2018.py

from pprint import pprint

import requests

auth = {
            'login_page':'https://lca2017.linux.org.au/account/login/',
            'login_data':{
                'username':'carlfk',
                'password':'xxxx',
                'next':'/' }}

schedule_endpoint="http://lca2017.linux.org.au/schedule/conference.json"

session = requests.session()
session.get(auth['login_page'])
token = session.cookies['csrftoken']
print( token )

login_data = auth['login_data']
login_data['csrfmiddlewaretoken'] = token

ret = session.post(auth['login_page'],
        data=login_data,
        headers={'Referer':auth['login_page']})

print( "ret: {}".format(ret) )

response = session.get(schedule_endpoint)
# print( response.text[:200] )
j = response.json()
pprint( j['schedule'][0]['contact'] )
schedule =j['schedule']
for s in schedule:
    if s['contact']:
        pprint( s )
        print( "\ncontact: {}".format(s['contact']) )
        break



