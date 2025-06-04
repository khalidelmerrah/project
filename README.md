# Google Search Console Fetcher

This repository contains a simple Python script to retrieve URLs for a property in Google Search Console using the [Google Search Console API](https://developers.google.com/search/apis). The script queries the Search Analytics endpoint and lists pages that received impressions, which usually indicates that they are indexed. For each URL the script also contacts the URL Inspection API to report whether Google currently considers the page indexed.

## Requirements

- Python 3.8+
- `google-api-python-client`
- `google-auth-oauthlib`

Install the dependencies with:

```bash
pip install google-api-python-client google-auth-oauthlib
```

## Usage

1. Enable the **Search Console API** in the [Google API Console](https://console.cloud.google.com/apis/library).
2. Create OAuth **Desktop** credentials in the API Console and download the `client_secrets.json` file into this directory.
3. Ensure the Google account you use for OAuth has access to the Search Console property. If not, add it as a *full user* in Search Console.
4. Run the script and follow the authentication prompts. A `token.json` file will be saved for future runs.

```bash
python fetch.py https://example.com
```

Replace `https://example.com` with your site's property URL in Google Search Console (must include the scheme).

The script outputs one URL per line with either `Indexed` or `NotIndexed` appended. Use `--limit 100` to show only the first 100 results or `--output urls.txt` to export all fetched URLs and their status to `urls.txt`. Progress is automatically saved so the script can resume when API quotas are hit.

Note that the API does not provide a guaranteed exhaustive list of all indexed pages; it returns only pages that recorded impressions in the selected date range. If a quota error stops the download early, rerun the command later and it will continue from where it left off.
