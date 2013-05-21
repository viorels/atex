import requests
from bs4 import BeautifulSoup
from collections import namedtuple


def scrape_specs(code):
    specs = []
    Spec = namedtuple('Spec', ['name', 'value', 'group'])
    EXCLUDE_LIST = ("garage", "garantie", "drivere", "suport tehnic")
    page = get_product_page(code)
    if page:
        soup = BeautifulSoup(page)
        group = ''
        specs_table = soup('table', {'class': 'specs-table'})
        if len(specs_table) > 0:
            for row in specs_table[0].tbody('tr'):
                tds = row('td')
                if len(tds) == 1 and 'group' in tds[0].get('class'):
                    group = tds[0].text.strip()
                if len(tds) == 2:
                    spec, value = tds
                    spec_text = spec.text.strip().rstrip(':')
                    if any(excluded in spec_text.lower() for excluded in EXCLUDE_LIST):
                        continue
                    specs.append(Spec(group=group, name=spec_text, value=value.text.strip()))
    return specs


def get_product_page(code):
    r = requests.get('http://www.pcgarage.ro/cauta', params={'search': code})
    if '/cauta' in r.url:
        return ''
    return r.text
