import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def get_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('searchconsole', 'v1', credentials=creds)
    return service


def fetch_indexed_pages(site_url):
    service = get_service()
    start_row = 0
    row_limit = 25000
    pages = []

    while True:
        request = {
            'startDate': '2023-01-01',
            'endDate': '2023-12-31',
            'dimensions': ['page'],
            'rowLimit': row_limit,
            'startRow': start_row,
        }
        response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        rows = response.get('rows', [])
        if not rows:
            break
        pages.extend([row['keys'][0] for row in rows])
        if len(rows) < row_limit:
            break
        start_row += row_limit
    return pages


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fetch indexed pages from Google Search Console.')
    parser.add_argument('site_url', help='The property URL to query (e.g. https://example.com)')
    args = parser.parse_args()

    urls = fetch_indexed_pages(args.site_url)
    for url in urls:
        print(url)
