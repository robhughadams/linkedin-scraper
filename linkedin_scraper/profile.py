import json
import re
from bs4 import BeautifulSoup


def parse_json_ld(soup):
    data = {}
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            parsed = json.loads(script.string)
            if isinstance(parsed, dict):
                data.update(parsed)
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        if '@type' in item and item['@type'] == 'Person':
                            data.update(item)
        except (json.JSONDecodeError, TypeError):
            continue
    return data


def parse_profile(html):
    soup = BeautifulSoup(html, 'html.parser')
    profile = {}

    ld = parse_json_ld(soup)

    if ld.get('name'):
        profile['name'] = ld['name']
    else:
        name_el = soup.select_one('h1')
        if name_el:
            profile['name'] = name_el.get_text(strip=True)

    if ld.get('jobTitle'):
        profile['headline'] = ld['jobTitle']
    else:
        headline_el = soup.select_one('div.text-body-medium')
        if headline_el:
            profile['headline'] = headline_el.get_text(strip=True)

    if ld.get('address', {}).get('addressLocality'):
        profile['location'] = ld['address']['addressLocality']
    elif ld.get('address', {}).get('addressCountry'):
        profile['location'] = ld['address']['addressCountry']
    else:
        for cls in ['text-body-small', 'inline-show-more-text']:
            el = soup.select_one(f'tploca.{cls}, span.{cls}')
            if el:
                text = el.get_text(strip=True)
                if text and not text.startswith('http'):
                    profile['location'] = text
                    break

    if ld.get('description'):
        profile['about'] = ld['description']
    else:
        about_section = soup.select_one('section#about')
        if about_section:
            text_el = about_section.select_one('div.display-flex')
            if text_el:
                profile['about'] = text_el.get_text(strip=True)

    sections = soup.select('section')
    for section in sections:
        section_id = section.get('id', '')
        heading_el = section.select_one('h2, h3, .section-title')
        if heading_el:
            heading = heading_el.get_text(strip=True).lower()
        else:
            heading = section_id.lower()

        if 'experience' in heading or section_id == 'experience':
            items = _parse_experience(section)
            if items:
                profile['experience'] = items

        if 'education' in heading or section_id == 'education':
            items = _parse_education(section)
            if items:
                profile['education'] = items

        if 'skill' in heading or section_id == 'skills':
            items = _parse_skills(section)
            if items:
                profile['skills'] = items

    return profile


def _parse_experience(section):
    items = []
    for li in section.select('li'):
        item = {}
        title_el = li.select_one('span[aria-hidden="true"]')
        if title_el:
            item['title'] = title_el.get_text(strip=True)

        company_el = li.select_one('span.t-14.t-normal')
        if not company_el:
            company_el = li.select_one('span.t-14.t-black--light')
        if company_el:
            item['company'] = company_el.get_text(strip=True)

        date_el = li.select_one('span.t-14.t-normal.t-black--light')
        if date_el:
            text = date_el.get_text(strip=True)
            if text and '·' not in text:
                item['dates'] = text

        if item.get('title') or item.get('company'):
            items.append(item)
    return items


def _parse_education(section):
    items = []
    for li in section.select('li'):
        item = {}
        school_el = li.select_one('span[aria-hidden="true"]')
        if school_el:
            item['school'] = school_el.get_text(strip=True)

        degree_el = li.select_one('span.t-14.t-normal')
        if degree_el:
            item['degree'] = degree_el.get_text(strip=True)

        date_el = li.select_one('span.t-14.t-normal.t-black--light')
        if date_el:
            item['dates'] = date_el.get_text(strip=True)

        if item.get('school'):
            items.append(item)
    return items


def _parse_skills(section):
    items = []
    for span in section.select('span[aria-hidden="true"]'):
        text = span.get_text(strip=True)
        if text and len(text) < 100:
            items.append(text)
    return items


def get_profile(client, username):
    resp = client.get_profile_html(username)
    return parse_profile(resp.text)
