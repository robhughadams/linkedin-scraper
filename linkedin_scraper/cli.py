import argparse
import json
import sys
import os

from .cookies import find_firefox_profiles, extract_cookies, format_cookies
from .client import LinkedInClient
from .search import parse_people_search, search_people, search_posts
from .profile import get_profile


def cmd_cookies(args):
    profiles, windows_user = find_firefox_profiles(args.user)

    all_cookies = []
    for profile in profiles:
        cookies = extract_cookies(profile, verbose=args.verbose)
        all_cookies.extend(cookies)

    if args.json:
        print(json.dumps(all_cookies, indent=2))
        return

    if not all_cookies:
        print("No LinkedIn cookies found — make sure you're logged into LinkedIn in Windows Firefox.")
        sys.exit(1)

    print(f"Windows user: {windows_user}")
    print(f"LinkedIn cookies ({len(all_cookies)}):")
    print(format_cookies(all_cookies))


def cmd_search_people(args):
    client = _make_client()
    page = args.page

    if args.from_url:
        resp = client.get_search_by_url(args.from_url)
        results = parse_people_search(resp.text)
    else:
        results = search_people(client, args.keywords, page=page)

        if args.all_pages:
            all_results = list(results)
            for p in range(2, 10):
                batch = search_people(client, args.keywords, page=p)
                if not batch:
                    break
                all_results.extend(batch)
            results = all_results

    if args.csv:
        import csv, io
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(['name', 'headline', 'location', 'profile_url', 'urn'])
        for r in results:
            w.writerow([
                r.get('name', ''),
                r.get('headline', ''),
                r.get('location', ''),
                r.get('profile_url', ''),
                r.get('urn', ''),
            ])
        print(buf.getvalue(), end='')
        return

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("No results found.")
        return

    print(f"People results for '{args.keywords}':\n")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r.get('name', '(no name)')}")
        if r.get('headline'):
            print(f"     {r['headline']}")
        if r.get('location'):
            print(f"     {r['location']}")
        if r.get('profile_url'):
            print(f"     {r['profile_url']}")
        print()


def cmd_search_posts(args):
    client = _make_client()
    results = search_posts(client, args.keywords, page=args.page)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("No results found.")
        return

    print(f"Post results for '{args.keywords}':\n")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r.get('author', 'Unknown')}")
        if r.get('date'):
            print(f"     {r['date']}")
        if r.get('text'):
            text = r['text'][:200]
            print(f"     {text}...")
        if r.get('url'):
            print(f"     {r['url']}")
        print()


def cmd_profile(args):
    client = _make_client()
    profile = get_profile(client, args.username)

    if args.json:
        print(json.dumps(profile, indent=2))
        return

    print(f"Profile: {args.username}\n")
    for key, val in profile.items():
        if isinstance(val, list):
            print(f"  {key}:")
            for item in val:
                if isinstance(item, dict):
                    parts = [f"{k}={v}" for k, v in item.items() if v]
                    print(f"    - {', '.join(parts)}")
                else:
                    print(f"    - {item}")
        elif isinstance(val, str):
            if len(val) > 200:
                print(f"  {key}: {val[:200]}...")
            else:
                print(f"  {key}: {val}")
        else:
            print(f"  {key}: {val}")
        print()


def cmd_connections(args):
    client = _make_client()

    try:
        resp = client.get(f'/in/{args.username}/details/connections/')
    except PermissionError as e:
        print(f"Error: {e}")
        print("Connections scraping requires specific LinkedIn permissions.")
        sys.exit(1)

    print(f"Connections page fetched for {args.username}.")
    print("Note: LinkedIn limits connection visibility — this may show an empty list.")


def _make_client():
    profiles, _ = find_firefox_profiles(None)
    all_cookies = []
    for profile in profiles:
        cookies = extract_cookies(profile)
        all_cookies.extend(cookies)

    if not all_cookies:
        print("No LinkedIn cookies found. Run 'linkedin-scraper cookies' first.")
        sys.exit(1)

    return LinkedInClient(all_cookies)


def main():
    parser = argparse.ArgumentParser(
        description='LinkedIn scraper — HTTP requests with Firefox cookies',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_cookies = sub.add_parser('cookies', help='Extract and display LinkedIn cookies from Firefox')
    p_cookies.add_argument('--user', help='Windows username')
    p_cookies.add_argument('--verbose', '-v', action='store_true')
    p_cookies.add_argument('--json', action='store_true', help='Output as JSON')
    p_cookies.set_defaults(func=cmd_cookies)

    p_search_people = sub.add_parser('search', help='Search LinkedIn')
    p_search_sub = p_search_people.add_subparsers(dest='search_type', required=True)

    p_people = p_search_sub.add_parser('people', help='Search for people')
    p_people.add_argument('keywords', nargs='?', default='', help='Search keywords')
    p_people.add_argument('--page', type=int, default=1)
    p_people.add_argument('--from-url', help='Full LinkedIn search URL to fetch')
    p_people.add_argument('--all-pages', action='store_true', help='Iterate all pages')
    p_people.add_argument('--json', action='store_true')
    p_people.add_argument('--csv', action='store_true')
    p_people.set_defaults(func=cmd_search_people)

    p_posts = p_search_sub.add_parser('posts', help='Search for posts')
    p_posts.add_argument('keywords', help='Search keywords')
    p_posts.add_argument('--page', type=int, default=1)
    p_posts.add_argument('--json', action='store_true')
    p_posts.set_defaults(func=cmd_search_posts)

    p_profile = sub.add_parser('profile', help='Get a LinkedIn profile')
    p_profile.add_argument('username', help='LinkedIn username (from /in/<username>)')
    p_profile.add_argument('--json', action='store_true')
    p_profile.set_defaults(func=cmd_profile)

    p_conns = sub.add_parser('connections', help='Get 1st-degree connections')
    p_conns.add_argument('username', help='LinkedIn username')
    p_conns.set_defaults(func=cmd_connections)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
