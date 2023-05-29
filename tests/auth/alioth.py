# uc.py

# log in to https://alioth.debian.org
# which is used for auth with https://summit.debconf.org/debconf14/
# so that comes next

"""
<form action="https://alioth.debian.org/plugins/authbuiltin/post-login.php" method="post">

<input name="form_key" value="1e16865f17377a061e216670ab7b66ea" type="hidden">

<input name="form_loginname" value="" type="text">
<input name="form_pw" type="password">

<input name="login" value="Login" type="submit">
<input name="return_to" value="/" type="hidden">
"""

import requests

from BeautifulSoup import BeautifulSoup

try:
    # read credentials from a file
    from pw import addeps
except ImportError:
    # you can fill in your credentials here
    # but better to put in pw.py so that they don't leak
    addeps = {
        'debconf14': {
             'login_page':'https://alioth.debian.org/account/login.php',
             'login_data':{
                'form_loginname':'someone-guest',
                'form_pw':'abc' ,
                'login':'Login' ,
                'return_to':'/' }},
        }

auth=addeps['debconf14']
print auth

session = requests.session()
response = requests.get(auth['login_page'])

# grab the crsf token (this is php stuff, not django, so not in headers)
soup = BeautifulSoup(response.text)
token = soup.find('input', dict(name='form_key'))['value']
print token

login_data = auth['login_data']
login_data['form_key'] = token

ret = session.post(auth['login_page'],
        data=login_data,
        headers={'Referer':auth['login_page']})

print "ret:", ret

response = session.get('https://alioth.debian.org/')
print response

html = response.text
open('result.html','w').write(html)
print "file:///home/carl/src/veyepar/tests/auth/result.html"

# print html

print
print "found Alioth:", "Alioth" in html
print "found Log Out:", "Log Out" in html

# j = response.json()
# print j
# print j['schedule'][0]['contact']
# print j[0]['contact']


