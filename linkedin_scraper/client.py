import requests


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0"
)


class LinkedInClient:
    def __init__(self, cookies=None):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.base_url = 'https://www.linkedin.com'
        self._csrf_token = None

        if cookies:
            self.set_cookies(cookies)

    def set_cookies(self, cookies):
        for c in cookies:
            self.session.cookies.set(
                c['name'],
                c['value'],
                domain=c.get('domain', '.linkedin.com'),
                path=c.get('path', '/'),
            )

        for c in cookies:
            if c['name'] == 'JSESSIONID' or c['name'] == 'li_at':
                raw = c['value']
                if raw.startswith('"') and raw.endswith('"'):
                    raw = raw[1:-1]
                self._csrf_token = raw
                break

        if self._csrf_token:
            self.session.headers['Csrf-Token'] = self._csrf_token
            self.session.headers['csrf-token'] = self._csrf_token

        self.session.headers['X-RestLi-Protocol-Version'] = '2.0.0'

    @property
    def csrf_token(self):
        return self._csrf_token

    def get(self, path, voyager=False, **kwargs):
        url = f'{self.base_url}{path}'
        headers = kwargs.pop('headers', {})

        if voyager:
            headers.setdefault('Accept', 'application/json')
            headers.setdefault('X-RestLi-Protocol-Version', '2.0.0')

        resp = self.session.get(url, headers=headers, **kwargs)

        if resp.status_code == 401:
            raise PermissionError("LinkedIn returned 401 — cookies may be expired")
        if resp.status_code == 403:
            raise PermissionError("LinkedIn returned 403 — cookies may be expired")
        if 'login' in resp.url.lower() and resp.url != url:
            raise PermissionError(
                f"Redirected to login page — cookies expired or invalid"
            )

        return resp

    def post(self, path, voyager=False, **kwargs):
        url = f'{self.base_url}{path}'
        headers = kwargs.pop('headers', {})

        if voyager:
            headers.setdefault('Accept', 'application/json')
            headers.setdefault('Content-Type', 'application/json')
            headers.setdefault('X-RestLi-Protocol-Version', '2.0.0')

        resp = self.session.post(url, headers=headers, **kwargs)

        if resp.status_code == 401:
            raise PermissionError("LinkedIn returned 401 — cookies may be expired")

        return resp

    def voyager_graphql(self, query_body):
        return self.post(
            '/voyager/api/graphql',
            voyager=True,
            json=query_body,
        )

    def get_profile_html(self, username):
        return self.get(f'/in/{username}/', voyager=False)

    def get_search_html(self, search_type, keywords, page=1):
        return self.get(
            f'/search/results/{search_type}/',
            params={'keywords': keywords, 'page': page},
            voyager=False,
        )
