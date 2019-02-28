# -*- coding: utf-8 -*-

import re
import urllib
import requests


class HttpClient(object):
    def __init__(self):
        self.session = requests.Session()

    @staticmethod
    def _write_debug_file(filename, text, *args):
        pass

    def get(self, url):
        try:
            response = self.session.get(url, timeout=10.0)
        except requests.RequestException as exc:
            print("RequestException: {}".format(type(exc).__name__))
            print(url)
            return None
        if response.status_code != 200:
            print("HTTP Status Code {} {}".format(response.status_code, response.reason))
            print(url)
            return None
        return response

    def get_text(self, url, encoding=None):
        response = self.get(url)
        if response is None:
            return None
        if encoding:
            response.encoding = encoding
        return response.text

    def get_json(self, url, debug_file=None):
        response = self.get(url)
        if response is None:
            return None
        return response.json()


# street_pattern = re.compile(r"^(.*?)(\d+\s*[a-z]?(?:-\d+\s*[a-z]?)?)\s*$")
district_pattern = re.compile(r"^(.*?)\s*/?\s*OT.*$")

def strip_district(city):
    m = district_pattern.match(city)
    if m is not None:
        return m.group(1)
    return None


class ReverseGeoCoder(object):

    def __init__(self):
        self.http = HttpClient()
        self.base_url = 'http://nominatim.openstreetmap.org/search'

    def _build_url(self, query):
        return self.base_url + '?' + '&'.join([k + '=' + urllib.parse.quote_plus(str(v)) for k, v in query.items()])

    @staticmethod
    def _format_query(query):
        if 'q' in query:
            return query['q']
        parts = []
        if 'country' in query:
            parts.append(query['country'])
        if 'city' in query and 'postalcode' in query:
            parts.append(query['postalcode'] + ' ' + query['city'])
        elif 'city' in query:
            parts.append(query['city'])
        elif 'postalcode' in query:
            parts.append(query['postalcode'])
        if 'street' in query:
            parts.append(query['street'])
        return ', '.join(parts)

    @staticmethod
    def _build_query(country, city, postalcode, street, house_number, **kwargs):
        query = {}
        if country:
            query['country'] = country
        if city:
            query['city'] = city
        if postalcode:
            query['postalcode'] = postalcode
        if street and house_number:
            query['street'] = '{} {}'.format(house_number, street)
        elif street:
            query['street'] = street
        return query

    @staticmethod
    def _build_soft_query(**kwargs):
        return {'q': __class__._format_query(__class__._build_query(**kwargs))}

    def _lookup(self, query):
        query['limit'] = 1
        query['format'] = 'json'
        if 'country' in query and query['country'] == 'Schweiz':
            query['countrycodes'] = 'ch'
        elif 'country' in query and query['country'] == 'Österreich':
            query['countrycodes'] = 'at'
        else:
            query['countrycodes'] = 'de'
        url = self._build_url(query)
        data = self.http.get_json(url)
        if data is None or len(data) == 0:
            print("DID NOT RESOLVE LOCATION FOR {}".format(
                  self._format_query(query)))
            return None
        else:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return {
                'latitude': float(lat),
                'longitude': float(lon)
            }

    def lookup(self, **kwargs):
        template = {
            'country': '',
            'city': '',
            'postalcode': '',
            'street': '',
            'house_number': '',
        }
        template.update(kwargs)
        kwargs = template

        # try structured query method
        kwargs2 = kwargs.copy()
        org_query = query = self._build_query(**kwargs2)
        result = self._lookup(query)

        # strip potentially existing district
        stripped_city = strip_district(kwargs['city'])
        if result is None and stripped_city:
            kwargs2['city'] = stripped_city
            query = self._build_query(**kwargs2)
            result = self._lookup(query)

        # omit street
        if result is None and kwargs2['street']:
            kwargs2['street'] = None
            query = self._build_query(**kwargs2)
            result = self._lookup(query)

        # try unstructured query method
        if result is None:
            kwargs2 = dict(kwargs)
            query = self._build_soft_query(**kwargs2)
            result = self._lookup(query)

        # strip potentially existing district
        if result is None and stripped_city:
            kwargs2['city'] = stripped_city
            query = self._build_soft_query(**kwargs2)
            result = self._lookup(query)

        # omit street
        if result is None and kwargs2['street']:
            kwargs2['street'] = None
            query = self._build_soft_query(**kwargs2)
            result = self._lookup(query)

        if result is None:
            print("FAILED TO GEOCODE {}".format(
                  self._format_query(org_query)))
        return result
