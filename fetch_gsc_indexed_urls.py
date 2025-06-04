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


def fetch_indexed_pages(site_url, *, limit=None, output_file=None, progress_file="progress.txt"):
    """Fetch indexed pages from a site.

    Parameters
    ----------
    site_url : str
        The Search Console property URL.
    limit : int, optional
        Maximum number of URLs to return. ``None`` returns all.
    output_file : str, optional
        File path to write all fetched URLs. Existing contents will be
        preserved and new URLs appended.
    progress_file : str, optional
        File used to store the next ``startRow`` when quota limits are
        reached. This allows the script to resume on subsequent runs.
    """

    service = get_service()
    start_row = 0
    row_limit = 25000
    pages = []

    if os.path.exists(progress_file):
        try:
            with open(progress_file) as f:
                start_row = int(f.read().strip())
                print(f"Resuming at row {start_row}")
        except (ValueError, OSError):
            start_row = 0

    out_fp = open(output_file, "a") if output_file else None

    while True:
        request = {
            'startDate': '2023-01-01',
            'endDate': '2023-12-31',
            'dimensions': ['page'],
            'rowLimit': row_limit,
            'startRow': start_row,
        }
        try:
            response = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        except Exception as exc:  # noqa: BLE001 - simple catch of API errors
            message = str(exc).lower()
            if any(tok in message for tok in ['rate limit', 'quota', 'userratelimitexceeded']):
                print('Quota limit reached, saving progress.')
                with open(progress_file, 'w') as f:
                    f.write(str(start_row))
                if out_fp:
                    out_fp.close()
                return pages
            raise

        rows = response.get('rows', [])
        if not rows:
            break

        urls = [row['keys'][0] for row in rows]
        pages.extend(urls)
        if out_fp:
            for url in urls:
                out_fp.write(url + '\n')

        start_row += len(rows)
        with open(progress_file, 'w') as f:
            f.write(str(start_row))

        if limit and len(pages) >= limit:
            pages = pages[:limit]
            break
        if len(rows) < row_limit:
            break

    if out_fp:
        out_fp.close()
    if os.path.exists(progress_file):
        os.remove(progress_file)

    return pages


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fetch indexed pages from Google Search Console.')
    parser.add_argument('site_url', help='The property URL to query (e.g. https://example.com)')
    parser.add_argument('--limit', type=int, default=None, help='Show only the first N results')
    parser.add_argument('--output', help='File to export all fetched URLs')
    parser.add_argument('--progress', default='progress.txt', help='File to store progress when quotas are hit')
    args = parser.parse_args()

    urls = fetch_indexed_pages(args.site_url, limit=args.limit, output_file=args.output, progress_file=args.progress)
    for url in urls:
        print(url)
