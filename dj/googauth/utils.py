# veyepar/dj/googauth/utils.py

import argparse
import json
import os

from http.server import HTTPServer, BaseHTTPRequestHandler
from pprint import pprint
from urllib.parse import urlparse, parse_qs

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery


def goog_start( client_secret_file, scopes, redirect_uri ):

    # Construct a URL that will ask the user to give this app permission to scopes

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        client_secret_file,
        scopes=scopes)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = redirect_uri

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission.
        access_type='offline',
        )
        # Don't enable incremental authorization.
        # This will cause a "Warning: Scope Changed" error later.
        # If someday we need to manage more than one set of scopes
        # then we well come back here.
        # include_granted_scopes='true',

    return authorization_url


def goog_token( client_secret_file, scopes, redirect_uri, authorization_response, state):

    # Google redirects the local browser to a url on some server.
    # parse the URL and send the needed parameters here.
    # (not sure why we have to extract state, and then pass the URL which includes state=.)

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        client_secret_file,
        scopes=scopes,
        state=state)

    flow.redirect_uri = redirect_uri

    # Use the authorization server's response to derive? the OAuth 2.0 tokens.
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials

    credd = {'token': credentials.token,
             'refresh_token': credentials.refresh_token,
             'token_uri': credentials.token_uri,
            }

    return credd

### end of auth ###

# sammple/demo code:

def get_items(api_service_name, api_version, credd):
    # verify we can do something with the token
    # TODO: find something generic instead of video.

    credentials = google.oauth2.credentials.Credentials(**credd)
    service = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = service.videos().list(
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

    return d


PATH=None

class My_Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        # send this data to the calling code (so bad!)
        global PATH
        PATH=self.path

        # give the browser something to chew on
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        content = json.dumps({'path':self.path}, indent=2)
        self.end_headers()
        self.wfile.write(bytes(content, 'utf-8'))

        return self.path


def wait_for_callback():

    # run a little webserver,
    # wait for the callback
    # return the path part of the URL (using global.. ewww.)

    print("wating for a connection...")
    httpd = HTTPServer(('localhost', 8000), My_Handler)
    httpd.handle_request()
    path = PATH

    return path


def get_token( client_secret_file, scopes, redirect_uri, path ):

    authorization_response = path

    parsed = urlparse(path)
    qs = parse_qs(parsed.query)
    state = qs['state'][0]

    credd = goog_token( client_secret_file, scopes, redirect_uri, authorization_response, state)

    return credd


def get_args():

    parser = argparse.ArgumentParser(
            description="Get a token from google.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )

    parser.add_argument('-client-secret-file', '-c',
            default=os.path.expanduser('~/.secrets/client_secret.json'),
            dest="client_secret_file",
            help="Process API key (what needs access to upload.)"),

    parser.add_argument('--token-file', '-t',
            default=os.path.expanduser('~/.secrets/oauth_token.json'),
            help="oAuth token file. (permission from the destination account owner)")

    parser.add_argument('--scope', '-s',
            nargs='+',
            dest="scopes",
            default='https://www.googleapis.com/auth/youtube.readonly',
            help="oAuth token file. (permission from the destination account owner)")

    parser.add_argument('--redirect-url', '-r',
            default='http://localhost:8080/redirect/',
            help="The Autorized URL google will redirect to once the user allow/denys access.")
    # more help:
    """
Users will be redirected to this path after they have authenticated with Google.
The path will be appended with the authorization code for access, and must have a protocol.
It can’t contain URL fragments, relative paths, or wildcards, and can’t be a public IP address.
    """

    parser.add_argument('--oauthlib-insecure-transport', '-i',
            default=True,
            help='set OAUTHLIB_INSECURE_TRANSPORT = 1 for runing on http://localhost:8080' )

    args = parser.parse_args()

    return args


def main():

    args = get_args()

    if args.oauthlib_insecure_transport:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # oAuth2 step 1
    start_url = goog_start( args.client_secret_file, args.scopes, args.redirect_url )
    print( f"Browse to {start_url}" )

    # oAuth2 step 2
    path = wait_for_callback()
    credd = get_token( args.client_secret_file, args.scopes, args.redirect_url, path )
    pprint(credd)

    # bonus step to prove it worked:
    d = get_items(api_service_name="youtube", api_version="v3", credd=credd)
    pprint(d)


if __name__ == '__main__':
    main()

