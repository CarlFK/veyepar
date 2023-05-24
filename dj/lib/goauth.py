# veyepar/dj/lib/goauth.py
# used by veyepar/dj/googauth/utils.py
# and veyepar/dj/lib/youtube_v3_uploader.py

"""
https://developers.google.com/identity/protocols/oauth2/web-server#creatingcred
    Go to the Credentials page....

clients_secrets.json contains: client id, client secret, and the authorized redirect uri(s).
You get these values by creating a new project in the Google APIs console
and registering for OAuth2.0 for *web* applications:
https://code.google.com/apis/console
"""

import argparse
import json
import os

from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
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

    # credentials  necessary fields need to refresh the access token.
    # refresh_token, token_uri, client_id, and client_secret.

    credd = {'token': credentials.token,
             'refresh_token': credentials.refresh_token,
             'token_uri': credentials.token_uri,
             'client_id': credentials.client_id,
             'client_secret': credentials.client_secret,
            }

    return credd

### end of auth flow ###

## Save and Load tokens from the servers filesystem
def put_cred(file_name, credd):
    ret = json.dump( credd, open(file_name, 'w'), indent=2 )
    return ret

def get_cred(file_name):
    ret = json.load( open(file_name) )
    return ret


# sammple/demo code:

def get_some_data(credd):
    # verify we can do something with the token

    credentials = google.oauth2.credentials.Credentials(**credd)

    service = googleapiclient.discovery.build("oauth2", "v2", credentials=credentials)
    request = service.userinfo().get()
    response = request.execute()

    if not response:
        d = {"message": "No data in response = request.execute()."}
    else:
        d = response

    return d


class My_Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        # send the path to the calling code
        self.server._saved_path = self.path

        # give the browser something to chew on
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        content = json.dumps({'path':self.path}, indent=2)
        self.end_headers()
        self.wfile.write(bytes(content, 'utf-8'))


def wait_for_callback():

    # run a little webserver,
    # wait for the callback
    # return the path of the URL

    print("wating for a connection...")
    httpd = HTTPServer(('localhost', 8000), My_Handler)
    httpd.handle_request()
    path = httpd._saved_path

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
            type = Path,
            default=os.path.expanduser('~/.secrets/client_secret.json'),
            dest="client_secret_file",
            help="Process API key (what needs access to upload.)"),

    parser.add_argument('--token-file', '-t',
            type = Path,
            default=os.path.expanduser('~/.secrets/oauth_token.json'),
            help="oAuth token file. (permission from the destination account owner)")

    parser.add_argument('--scope', '-s',
            nargs='+',
            dest="scopes",
            default=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.profile",
                'https://www.googleapis.com/auth/youtube.readonly',
                ],
            help="oAuth token file. (permission from the destination account owner)")

    parser.add_argument('--redirect-url', '-r',
            default='http://localhost:8000/googauth/redirect/',
            help="The Autorized URL google will redirect to once the user allow/denys access.")
    # more help:
    """
Users will be redirected to this path after they have authenticated with Google.
The path will be appended with the authorization code for access, and must have a protocol.
It can’t contain URL fragments, relative paths, or wildcards, and can’t be a public IP address.
    """

    parser.add_argument('--oauthlib-insecure-transport', '-i',
            default=True,
            help='set OAUTHLIB_INSECURE_TRANSPORT = 1 for runing on http://localhost:8000' )

    parser.add_argument('--debug',
            action="store_true",
            help='pprint the keys to stdout.' )

    parser.add_argument('--warnings',
            action="store_true",
            help='print warnings to stdout.' )

    args = parser.parse_args()

    return args


def main():

    args = get_args()

    if args.oauthlib_insecure_transport:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    if args.debug:
        client_secret = get_cred(args.client_secret_file)
        print( "client_secret:" )
        pprint( client_secret )
        print()

    if args.warnings:
        client_secret = get_cred(args.client_secret_file)
        if args.redirect_url not in client_secret['web']['redirect_uris']:
            print( "WARNING: args.redirect_url not in client_secret." )
            if args.debug:
                print( "client_secret['web']['redirect_uris']:" )
                pprint( client_secret['web']['redirect_uris'] )
                print()

    if args.token_file.exists():

        credd = get_cred(args.token_file)
        print(f"credd read from {args.token_file=}")

        if args.debug:
            print( "credd:" )
            pprint( credd )
            print()

    else:

        # oAuth2 step 1
        start_url = goog_start( args.client_secret_file, args.scopes, args.redirect_url )
        print( f"Browse to {start_url}" )

        # oAuth2 step 2
        path = wait_for_callback()
        credd = get_token( args.client_secret_file, args.scopes, args.redirect_url, path )

        # save it for the next run
        put_cred(args.token_file, credd)
        print(f"credd saved to {args.token_file=}")


    # bonus step to prove it worked:
    print("get_some_data(), maybe...")
    d = get_some_data(credd=credd)
    pprint(d)


if __name__ == '__main__':
    main()

