from django.shortcuts import render
from phrase.application.get_movie_info import get_movie_info
# from phrase.application.get_imdb_poster_url import get_poster_urls
from phrase.application.common import convert_keys_for_template
from phrase.application.load_to_db import load_to_db
from phrase.application.clean_data import extract_movie_info


def index(request):
    """메인 페이지 - 텍스트 입력 폼을 보여줍니다."""
    return render(request, 'index.html')

def process_text(request):
    """텍스트 처리 - POST로 전송된 텍스트를 받아 처리합니다."""
    if request.method == 'POST':
        user_text = request.POST.get('user_text', '')

        if not user_text:
            return render(request, 'index.html', {'error': '텍스트를 입력해주세요.'})

        # 입력된 텍스트로 playphrase.me에서 영화 정보를 가져오기
        playphrase_movies = get_movie_info(user_text)

        # 내가 원하는 영화 정보만 추출
        movies = extract_movie_info(playphrase_movies)

        # 영화 정보를 DB에 저장하고 최종 영화 정보 리스트를 반환
        movies = load_to_db(movies)

        context = {
            'message': user_text,
            'movies': movies,  # 영화 정보 추가
        }
        return render(request, 'index.html', context)
    
    # GET 요청인 경우 메인 페이지로 리다이렉트
    return render(request, 'index.html')