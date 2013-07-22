# uc.py

# use crsf token when logging in and get data

import requests

try:
    # read credentials from a file
    from pw import addeps 
except ImportError:
    # you can fill in your credentials here
    # but better to put in pw.py so that they don't leak
    addeps = { 
        'pyconca2013': { 
            'login_page':'https://2013.pycon.ca/en/account/login/',
            'user':'test@example.com', 'password':'abc' },
        }

auth=addeps['pyconca2013']
print auth

session = requests.session()
session.get(auth['login_page'])
token = session.cookies['csrftoken']
print token

login_data = {
        'login-email':auth['user'], 
        'login-password':auth['password'], 
        'csrfmiddlewaretoken':token,
        'next':'/'}

ret = session.post(auth['login_page'],
        data=login_data,
        headers={'Referer':auth['login_page']})

print "ret:", ret

response = session.get('https://2013.pycon.ca/en/schedule/conference.json')
# print response.text
j = response.json()
print j['schedule'][0]['contact']


