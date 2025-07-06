import re
import json
from phrase.models import Movie, MovieQuote
from phrase.application.get_imdb_poster_url import get_poster_url,download_poster_image

def decode_playphrase_format(text):
    """
    playphrase.me의 특수 인코딩을 표준 JSON으로 변환
    ° -> {, ç -> }, ¡ -> [, ¿ -> ]
    """
    # None이나 빈 문자열 체크
    if not text:
        return ""
    
    # 특수 문자를 JSON 표준 문자로 변환
    text = text.replace('°', '{')
    text = text.replace('ç', '}')
    text = text.replace('¡', '[')
    text = text.replace('¿', ']')
    
    # 작은따옴표를 큰따옴표로 변환 (JSON 표준)
    # 키-값 쌍의 키 부분
    text = re.sub(r"'([^']*?)':", r'"\1":', text)
    # 키-값 쌍의 값 부분 (문자열)
    text = re.sub(r": '([^']*?)'([,}\]])", r': "\1"\2', text)
    # 배열 내부 문자열
    text = re.sub(r"\['([^']*?)'\]", r'["\1"]', text)
    text = re.sub(r", '([^']*?)'([,\]])", r', "\1"\2', text)
    
    return text

def extract_movie_info(data_text):
    """
    playphrase.me 데이터에서 영화 정보 추출
    """
    # None이나 빈 데이터 체크
    if not data_text:
        print("입력 데이터가 없습니다.")
        return []
    
    # 문자열이 아닌 경우 (리스트 등) 처리
    if not isinstance(data_text, str):
        print(f"잘못된 데이터 타입: {type(data_text)}")
        return []
    
    try:
        # 데이터 디코딩
        decoded_text = decode_playphrase_format(data_text)
        
        # 빈 문자열 체크
        if not decoded_text.strip():
            print("디코딩된 데이터가 비어있습니다.")
            return []
        
        # JSON 파싱을 위한 추가 정리
        # 'searched?': True/False 형태 처리
        decoded_text = re.sub(r"'searched\?': (True|False)", r'"searched": \1', decoded_text)
        decoded_text = decoded_text.replace('True', 'true').replace('False', 'false')
        
        # 파싱 시도
        try:
            data = json.loads(decoded_text)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            # JSON 파싱 실패시 정규식으로 직접 추출
            return extract_with_regex(data_text)
        
        movies = []
        
        # phrases 배열에서 영화 정보 추출
        if 'phrases' in data and data['phrases']:
            for phrase in data['phrases']:
                movie_info = {}
                
                # video-info에서 info와 source_url 추출
                if 'video-info' in phrase and phrase['video-info']:
                    video_info = phrase['video-info']
                    
                    # info Data 를 name 과 start-time으로 분리
                    info_text = video_info.get('info', '')

                    # 정규 표현식을 사용하여 대괄호 안의 시간 부분을 찾습니다.
                    match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', info_text)

                    if match:
                        start_time = match.group(1)  # 대괄호 안의 시간 부분 (예: 00:21:27)
                        name = info_text.replace(f' [{start_time}]', '').strip() # 시간 부분을 제거하고 앞뒤 공백을 제거합니다.
                    else:
                        # 시간 형식이 없는 경우를 대비한 처리
                        name = info_text.strip()
                        start_time = "00:00:00"  # 기본값 설정

                    movie_info['start_time'] = start_time
                    movie_info['name'] = name                    
                    movie_info['source_url'] = video_info.get('source-url', '')
                
                # video-url과 text 추출
                movie_info['video_url'] = phrase.get('video-url', '')
                movie_info['text'] = phrase.get('text', '')
                
                # 필수 정보가 있는 경우만 추가
                if movie_info.get('name') and movie_info.get('text'):
                    movies.append(movie_info)
        else:
            print("phrases 데이터가 없거나 비어있습니다.")
        
        return movies
        
    except Exception as e:
        print(f"파싱 오류: {e}")
        return extract_with_regex(data_text)

def extract_with_regex(data_text):
    """
    정규식을 사용한 직접 추출 (JSON 파싱 실패시 대안)
    """
    # None이나 빈 데이터 체크
    if not data_text:
        return []
    
    movies = []
    
    try:
        # 각 영화 클립 블록을 찾기
        # °'video-info'부터 다음 °'video-info' 또는 끝까지
        pattern = r"°'video-info'.*?(?=°'video-info'|$)"
        matches = re.findall(pattern, data_text, re.DOTALL)
        
        for match in matches:
            movie_info = {}
            
            # info 추출 - ¡와 ¿를 [, ]로 변환
            info_match = re.search(r"'info':\s*'([^']*)'", match)
            if info_match:
                info_text = info_match.group(1)
                info_text = info_text.replace('¡', '[').replace('¿', ']')

                # 정규 표현식을 사용하여 대괄호 안의 시간 부분을 찾습니다.
                time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', info_text)

                if time_match:
                    start_time = time_match.group(1)  # 대괄호 안의 시간 부분 (예: 00:21:27)
                    name = info_text.replace(f' [{start_time}]', '').strip() # 시간 부분을 제거하고 앞뒤 공백을 제거합니다.
                else:
                    # 시간 형식이 없는 경우를 대비한 처리
                    start_time = "00:00:00"  # 기본값 설정
                    name = info_text.strip()

                movie_info['start_time'] = start_time  # 'start-time'에서 'start_time'으로 수정
                movie_info['name'] = name
            
            # source_url 추출
            source_url_match = re.search(r"'source_url':\s*'([^']*)'", match)
            if source_url_match:
                movie_info['source_url'] = source_url_match.group(1)
            
            # video-url 추출
            video_url_match = re.search(r"'video-url':\s*'([^']*)'", match)
            if video_url_match:
                movie_info['video_url'] = video_url_match.group(1)  # 'video-url'에서 'video_url'로 수정
            
            # text 추출
            text_match = re.search(r"'text':\s*'([^']*)'", match)
            if text_match:
                text_content = text_match.group(1)
                # 텍스트 내의 특수 문자도 처리
                text_content = text_content.replace('¡', '[').replace('¿', ']')
                movie_info['text'] = text_content
            
            # 필수 정보가 있는 경우만 추가
            if movie_info.get('name') and movie_info.get('text'):
                movies.append(movie_info)
    
    except Exception as e:
        print(f"정규식 추출 중 오류: {e}")
        return []
    
    return movies

def print_movies(movies):
    """
    추출된 영화 정보를 콘솔에 출력
    """
    if not movies:
        print("출력할 영화 정보가 없습니다.")
        return
    
    print(f"\n=== 총 {len(movies)}개의 영화 정보 추출 ===\n")
    
    for i, movie in enumerate(movies, 1):
        print(f"[{i}] {movie.get('name', 'N/A')}")
        print(f"    Source URL: {movie.get('source_url', 'N/A')}")
        print(f"    Video URL: {movie.get('video_url', 'N/A')}")
        print(f"    Text: {movie.get('text', 'N/A')}")
        print(f"    Start Time: {movie.get('start_time', 'N/A')}")
        print("-" * 80)

# 메인 실행 함수
def clean_data_from_playphrase(data_text):
    # 내가 원하는 정보만 추출
    movies = extract_movie_info(data_text)
    if not movies:
        print("영화 정보가 추출되지 않았습니다.")
        return []

    return movies