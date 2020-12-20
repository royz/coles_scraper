import asyncio
import csv
import json
import time
from pprint import pprint
import os
import aiohttp
import requests


class Coles:

    def __init__(self):
        self.subscription_key = '2905142349a44ee3a8a418201d1535c4'
        self.headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'X-App-Platform': 'Android',
            'X-OS-Version': '6.0',
            'content-type': 'application/json',
            'X-App-Version': '3.19.0',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0; Coles Build/MRA58K)',
            'Host': 'apigw.coles.com.au',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }

    @staticmethod
    async def get_suggestions(session, item_name):
        params = {
            'searchTerm': item_name,
            'storeId': 406
        }

        url = 'https://apigw.coles.com.au/digital/colesappbff/v1/products/search/suggestions'
        try:
            async with session.get(url, params=params) as response:
                json_response, status_code = await response.json(), response.status
                # print(status_code)
                return json_response['results'][0]['text']
        except Exception as e:
            # print(f'failed to get search result')
            # err(e)
            pass

    async def _get_all_suggestions(self, items):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [coles.get_suggestions(session, item) for item in items]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result]

    def get_all_suggestions(self, items):
        suggestions = asyncio.run(self._get_all_suggestions(items))
        return suggestions

    @staticmethod
    async def get_aisle(session, item_name, store_id):
        params = {
            'searchTerm': item_name,
            'storeId': store_id,
            'start': '0',
            'limit': '20',
            'searchToggle': '1',
        }

        url = 'https://apigw.coles.com.au/digital/colesappbff/v1/products/search'
        try:
            async with session.get(url, params=params) as response:
                json_response, status_code = await response.json(), response.status
                # print(status_code)
                return item_name, json_response['Results'][0]['Locations'][0]['Aisle']
        except Exception as e:
            print(f'failed to get aisle for {item_name}')
            err(e)

    async def _get_all_aisles(self, items):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [coles.get_aisle(session, item, '406') for item in items]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result]

    def get_all_aisles(self, items):
        aisles = asyncio.run(self._get_all_aisles(items))
        return aisles

    @staticmethod
    def search_stores():
        duplicates = []
        if not os.path.exists(file('input', 'coles_stores_coordinates.csv')):
            print('coles_stores_coordinates.csv not found')
            quit()
        with open(file('input', 'coles_stores_coordinates.csv')) as f:
            reader = csv.reader(f)
            coordinates = []
            for row in reader:
                if ''.join(row) in duplicates:
                    pass
                else:
                    duplicates.append(''.join(row))
                    coordinates.append(row)

            stores = {}
            for i, coordinate in enumerate(coordinates):
                print(f'[{i + 1} / {len(coordinates)}] {coordinate}:', end=' ')
                params = {
                    'latitude': float(coordinate[0]),
                    'longitude': float(coordinate[1]),
                    'brandIds': '2,1',
                    'numberOfStores': 15,
                }
                response = requests.get('https://apigw.coles.com.au/digital/colesweb/v1/stores/search', params=params)
                new_stores = response.json()['stores']
                new_stores = {new_store['storeId']: new_store for new_store in new_stores}
                previous_store_count = len(stores)
                stores.update(new_stores)
                print(f'{len(new_stores)} stores found. {len(stores) - previous_store_count} new.')
        with open(file('cache', 'stores.json'), 'w', encoding='utf-8') as f:
            json.dump(stores, f, indent=2)


def file(*filepath):
    return os.path.join(os.path.dirname(__file__), *filepath)


def err(er):
    print('-' * 100)
    print(err)
    print('-' * 100)


if __name__ == '__main__':
    coles = Coles()
    coles.search_stores()
