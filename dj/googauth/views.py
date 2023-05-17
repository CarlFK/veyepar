# veyepar/dj/googauth/views.py

import json
import os

from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse

from .utils import goog_start, goog_token, get_cred, put_cred, get_some_data

if settings.DEBUG:
    # for dev server runing on http://localhost:8000
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# CLIENT_SECRET:  the OAuth 2.0 for this application, namely client_id and client_secret.
CLIENT_SECRET_FILE = settings.GOOG_CLIENT_SECRET
TOKEN_FILE = settings.GOOG_TOKEN

SCOPES = settings.GOOG_SCOPES # ["https://www.googleapis.com/auth/youtube.force-ssl",]
REDIRECT_URL = settings.GOOG_REDIRECT_URL #  'http://127.0.0.1:8000/googauth/redirect/'


def goog_init(request):

    authorization_url = goog_start( CLIENT_SECRET_FILE, SCOPES, REDIRECT_URL )

    return redirect(authorization_url)


def goog_redirect(request):

    authorization_response = request.get_full_path()

    # state created in the flow in the callback will be verified
    state = request.GET['state']

    credd = goog_token( CLIENT_SECRET_FILE, SCOPES, REDIRECT_URL, authorization_response, state)

    # Save Creds
    # Saving to a file on the local file system.
    # TODO: use something like https://pypi.org/project/keyring/
    put_cred(credd, TOKEN_FILE)

    # verify they can do something

    data = get_some_data(credd=credd)

    # TODO: a nice thankyou page confirming all is well.
    # this blurt of json might be a little alarming.
    response = HttpResponse(content_type="application/json")
    json.dump(data, response, indent=2)
    return response


