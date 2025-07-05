import requests
from .clean_data import clean_data_from_playphrase

# 텍스트가 있는 영화 찾기
def get_movie_info(text):
    cookies = {
        'ring-session': '1899c079-0a8e-44da-a1a0-e3a3562dfd53',
    }

    headers = {
        'accept': 'json',
        'accept-language': 'en-US,en;q=0.8',
        'authorization': 'Token',
        'content-type': 'json',
        'priority': 'u=1, i',
        'referer': 'https://www.playphrase.me/',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-csrf-token': 'cmf6ALYjeK3Xxi1Wobc1dIitdPqz+IjROylUqKHePZ+HQCkfROzIedaKmgSWlbgJogBBpd5HpkcmvFLF',
    }

    params = {
        'q': text,  # Use the text parameter passed to the function instead of a hardcoded string
        'limit': '10',
        'language': 'en',
        'platform': 'desktop safari',
        'skip': '0',
    }

    response = requests.get('https://www.playphrase.me/api/v1/phrases/search', params=params, cookies=cookies, headers=headers)

    if response.status_code == 200:
        data = response.text
        return data
    else:
        print("API 요청 실패", response.status_code, response.text)
        return [] # Return an empty list if the request fails]