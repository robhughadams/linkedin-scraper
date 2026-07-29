# linkedin-scraper — Agent Instructions

## Project Overview

An HTTP-requests-based LinkedIn scraper that:

1. **Extracts** session cookies from Windows Firefox's `cookies.sqlite` (WSL2, `/mnt/c/Users/`)
2. **Authenticates** a `requests.Session` with those cookies
3. **Scrapes** LinkedIn search results, profiles, and connections from HTML
4. **CLI** with subcommands for each operation

## Package Management

- **Always use `uv`** — never pip or conda.
- `uv add <package>` to add dependencies.
- `uv run linkedin-scraper <command>` to run.
- The project uses **Python >=3.13**.

## Project Structure

```
linkedin-scraper/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── LICENSE                 (AGPLv3)
├── .gitignore
├── linkedin_scraper/
│   ├── __init__.py
│   ├── cookies.py          # Extract cookies from Firefox profile
│   ├── client.py           # HTTP client with cookie auth
│   ├── search.py           # Search people/posts
│   ├── profile.py          # Get profiles
│   └── cli.py              # CLI entry point
```

## Running

```bash
uv run linkedin-scraper cookies --user robhu --verbose
uv run linkedin-scraper search people "data engineer"
uv run linkedin-scraper search posts "python"
uv run linkedin-scraper profile johndoe
uv run linkedin-scraper connections johndoe
```

## Key Conventions

- **Cookie extraction**: Reads Firefox `cookies.sqlite` from Windows (WSL2 path `/mnt/c/Users/`).
- **Error handling**: Graceful fallbacks if cookies expired or profile not found.
- **Parsing**: Uses BeautifulSoup for HTML parsing; JSON-LD script tags where available.

## GitHub

- Remote: `https://github.com/robhughadams/linkedin-scraper`
- License: AGPLv3
