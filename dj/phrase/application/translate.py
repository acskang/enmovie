import requests
import re
from urllib.parse import quote

class LibreTranslator:
    def __init__(self):
        # MyMemory API 사용 (더 안정적)
        self.api_url = "https://api.mymemory.translated.net/get"
    
    def is_korean(self, text):
        korean_pattern = re.compile(r'[가-힣]')
        return bool(korean_pattern.search(text))
    
    def translate_to_english(self, text):
        if not self.is_korean(text):
            return text
        
        if len(text.strip()) < 2:
            return text
        
        try:
            # URL 파라미터로 전송
            params = {
                'q': text,
                'langpair': 'ko|en'
            }
            
            response = requests.get(self.api_url, params=params, timeout=10)
            print(f"API 응답 상태: {response.status_code}")
            print(f"API 응답 내용: {response.text[:200]}...")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('responseStatus') == 200:
                    translated_text = result['responseData']['translatedText']
                    print(f"번역 성공: '{text}' → '{translated_text}'")
                    return translated_text
                else:
                    print(f"API 응답 오류: {result}")
                    return text
            else:
                print(f"HTTP 오류: {response.status_code}")
                return text
                
        except Exception as e:
            print(f"번역 중 오류: {e}")
            return text