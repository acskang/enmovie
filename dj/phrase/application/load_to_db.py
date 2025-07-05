import re
from phrase.models import Movie, MovieQuote
import requests
from io import BytesIO
from django.core.files import File
from phrase.application.get_imdb_poster_url import IMDBPosterExtractor
from django.core.files.base import ContentFile
from django.http import JsonResponse
import os
import time
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

def convert_to_pep8_filename(text):
    # 1. 모든 문자를 소문자로 변환
    text = text.lower()
    # 2. 특수 문자(따옴표, 물음표 등) 제거
    text = re.sub(r"[^\w\s]", "", text)
    # 3. 공백을 밑줄(_)로 변환
    filename = text.replace(" ", "_")
    return filename

def download_poster_image(poster_url, filename=None, max_retries=3):
    """
    포스터 이미지 다운로드 함수
    에러 발생 시 재시도 로직 포함
    """
    if not poster_url:
        logger.warning(f"포스터 URL이 없습니다: {filename}")
        return None
    
    for attempt in range(max_retries):
        try:
            response = requests.get(poster_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 이미지 파일 이름 생성
            file_name = f'{filename}.jpg'
            
            # 이미지 저장
            image = BytesIO(response.content)
            return File(image, name=file_name)
        
        except requests.RequestException as e:
            logger.warning(f"포스터 다운로드 시도 {attempt + 1}/{max_retries} 실패: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 지수 백오프
            else:
                logger.error(f"포스터 다운로드 최종 실패 - URL: {poster_url}, 파일명: {filename}")
                return None
        except Exception as e:
            logger.error(f"포스터 다운로드 중 예상치 못한 에러: {e}")
            return None

def download_video_file(video_url, filename=None, max_retries=3):
    """
    비디오 파일 다운로드 함수
    에러 발생 시 재시도 로직 포함
    """
    if not video_url:
        logger.warning(f"비디오 URL이 없습니다: {filename}")
        return None
    
    file_name = f'{filename}.mp4'  # 비디오 파일이므로 .mp4로 수정
    
    for attempt in range(max_retries):
        try:
            response = requests.get(video_url, stream=True, timeout=60)
            if response.status_code != 200:
                logger.warning(f"비디오 다운로드 HTTP 에러: {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return None
            
            video_content = ContentFile(response.content, name=file_name)
            return video_content
        
        except requests.RequestException as e:
            logger.warning(f"비디오 다운로드 시도 {attempt + 1}/{max_retries} 실패: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"비디오 다운로드 최종 실패 - URL: {video_url}, 파일명: {filename}")
                return None
        except Exception as e:
            logger.error(f"비디오 다운로드 중 예상치 못한 에러: {e}")
            return None

def load_to_db(movies):
    """
    영화 데이터를 Movie 테이블에 저장합니다.
    이미 존재하는 영화는 건너뜁니다.
    파일 다운로드 실패 시에도 계속 진행합니다.
    """
    processed_movies = []
    
    for movie in movies:
        movie_object = None
        
        # Movie 객체 생성 또는 가져오기
        try:
            if not Movie.objects.filter(source_url=movie['source_url']).exists():
                extractor = IMDBPosterExtractor()
                movie['poster_url'] = extractor.extract_poster_url(movie['source_url'])
                filename = convert_to_pep8_filename(movie['name'])
                
                # 포스터 이미지 다운로드 시도
                image_file = download_poster_image(movie['poster_url'], filename=filename)
                
                # Movie 객체 생성 (이미지 다운로드 실패해도 계속 진행)
                movie_create_kwargs = {
                    'name': movie['name'],
                    'source_url': movie['source_url'],
                    'poster_url': movie['poster_url'],
                    'poster_image_path': f'posters/{filename}.jpg',
                }
                
                # 이미지 파일이 성공적으로 다운로드된 경우에만 추가
                if image_file:
                    movie_create_kwargs['poster_image'] = image_file
                    logger.info(f"✅ 포스터 이미지 다운로드 성공: {movie['name']}")
                else:
                    logger.warning(f"⚠️ 포스터 이미지 다운로드 실패하여 건너뜀: {movie['name']}")
                
                movie_object = Movie.objects.create(**movie_create_kwargs)
                
            else:
                movie_object = Movie.objects.get(source_url=movie['source_url'])
                logger.info(f"⏩ 영화 이미 존재함 (SKIP): {movie_object.source_url}")
                
        except Exception as e:
            logger.error(f"❌ Movie 객체 생성/조회 실패: {movie['name']} - {e}")
            continue
        
        # MovieQuote 객체 생성 또는 가져오기
        try:
            if not MovieQuote.objects.filter(video_url=movie['video_url']).exists():
                filename = convert_to_pep8_filename(movie['text'])
                
                # 비디오 파일 다운로드 시도
                video_content = download_video_file(movie['video_url'], filename)
                
                # MovieQuote 객체 생성 (비디오 다운로드 실패해도 계속 진행)
                quote_create_kwargs = {
                    'movie': movie_object,
                    'start_time': movie['start_time'],
                    'video_url': movie['video_url'],
                    'text': movie['text'],
                    'video_file_path': f'videos/{filename}.mp4',
                }
                
                # 비디오 파일이 성공적으로 다운로드된 경우에만 추가
                if video_content:
                    quote_create_kwargs['video_file'] = video_content
                    logger.info(f"✅ 비디오 파일 다운로드 성공: {movie['text'][:50]}...")
                else:
                    logger.warning(f"⚠️ 비디오 파일 다운로드 실패하여 건너뜀: {movie['text'][:50]}...")
                
                quote = MovieQuote.objects.create(**quote_create_kwargs)
                
            else:
                quote = MovieQuote.objects.get(video_url=movie['video_url'])
                logger.info(f"⏩ 명언 이미 존재함 (SKIP): {movie['video_url']}")
                
        except Exception as e:
            logger.error(f"❌ MovieQuote 객체 생성/조회 실패: {movie['text'][:50]}... - {e}")
            # MovieQuote 생성 실패해도 계속 진행
            quote = None
        
        # 처리된 영화 데이터 추가 (파일 다운로드 실패해도 기본 정보는 포함)
        if movie_object:
            processed_movie_data = {
                'name': movie_object.name,
                'poster_image': getattr(movie_object, 'poster_image', None),
                'start_time': movie.get('start_time', ''),
                'text': movie.get('text', ''),
            }
            
            if quote:
                processed_movie_data.update({
                    'video_file': getattr(quote, 'video_file', None),
                })
            
            processed_movies.append(processed_movie_data)
            logger.info(f"✅ 처리 완료: {movie_object.name}")
        
        # 요청 간 간격 유지
        time.sleep(0.3)
    
    logger.info(f"📊 총 처리 완료: {len(processed_movies)}개 영화")
    return processed_movies