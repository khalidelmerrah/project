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


def get_index_status(service, site_url, url):
    """Return "Indexed" or "NotIndexed" for a given URL using the URL Inspection API."""
    try:
        result = (
            service.urlInspection()
            .index()
            .inspect(body={"inspectionUrl": url, "siteUrl": site_url})
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to inspect {url}: {exc}")
        return "Unknown"

    coverage = (
        result.get("inspectionResult", {})
        .get("indexStatusResult", {})
        .get("coverageState")
    )
    if coverage and "indexed" in coverage.lower():
        return "Indexed"
    return "NotIndexed"


def fetch_indexed_pages(service, site_url, *, limit=None, progress_file="progress.txt"):
    """Fetch indexed pages from a site using the Search Analytics API.

    Parameters
    ----------
    service : Resource
        Authorized Search Console service instance.
    site_url : str
        The Search Console property URL.
    limit : int, optional
        Maximum number of URLs to return. ``None`` returns all.
    progress_file : str, optional
        File used to store the next ``startRow`` when quota limits are
        reached. This allows the script to resume on subsequent runs.
    """

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
                return pages
            raise

        rows = response.get('rows', [])
        if not rows:
            break

        urls = [row['keys'][0] for row in rows]
        pages.extend(urls)

        start_row += len(rows)
        with open(progress_file, 'w') as f:
            f.write(str(start_row))

        if limit and len(pages) >= limit:
            pages = pages[:limit]
            break
        if len(rows) < row_limit:
            break

    if os.path.exists(progress_file):
        os.remove(progress_file)

    return pages


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Fetch indexed pages from Google Search Console.'
    )
    parser.add_argument(
        'site_url',
        help='The property URL to query (e.g. https://example.com)'
    )
    parser.add_argument(
        '--limit', type=int, default=None, help='Show only the first N results'
    )
    parser.add_argument('--output', help='File to export all fetched URLs')
    parser.add_argument(
        '--progress',
        default='progress.txt',
        help='File to store progress when quotas are hit'
    )
    args = parser.parse_args()

    service = get_service()
    urls = fetch_indexed_pages(
        service,
        args.site_url,
        limit=args.limit,
        progress_file=args.progress,
    )

    results = []
    for url in urls:
        status = get_index_status(service, args.site_url, url)
        results.append((url, status))
        print(f"{url}\t{status}")

    if args.output:
        with open(args.output, "a") as fp:
            for url, status in results:
                fp.write(f"{url}\t{status}\n")
