from bs4 import BeautifulSoup
from urllib.parse import urljoin


def parse_people_search(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    entities = soup.select('li[data-entity-urn*="urn:li:person:"]')
    if not entities:
        entities = soup.select('li.reusable-search__result-container')

    for entity in entities:
        result = {}

        name_el = entity.select_one('a[href*="/in/"] span[aria-hidden="true"]')
        if not name_el:
            name_el = entity.select_one('.entity-result__title-text a span[aria-hidden="true"]')
        if not name_el:
            name_el = entity.select_one('a[href*="/in/"]')
            if name_el:
                name_el = name_el.find('span', string=True)
        if name_el:
            result['name'] = name_el.get_text(strip=True)

        link_el = entity.select_one('a[href*="/in/"]')
        if link_el:
            href = link_el.get('href', '')
            result['profile_url'] = urljoin('https://www.linkedin.com', href)

        headline_el = entity.select_one('.entity-result__primary-subtitle')
        if not headline_el:
            headline_el = entity.select_one('.search-result__info')
        if headline_el:
            result['headline'] = headline_el.get_text(strip=True)

        location_el = entity.select_one('.entity-result__secondary-subtitle')
        if not location_el:
            location_el = entity.select_one('.search-result__truncation')
        if location_el:
            result['location'] = location_el.get_text(strip=True)

        if result.get('name') or result.get('profile_url'):
            results.append(result)

    return results


def parse_content_search(html):
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    articles = soup.select('li[data-entity-urn*="urn:li:activity:"]')
    if not articles:
        articles = soup.select('li.reusable-search__result-container')

    for article in articles:
        result = {}

        text_el = article.select_one('.update-components-text')
        if text_el:
            spans = text_el.find_all('span', attrs={'dir': 'ltr'})
            result['text'] = ' '.join(
                s.get_text(strip=True) for s in spans if s.get_text(strip=True)
            )

        link_el = article.select_one('a[href*="/feed/update/"]')
        if link_el:
            href = link_el.get('href', '')
            result['url'] = urljoin('https://www.linkedin.com', href)

        author_el = article.select_one('.update-components-actor__name a')
        if author_el:
            result['author'] = author_el.get_text(strip=True)

        date_el = article.select_one('.update-components-actor__sub-description')
        if not date_el:
            date_el = article.select_one('time')
        if date_el:
            result['date'] = date_el.get_text(strip=True)

        if result.get('text') or result.get('url'):
            results.append(result)

    return results


def search_people(client, keywords, page=1):
    resp = client.get_search_html('people', keywords, page=page)
    return parse_people_search(resp.text)


def search_posts(client, keywords, page=1):
    resp = client.get_search_html('content', keywords, page=page)
    return parse_content_search(resp.text)
