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

def convert_to_pep8_filename(text):
    # 1. 모든 문자를 소문자로 변환
    text = text.lower()

    # 2. 특수 문자(따옴표, 물음표 등) 제거
    text = re.sub(r"[^\w\s]", "", text)

    # 3. 공백을 밑줄(_)로 변환
    filename = text.replace(" ", "_")

    return filename


def download_poster_image(poster_url, filename=None):
    try:
        response = requests.get(poster_url, stream=True)
        response.raise_for_status()
        
        # 이미지 파일 이름 생성
        file_name = f'{filename}.jpg'
        
        # 이미지 저장
        image = BytesIO(response.content)
        return File(image, name=file_name)
    
    except requests.RequestException as e:
        print(f"파일 다운로드 중 에러 발생: {e}")
        return None

def download_video_file(video_url, filename=None):
    file_name = f'{filename}.jpg'
    try:
        response = requests.get(video_url, stream=True)
        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to download video'}, status=400)
        
        video_content = ContentFile(response.content, name=file_name)
        
        return video_content
    
    except requests.RequestException as e:
        print(f"파일 다운로드 중 에러 발생: {e}")
        return None


def load_to_db(movies):
    """
    영화 데이터를 Movie 테이블에 저장합니다.
    이미 존재하는 영화는 건너뜁니다.
    """
    for movie in movies:
        if not Movie.objects.filter(source_url=movie['source_url']).exists():
            extractor = IMDBPosterExtractor()
            movie['poster_url'] = extractor.extract_poster_url(movie['source_url'])
            filename = convert_to_pep8_filename(movie['name'])
            image_file = download_poster_image(movie['poster_url'], filename=filename)
            movie_object = Movie.objects.create(
                name=movie['name'],
                source_url=movie['source_url'],
                poster_url=movie['poster_url'],
                poster_image_path=f'posters/{filename}.jpg',
                poster_image = image_file,
            )
            # movie['poster_image_path'] = movie.poster_image_path
        else:
            movie_object = Movie.objects.get(source_url=movie['source_url'])
            print(f"⏩ 이미 존재함 (SKIP): {movie_object.source_url}")

        if not MovieQuote.objects.filter(video_url=movie['video_url']).exists():
            filename = convert_to_pep8_filename(movie['text'])
            video_content = download_video_file(movie['video_url'], filename)
            quote = MovieQuote.objects.create(
                movie = movie_object,
                start_time = movie['start_time'],
                video_url = movie['video_url'],
                text = movie['text'],
                video_file = video_content,
                video_file_path = f'videos/{filename}.mp4',
            )
            # quote.video_file.save(f'{filename}.mp4', download_video_file(movie['video_url']), save=True)
            # movie['video_file_path'] = quote.video_image_path
        else:
            quote = MovieQuote.objects.get(video_url=movie['video_url'])
            print(f"⏩ 이미 존재함 (SKIP): {quote['video_url']}")
            continue

        movies.append({
            'name': movie_object.name,
            # 'source_url': movie.source_url,
            # 'poster_url': movie.poster_url,
            'poster_image': movie_object.poster_image,
            'video_file': quote.video_file,
            'start_time': quote.start_time,
            'text': quote.text,
        })
        time.sleep(1)

    return movies