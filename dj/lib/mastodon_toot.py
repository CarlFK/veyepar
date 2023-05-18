#!/usr/bin/python

# mastodon lib, cli and tests.

import argparse
import json
import os

from pathlib import Path
from pprint import pprint

from mastodon import Mastodon


def toot_toot(client_secret, access_token, api_base_url, message):

    print('tooting:', message)
    print('api_base_url:', api_base_url)
    print('access_token:', access_token)
    m = Mastodon(client_secret=client_secret, access_token=access_token, api_base_url=api_base_url)
    # m = Mastodon(access_token = 'pytooter_usercred.secret')

    status = m.status_post(message)
    pprint(status.id)

    return m


def create_client_creds(
        client_name,
        api_base_url,
        ):
    # Register this app with the sending server

    client_id, client_secret = Mastodon.create_app(
                                    client_name = client_name,
                                    api_base_url = api_base_url,
                                )

    ret = {
            'client_name': client_name,
            'api_base_url': api_base_url,
            'client_id': client_id,
            'client_secret': client_secret,
            }

    return ret

def create_access_token(
        client_name,
        api_base_url,
        client_id,
        client_secret,
        username,
        password,
        ):

    # Get the access token for a user.

    mastodon = Mastodon(
            client_id = client_id,
            client_secret = client_secret,
            api_base_url = api_base_url,
            )

    print(f"u: {username} p: {password}")
    access_token = mastodon.log_in(
            username,
            password,
            )

    return access_token

"""
# Then, log in. This can be done every time your application starts (e.g. when writing a
# simple bot), or you can use the persisted information:
mastodon = Mastodon(client_id = 'pytooter_clientcred.secret',)

mastodon.log_in(
    'my_login_email@example.com',
    'incrediblygoodpassword',
    to_file = 'pytooter_usercred.secret'
)
"""

def store_client_creds(client_creds, file_name):

    ret = json.dump( client_creds, open(file_name, 'w') )
    return ret

def store_access_token(access_token, file_name):

    ret = json.dump( access_token, open(file_name, 'w') )
    return ret

def load_client_creds(file_name):

    ret = json.load( open(file_name) )
    return ret

def load_access_token(file_name):

    ret = json.load( open(file_name) )
    return ret


def test_args(args):
    # test using the cli args

    # client creds
    if not args.client_creds_file.exists():
        client_creds = create_client_creds(
                client_name = args.client_name,
                api_base_url = args.api_base_url,
                )
        store_client_creds(client_creds, args.client_creds_file)
    else:
        client_creds = load_client_creds(args.client_creds_file)

    # auth token
    if not args.access_token_file.exists():
        access_creds = create_access_token(
            client_name = client_creds['client_name'],
            api_base_url = client_creds['api_base_url'],
            client_id = client_creds['client_id'],
            client_secret = client_creds['client_secret'],
            username = args.username,
            password = args.password,
            )

        store_access_token(access_creds, args.access_token_file)
    else:
        access_creds = load_access_token(args.access_token_file)

    ret = toot_toot(
            client_secret=client_creds['client_secret'],
            access_token = access_creds['access_token'],
            api_base_url = client_creds['api_base_url'],
            message = args.message)


def test_1():
    """
    works

    tooting: test_1
    api_base_url: https://yiff.life
    access_token: H6VfHUZiyAeX6YTRyzOGem6qq2fO9EktndFSE7ChqnE
    110244808830935725
    """
    ret = toot_toot(
            client_secret='T3g-D_JlN0VNSZj3bHrl2nAfHsGPirAFjuuP0RX3tnU',
            access_token='H6VfHUZiyAeX6YTRyzOGem6qq2fO9EktndFSE7ChqnE',
            api_base_url="https://yiff.life",
            message="test_1")

    return ret

def test_2(args):
    """
    """

    client_creds = load_client_creds(args.client_creds_file)

    access_token = load_access_token(args.access_token_file)


    ret = toot_toot(
            client_secret='T3g-D_JlN0VNSZj3bHrl2nAfHsGPirAFjuuP0RX3tnU',
            access_token='H6VfHUZiyAeX6YTRyzOGem6qq2fO9EktndFSE7ChqnE',
            api_base_url="https://yiff.life",
            message="test_2")

    return ret




def make_parser():

    cred_dir = Path(os.path.expanduser('~/.creds/mastodon'))

    parser = argparse.ArgumentParser(
            description="Toot a toot.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )

    parser.add_argument('--message', '-m',
            default = f"Test toot from {parser.prog} using #mastodon.py.",
            help="Test toot.")

    parser.add_argument('--api_base_url', '-b',
            default = 'https://mastodon.social',
            help="URL of the Mastodon instance sending the toots.")


    parser.add_argument('--client_name', '-n',
            default = parser.prog,
            help="The name of the thing sending the toots.")

    parser.add_argument('--username', '-u',
            default=None,
            help="Username of sending account.")

    parser.add_argument('--password', '-p',
            default=None,
            help="password of sending account.")


    parser.add_argument('--credintials-file', '-c',
            type = Path,
            default = cred_dir / 'client_creds.json',
            dest="client_creds_file",
            help="Process API key (what needs access to toot.)")

    parser.add_argument('--token-file', '-t',
            type = Path,
            default = cred_dir / 'access_token.json',
            dest="access_token_file",
            help="Access token file. (permission from the account owner)")

    parser.add_argument('--debug', '-d', default=False,
            action='store_true',
            help='Drop to prompt after toot.')


    return parser

def test( args ):
    return ret


def main():

    parser = make_parser()
    args = parser.parse_args()

    test_1()
    # ret = test_args(args)

if __name__ == '__main__':
   main()


