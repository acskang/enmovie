import requests
from .clean_data import clean_data_from_playphrase
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

def get_movie_info(text):
    """
    playphrase.me API에서 영화 정보를 가져오는 함수
    """
    if not text or not text.strip():
        logger.warning("검색 텍스트가 비어있습니다.")
        return None
    
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
        'q': text.strip(),  # 공백 제거
        'limit': '10',
        'language': 'en',
        'platform': 'desktop safari',
        'skip': '0',
    }

    try:
        logger.info(f"playphrase.me API 요청: {text}")
        response = requests.get(
            'https://www.playphrase.me/api/v1/phrases/search', 
            params=params, 
            cookies=cookies, 
            headers=headers,
            timeout=30  # 타임아웃 설정
        )

        if response.status_code == 200:
            data = response.text
            
            # 응답 데이터 검증
            if not data or data.strip() == '':
                logger.warning(f"playphrase.me에서 빈 응답: {text}")
                return None
            
            # 에러 응답인지 확인
            if 'error' in data.lower() or 'not found' in data.lower():
                logger.warning(f"playphrase.me 에러 응답: {data[:100]}...")
                return None
            
            logger.info(f"playphrase.me API 응답 수신 성공: {len(data)} 문자")
            return data
            
        else:
            logger.error(f"API 요청 실패 - 상태 코드: {response.status_code}")
            logger.error(f"응답 내용: {response.text[:200]}...")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"API 요청 타임아웃: {text}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"API 연결 실패: {text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 중 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"예상치 못한 오류: {e}")
        return None