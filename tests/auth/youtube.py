# Sample Python code for youtube.videos.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


def get_creds(credentials_file, client_secrets_file):

    # If modifying these scopes, delete credentials_file.
    YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
    # scopes = [YOUTUBE_READ_WRITE_SCOPE,]
    # scopes = ['https://www.googleapis.com/auth/youtube.upload']
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

    # The credentials_file stores the user's access and refresh tokens.
    if os.path.exists(credentials_file):
        credentials = google.oauth2.credentials.Credentials.from_authorized_user_file(
                credentials_file, scopes)
    else:
        credentials = None

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:

            # Get credentials and create an API client
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
            credentials = flow.run_local_server(port=0)

    return credentials


def save_creds(credentials, credentials_file):
        # Save the credentials for the next run
        with open(credentials_file, 'w') as f:
            f.write(credentials.to_json())


def use_creds(credentials):

    try:

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

        print(response)

    except googleapiclient.errors.HttpError as err:
        print(err)


def main():

    client_secrets_file = 'client_secrets.json'
    credentials_file = 'credentials.json'

    credentials = get_creds(credentials_file, client_secrets_file)
    if credentials:
        save_creds(credentials, credentials_file)
        use_creds(credentials)


if __name__ == '__main__':
    main()


