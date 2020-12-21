import asyncio
import csv
import json
import time
import os
import aiohttp
import requests
import config
import glob
import re


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
        self.stores = None
        self.get_stores()

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
            # print(f'failed to get aisle for {item_name}')
            # err(e)
            pass

    async def _get_all_aisles(self, items, store_id):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [coles.get_aisle(session, item, store_id) for item in items]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result]

    def get_all_aisles(self, items, store_id):
        aisles = asyncio.run(self._get_all_aisles(items, store_id))
        return aisles

    def search_stores(self):
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

            for i, coordinate in enumerate(coordinates):
                print(f'[{i + 1} / {len(coordinates)}] {coordinate}:', end=' ')
                params = {
                    'latitude': float(coordinate[0]),
                    'longitude': float(coordinate[1]),
                    'brandIds': '2,1',
                    'numberOfStores': 15,
                }
                while True:
                    try:
                        response = requests.get('https://apigw.coles.com.au/digital/colesweb/v1/stores/search',
                                                params=params)
                        new_stores = response.json()['stores']
                        new_stores = {new_store['storeId']: new_store for new_store in new_stores}
                        previous_store_count = len(self.stores)
                        self.stores.update(new_stores)
                        print(f'{len(new_stores)} stores found. {len(self.stores) - previous_store_count} new.')
                        break
                    except:
                        print('failed to connect. retrying in 5 seconds...')
                        time.sleep(5)

        with open(file('cache', 'stores.json'), 'w', encoding='utf-8') as f:
            json.dump(self.stores, f, indent=2)

    def get_stores(self):
        if os.path.exists(file('cache', 'stores.json')):
            with open(file('cache', 'stores.json'), encoding='utf-8') as f:
                self.stores = json.load(f)
        else:
            self.stores = {}

    @staticmethod
    def get_items():
        if not os.path.exists(file('input', 'items.csv')):
            print('items.csv not found')
            quit()
        else:
            with open(file('input', 'items.csv'), encoding='utf-8') as f:
                return list(map(lambda x: x.strip(), f.read().split('\n')))

    @staticmethod
    def save_aisle(data, store_id, store_name):
        with open(file('aisles', f'{store_name}-{store_id}.csv'), 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(data)


class Importer:
    def __init__(self):
        self.session = requests.session()
        self.import_session = requests.session()
        self.files = None
        self.form_body_template = None

    def login(self):
        print('logging in to speedshopperapp dashboard...')

        self.session.headers = {
            'Referer': 'https://www.speedshopperapp.com/app/admin/login',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'
        }

        payload = {
            'username': config.import_username,
            'password': config.import_password
        }

        response = self.session.post('https://www.speedshopperapp.com/app/admin/login', data=payload)

        if '<title>Dashboard</title>' in response.text:
            print('logged in')
            self.import_session.headers = {
                'Host': 'www.speedshopperapp.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'multipart/form-data; boundary=---------------------------1267546269709',
                'Origin': 'https://www.speedshopperapp.com',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            self.import_session.cookies = self.session.cookies
        else:
            print('login failed. check your username and password in import_user.json file')
            quit()

    def get_files(self):
        self.files = glob.glob('aisles/*.csv')
        if len(self.files) == 0:
            print('no csv files found under aisle_data folder')
            quit()
        count = len(self.files)
        print(f'{count} {"file" if count == 1 else "files"} found')

    def search_store(self, address='', name=''):
        data = {
            'draw': '2',
            'columns[0][data]': '0',
            'columns[0][name]': '',
            'columns[0][searchable]': 'true',
            'columns[0][orderable]': 'true',
            'columns[0][search][value]': '',
            'columns[0][search][regex]': 'false',
            'columns[1][data]': '1',
            'columns[1][name]': '',
            'columns[1][searchable]': 'true',
            'columns[1][orderable]': 'true',
            'columns[1][search][value]': '',
            'columns[1][search][regex]': 'false',
            'columns[2][data]': '2',
            'columns[2][name]': '',
            'columns[2][searchable]': 'true',
            'columns[2][orderable]': 'true',
            'columns[2][search][value]': '',
            'columns[2][search][regex]': 'false',
            'columns[3][data]': '3',
            'columns[3][name]': '',
            'columns[3][searchable]': 'true',
            'columns[3][orderable]': 'true',
            'columns[3][search][value]': '',
            'columns[3][search][regex]': 'false',
            'columns[4][data]': '4',
            'columns[4][name]': '',
            'columns[4][searchable]': 'true',
            'columns[4][orderable]': 'true',
            'columns[4][search][value]': '',
            'columns[4][search][regex]': 'false',
            'columns[5][data]': '5',
            'columns[5][name]': '',
            'columns[5][searchable]': 'true',
            'columns[5][orderable]': 'true',
            'columns[5][search][value]': '',
            'columns[5][search][regex]': 'false',
            'columns[6][data]': '6',
            'columns[6][name]': '',
            'columns[6][searchable]': 'true',
            'columns[6][orderable]': 'true',
            'columns[6][search][value]': '',
            'columns[6][search][regex]': 'false',
            'columns[7][data]': '7',
            'columns[7][name]': '',
            'columns[7][searchable]': 'true',
            'columns[7][orderable]': 'true',
            'columns[7][search][value]': '',
            'columns[7][search][regex]': 'false',
            'columns[8][data]': '8',
            'columns[8][name]': '',
            'columns[8][searchable]': 'true',
            'columns[8][orderable]': 'false',
            'columns[8][search][value]': '',
            'columns[8][search][regex]': 'false',
            'order[0][column]': '0',
            'order[0][dir]': 'asc',
            'start': '0',
            'length': '50000',
            'search[value]': '',
            'search[regex]': 'false',
            'name': name,
            'address': address
        }

        res = self.session.post('https://www.speedshopperapp.com/app/admin/stores/getstores', data=data)

        try:
            data = res.json()['data'][0]
            return re.search(r'[0-9]+', data[4]).group()
        except IndexError:
            return None

    def import_file(self, file_path, filename, store_id):
        """imports a csv file in the website"""
        response = self.import_session.post('https://www.speedshopperapp.com/app/admin/stores/importFile',
                                            data=self.get_form_body(file_path, filename, store_id))

        if 'Imported items successfully' in response.text:
            return True
        return False

    def get_form_body(self, file_path, file_name, store_id):
        if not self.form_body_template:
            try:
                with open('request-body.txt', encoding='utf-8') as f:
                    self.form_body_template = f.read().strip()
            except:
                print('request-body.txt not found')
                quit()

        with open(file_path, encoding='utf-8') as f:
            data = f.read().strip()

        # remove items with "char" in name
        data = '\n'.join([line for line in data.split('\n') if 'char' not in line.lower() and 'c ' not in line.lower()])

        body = self.form_body_template % (config.import_id, file_name, data, store_id)
        return body.encode('utf-8')


def file(*filepath):
    full_path = os.path.join(os.path.dirname(__file__), *filepath)
    print('path:', full_path)
    return full_path


def err(er):
    print('-' * 100)
    print(er)
    print('-' * 100)


if __name__ == '__main__':
    coles = Coles()

    print('choose an option:')
    print('1. search stores\n2. get aisles\n3. import csv')
    option = input('option: ')
    if option == '1':
        coles.search_stores()
    elif option == '2':
        item_names = coles.get_items()
        suggestions = coles.get_all_suggestions(item_names)

        for i, store in enumerate(coles.stores.values()):
            if os.path.exists(file('aisles', f'{store["storeName"]}-{store["storeId"]}.csv')):
                print(f'[{i + 1}/{len(coles.stores)}] {store["storeId"]}-{store["storeName"]}: already scraped')
                continue

            aisles = coles.get_all_aisles(suggestions, store['storeId'])
            if not aisles:
                # print(f'[{i + 1}/{len(coles.stores)}] store: {store["storeId"]} - data not found')
                pass
            else:
                coles.save_aisle(aisles, store['storeId'], store['storeName'])
                print(f'[{i + 1}/{len(coles.stores)}] saved: {store["storeName"]}-{store["storeId"]}.csv')
    elif option == '3':
        importer = Importer()
        importer.login()
        importer.get_files()
        print('-' * 75)
        for file in importer.files:
            filename = file.split('\\')[-1]
            print(f'filename: {filename}')
            store_id = filename[:-4].split('-')[-1]
            print(f'store id: {store_id}')
            street_address = coles.stores[store_id]['address']
            print(f'street address: {street_address}')
            site_id = importer.search_store(address=street_address)
            if not site_id:
                print('store not found on speedshopperapp')
                print('-' * 75)
                continue
            print(f'import url: https://www.speedshopperapp.com/app/admin/stores/import/{site_id}')
            success = importer.import_file(file, filename, site_id)
            if success:
                print('imported successfully')
            else:
                print('failed to import')
            print('-' * 75)
    else:
        print('choose a valid option')
