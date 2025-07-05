import requests
import re
from bs4 import BeautifulSoup
from django.shortcuts import render
from django.http import JsonResponse
from urllib.parse import urljoin
import time
import logging
from phrase.models import MovieQuote
from django.core.files import File
from io import BytesIO

# 로깅 설정
logger = logging.getLogger(__name__)

class IMDBPosterExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_poster_url(self, imdb_url):
        """IMDB 페이지에서 포스터 이미지 URL 추출"""
        try:
            logger.info(f"IMDB 페이지 접근 중: {imdb_url}")
            response = self.session.get(imdb_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            poster_img_tag = None
            poster_url = None
            
            # 첫 번째 시도: 'ipc-image' 클래스 찾기
            poster_img_tag = soup.find('img', class_='ipc-image')
            
            # 두 번째 시도: 포스터 컨테이너 내부의 img 태그 찾기
            if not poster_img_tag:
                poster_container = soup.find('div', class_='ipc-poster__poster-image')
                if poster_container:
                    poster_img_tag = poster_container.find('img')
            
            # 세 번째 시도: 최신 IMDb 포스터 이미지 클래스
            if not poster_img_tag:
                poster_img_tag = soup.find('img', class_='sc-7c0a76a2-0')
            
            # 네 번째 시도: 다른 일반적인 포스터 선택자들
            if not poster_img_tag:
                selectors = [
                    'img[data-testid="hero-media__poster"]',
                    '.ipc-poster img',
                    '.poster img',
                    'img[alt*="poster"]',
                    'img[alt*="Poster"]',
                    '.titlereference-overview-poster-container img'
                ]
                
                for selector in selectors:
                    poster_img_tag = soup.select_one(selector)
                    if poster_img_tag:
                        break
            
            # 포스터 URL 추출
            if poster_img_tag:
                poster_url = poster_img_tag.get('src')
                if poster_url:
                    # 상대 URL을 절대 URL로 변환
                    if not poster_url.startswith('http'):
                        poster_url = urljoin(imdb_url, poster_url)
                    
                    # 고해상도 이미지 URL로 변환
                    if '@' in poster_url:
                        poster_url = poster_url.split('@')[0] + '@._V1_UX400_.jpg'
                    
                    logger.info(f"포스터 URL 찾음: {poster_url}")
                    return poster_url
            
            logger.warning("포스터 이미지 태그를 찾을 수 없습니다.")
            return None
                
        except Exception as e:
            logger.error(f"포스터 URL 추출 중 오류 발생: {str(e)}")
            return None
    
    def get_movie_title(self, soup):
        """HTML에서 영화 제목 추출"""
        try:
            title_tag = soup.find('meta', property='og:title')
            if title_tag:
                return title_tag.get('content').replace(' - IMDb', '').strip()
            return None
        except Exception:
            return None


def download_poster_image(poster_url, filename=None):
    try:
        response = requests.get(poster_url, stream=True)
        response.raise_for_status()
        
        # 이미지 파일 이름 생성
        file_name = filename
        
        # 이미지 저장
        image = BytesIO(response.content)
        return File(image, name=file_name)
    
    except requests.RequestException as e:
        print(f"파일 다운로드 중 에러 발생: {e}")
        return None



def convert_to_pep8_filename(text):
    # 1. 모든 문자를 소문자로 변환
    text = text.lower()

    # 2. 특수 문자(따옴표, 물음표 등) 제거
    text = re.sub(r"[^\w\s]", "", text)

    # 3. 공백을 밑줄(_)로 변환
    filename = text.replace(" ", "_")

    return filename


def get_poster_url(source_url):
    """영화 데이터에서 IMDB 포스터 URL을 추출하는 함수"""
    # IMDBPosterExtractor 인스턴스 생성
    extractor = IMDBPosterExtractor()
    poster_url = extractor.extract_poster_url(source_url)
    return poster_url
    
    for movie in movie_data:
        # MovieQuete 테이블에 source_url이 있으면 그 RAW에 poster_url을 가져옴
        try:
            # source_url이 이미 존재하는지 확인
            movie = MovieQuote.objects.get(source_url = movie['source-url'])
            print(f"📌 이미 존재하는 poster_url: {movie.poster_url}")
            poster_url = movie.poster_url
        except MovieQuote.DoesNotExist:
            print(f"🔍 해당 source_url에 대한 poster_url 없음, 새로 가져오는 중...")
            # 없으면 포스터를 IMDb에서 가져옴
            poster_url = extractor.extract_poster_url(movie['source-url'])

            if poster_url:
               filename = convert_to_pep8_filename(movie['name'])
               image_file = download_poster_image(poster_url, filename=filename)
               image = MovieQuote.objects.create(
                   name = filename,
                   start_time=movie['start-time'],
                   video_url=movie.get('video-url', ''),  # 비디오 URL이 없을 경우 빈 문자열
                   source_url=movie['source-url'],
                   poster_url=poster_url,
                   text=movie['text'],
               )
        
        movie_info = {
            'name': movie['name'],
            'start_time': movie['start-time'],
            'video-url': movie.get('video-url', ''),  # 비디오 URL이 없을 경우 빈 문자열
            'source-url': movie['source-url'],
            'poster_url': poster_url,
            'text': movie['text'],
        }
        
        movies_with_posters.append(movie_info)

        
        # 요청 간 딜레이 (IMBD 부하 방지)
        time.sleep(0.5)
    
    return movies_with_posters


def get_poster_ajax(request):
    """AJAX로 개별 포스터 URL을 가져오는 뷰"""
    if request.method == 'GET':
        imdb_url = request.GET.get('imdb_url')
        if not imdb_url:
            return JsonResponse({'error': 'IMDB URL이 필요합니다.'}, status=400)
        
        extractor = IMDBPosterExtractor()
        poster_url = extractor.extract_poster_url(imdb_url)
        
        return JsonResponse({
            'poster_url': poster_url,
            'success': poster_url is not None
        })
    
    return JsonResponse({'error': '잘못된 요청입니다.'}, status=400)