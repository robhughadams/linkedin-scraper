import argparse
import os
import shutil
import sqlite3
import glob
import uuid
from datetime import datetime


LINKEDIN_DOMAINS = {'.linkedin.com', '.licdn.com'}


def find_firefox_profiles(windows_user=None):
    if windows_user:
        users_dir = '/mnt/c/Users'
        user_path = os.path.join(users_dir, windows_user)
        if not os.path.isdir(user_path):
            raise FileNotFoundError(f"Windows user directory not found: {user_path}")
        base = os.path.join(user_path, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles')
    else:
        users_dir = '/mnt/c/Users'
        if not os.path.isdir(users_dir):
            raise FileNotFoundError(f"Windows users directory not found: {users_dir}")
        candidates = sorted(os.listdir(users_dir))
        base = None
        for user in candidates:
            candidate = os.path.join(users_dir, user, 'AppData', 'Roaming', 'Mozilla', 'Firefox', 'Profiles')
            if os.path.isdir(candidate):
                base = candidate
                windows_user = user
                break
        if base is None:
            raise FileNotFoundError("No Firefox profiles found under any Windows user")

    profiles = glob.glob(os.path.join(base, '*.*'))
    return profiles, windows_user


def find_cookie_db(profile_dir):
    db = os.path.join(profile_dir, 'cookies.sqlite')
    if os.path.isfile(db):
        return db
    return None


def extract_cookies(profile_dir, verbose=False):
    db_path = find_cookie_db(profile_dir)
    if not db_path:
        return []

    if verbose:
        print(f"[cookies] Reading: {db_path}")

    tmp = f"/tmp/cookies-{uuid.uuid4().hex[:8]}.sqlite"
    shutil.copy2(db_path, tmp)
    try:
        conn = sqlite3.connect(tmp)
    except Exception:
        os.unlink(tmp)
        raise
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(moz_cookies)")
    columns = [row['name'] for row in cursor.fetchall()]

    if 'host' in columns:
        host_col = 'host'
    elif 'baseDomain' in columns:
        host_col = 'baseDomain'
    else:
        conn.close()
        return []

    query = f"""
        SELECT name, value, {host_col} AS domain, path, expiry, isSecure, isHttpOnly
        FROM moz_cookies
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    os.unlink(tmp)

    cookies = []
    for row in rows:
        domain = row['domain']
        if not any(domain.endswith(d) or domain == d for d in LINKEDIN_DOMAINS):
            continue

        expiry = row['expiry']
        if expiry and expiry > 1_000_000_000_000:
            expiry = expiry // 1_000_000
        elif expiry and expiry > 1_000_000_000:
            expiry = expiry // 1_000

        cookie = {
            'name': row['name'],
            'value': row['value'],
            'domain': domain,
            'path': row['path'],
            'secure': bool(row['isSecure']),
            'httpOnly': bool(row['isHttpOnly']),
        }
        if expiry:
            cookie['expires'] = int(expiry)
        cookies.append(cookie)

    if verbose:
        names = [c['name'] for c in cookies]
        print(f"[cookies] Found {len(cookies)} LinkedIn cookies: {names}")

    return cookies


def format_cookies(cookies):
    lines = []
    for c in cookies:
        expires = ''
        if 'expires' in c:
            dt = datetime.fromtimestamp(c['expires'])
            expires = f"  expires={dt.isoformat()}"
        lines.append(f"  {c['name']}={c['value'][:40]}...  domain={c['domain']}{expires}")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Extract LinkedIn cookies from Firefox')
    parser.add_argument('--user', help='Windows username')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Show profile paths without extracting')
    args = parser.parse_args()

    profiles, windows_user = find_firefox_profiles(args.user)

    if args.verbose:
        print(f"[cookies] Windows user: {windows_user}")
        print(f"[cookies] Profiles found: {len(profiles)}")

    all_cookies = []
    for profile in profiles:
        if args.dry_run:
            db = find_cookie_db(profile)
            status = "has cookies.sqlite" if db else "no cookies.sqlite"
            print(f"  {os.path.basename(profile)}  ({status})")
            continue

        cookies = extract_cookies(profile, verbose=args.verbose)
        all_cookies.extend(cookies)

    if args.dry_run:
        return

    if not all_cookies:
        print("No LinkedIn cookies found in any Firefox profile.")
        print("Make sure you're logged into LinkedIn in Windows Firefox.")
        return

    print(f"Found {len(all_cookies)} LinkedIn cookies:")
    print(format_cookies(all_cookies))


if __name__ == '__main__':
    main()
