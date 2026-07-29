# linkedin-scraper

HTTP-requests-based LinkedIn scraper using session cookies extracted from Windows Firefox.

No browser automation — just `requests` + cookies from Firefox's `cookies.sqlite`.

## Usage

```bash
# Extract cookies from Windows Firefox
uv run linkedin-scraper cookies

# Search for people
uv run linkedin-scraper search people "data engineer"

# Search for posts
uv run linkedin-scraper search posts "python"

# Get a profile
uv run linkedin-scraper profile johndoe

# Get connections
uv run linkedin-scraper connections johndoe
```

## How it works

1. Extracts LinkedIn session cookies from Windows Firefox's `cookies.sqlite` (plaintext, mounted at `/mnt/c/`)
2. Creates a `requests.Session` authenticated with those cookies
3. Fetches LinkedIn HTML pages and parses structured data with BeautifulSoup
4. Supports LinkedIn's Voyager GraphQL API via `csrf-token` header
