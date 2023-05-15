# veyepar/dj/googauth/views.py

import json
import os

from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

from rest_framework.decorators import api_view
from rest_framework.response import Response

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = settings.GOOG_CLIENT_SECRET

YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
SCOPES = [YOUTUBE_READ_WRITE_SCOPE,]

REDIRECT_URL = 'http://127.0.0.1:8000/googauth/redirect/'

def goog_start(request):

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = REDIRECT_URL

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        # include_granted_scopes='true',
        )

    return redirect(authorization_url)


def goog_redirect(request):

    # state created in the flow in the callback so that it can
    # verified in the authorization server response.
    state = request.GET['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state)

    flow.redirect_uri = REDIRECT_URL

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.get_full_path()
    flow.fetch_token(authorization_response=authorization_response)

    # Save credentials back to session in case access token was refreshed.
    credentials = flow.credentials

    credd = {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

    # Save Creds and bail
    # or maybe verify they can do something

    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = youtube.videos().list(
            part="id",
            chart="mostPopular",
            prettyPrint=True
        )
    response = request.execute()

    if not response['items']:
        print('No data found.')
        d = {"message": "No data found or user credentials invalid."}
    else:
        d = {"items": response['items']}

    response = HttpResponse(content_type="application/json")
    json.dump([d, credd], response, indent=2)
    return response


