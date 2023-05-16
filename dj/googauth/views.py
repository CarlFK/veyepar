# veyepar/dj/googauth/views.py

import json
import os

from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse

from .utils import goog_start, goog_token, get_items, get_cred, put_cred

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

    # Save Creds and bail
    put_cred(credd, TOKEN_FILE)

    # or maybe verify they can do something
    # or maybe a thank you page.
    # don't know or care right now, getting/saving the key is the important part.

    items = get_items(api_service_name="youtube", api_version="v3", credd=credd)
    d = {
            "authorization_response": authorization_response,
            "credd": credd,
            "items": items,
            }

    response = HttpResponse(content_type="application/json")
    json.dump(d, response, indent=2)
    return response


