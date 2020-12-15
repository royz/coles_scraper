import asyncio
import time

import aiohttp


class Coles:

    def __init__(self):
        self.subscription_key = '2905142349a44ee3a8a418201d1535c4'
        self.headers = headers = {
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
            print(f'failed to get search result')
            err(e)

    async def _get_all_suggestions(self, items):
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [coles.get_suggestions(session, item) for item in items]
            results = await asyncio.gather(*tasks)
            return [result for result in results if result]

    def get_all_suggestions(self, items):
        suggestions = asyncio.run(self._get_all_suggestions(items))
        return suggestions

    async def get_location(self, item_name, store_id):
        params = {
            'searchTerm': 'sugar',
            'storeId': '406',
            'start': '0',
            'limit': '20',
            'searchToggle': '1',
            'latitude': '-34.956463',
            'longitude': '138.565066',
            'distance': '10.0',
        }

        url = 'https://apigw.coles.com.au/digital/colesappbff/v1/products/search/suggestions'
        try:
            async with session.get(url, params=params) as response:
                json_response, status_code = await response.json(), response.status
                # print(status_code)
                return json_response['results'][0]['text']
        except Exception as e:
            print(f'failed to get search result')
            err(e)

    def get_all_aisles(self):
        pass


def err(er):
    print('-' * 100)
    print(err)
    print('-' * 100)


if __name__ == '__main__':
    items = ['milk', 'biscuit', 'sugar'] * 50
    coles = Coles()
    start = time.time()
    suggestions = coles.get_all_suggestions(items)
    print(suggestions)
    print(f'time taken: {time.time() - start} sec')
