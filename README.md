# Google Search Console Fetcher

This repository contains a simple Python script to retrieve URLs for a property in Google Search Console using the [Google Search Console API](https://developers.google.com/search/apis). The script queries the Search Analytics endpoint and lists pages that received impressions, which usually indicates that they are indexed.

## Requirements

- Python 3.8+
- `google-api-python-client`
- `google-auth-oauthlib`

Install the dependencies with:

```bash
pip install google-api-python-client google-auth-oauthlib
```

## Usage

1. Create OAuth client credentials in the [Google API Console](https://console.cloud.google.com/apis/credentials) and download the `client_secrets.json` file into this directory.
2. Run the script and follow the authentication prompts. A `token.json` file will be saved for future runs.

```bash
python fetch_gsc_indexed_urls.py https://example.com
```

Replace `https://example.com` with your site's property URL in Google Search Console (must include the scheme).

The script will output the pages returned by the API. Use `--limit 100` to show only the first 100 results or `--output urls.txt` to export all fetched URLs to `urls.txt`. Progress is automatically saved so the script can resume when API quotas are hit.

Note that the API does not provide a guaranteed exhaustive list of all indexed pages; it returns only pages that recorded impressions in the selected date range. If a quota error stops the download early, rerun the command later and it will continue from where it left off.
