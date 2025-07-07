# phrase/views.py
from django.shortcuts import render
from phrase.application.get_movie_info import get_movie_info
from phrase.application.clean_data import extract_movie_info
from phrase.application.load_to_db import load_to_db
from phrase.application.translate import LibreTranslator

def index(request):
    """메인 페이지 - 텍스트 입력 폼을 보여줍니다."""
    return render(request, 'index.html')

def process_text(request):
    """텍스트 처리 - POST로 전송된 텍스트를 받아 처리합니다."""
    if request.method == 'POST':
        user_text = request.POST.get('user_text', '')

        if not user_text:
            return render(request, 'index.html', {'error': '텍스트를 입력해주세요.'})

        # 1단계: 번역기 초기화
        translator = LibreTranslator()
        
        # 2단계: 한글 인식 및 번역
        translated_text = None
        search_text = user_text  # 검색에 사용할 텍스트
        
        if translator.is_korean(user_text):
            print(f"🔍 한글 검색어 감지: '{user_text}'")
            
            # 한글을 영어로 번역
            translated_text = translator.translate_to_english(user_text)
            search_text = translated_text  # playphrase.me에는 번역된 영어로 검색
            
            print(f"🔄 한글 → 영어 번역: '{user_text}' → '{translated_text}'")
        else:
            print(f"🔍 영어 검색어: '{user_text}'")

        # 3단계: 번역된 텍스트(영어)로 playphrase.me에서 영화 정보 가져오기
        print(f"🎬 playphrase.me 검색 시작: '{search_text}'")
        playphrase_movies = get_movie_info(search_text)

        if not playphrase_movies:
            print(f"❌ playphrase.me에서 '{search_text}' 결과 없음")
            context = {
                'message': user_text,
                'translated_message': translated_text,
                'error': f'"{user_text}"에 대한 검색 결과를 찾을 수 없습니다.',
                'movies': [],
                'total_results': 0,
                'displayed_results': 0,
                'has_more_results': False,
            }
            return render(request, 'index.html', context)

        # 4단계: 내가 원하는 영화 정보만 추출
        print(f"📊 데이터 추출 중...")
        movies = extract_movie_info(playphrase_movies)

        if not movies:
            print(f"❌ 영화 정보 추출 실패")
            context = {
                'message': user_text,
                'translated_message': translated_text,
                'error': f'"{user_text}"에 대한 영화 정보를 처리할 수 없습니다.',
                'movies': [],
                'total_results': 0,
                'displayed_results': 0,
                'has_more_results': False,
            }
            return render(request, 'index.html', context)

        # 5단계: 영화 정보를 DB에 저장하고 최종 영화 정보 리스트를 반환
        print(f"💾 데이터베이스 저장 중...")
        movies = load_to_db(movies)

        # 검색 결과 통계 계산
        total_results = len(movies)
        displayed_results = min(total_results, 5)  # 최대 5개까지 표시

        print(f"✅ 검색 완료: 총 {total_results}개 결과, {displayed_results}개 표시")

        context = {
            'message': user_text,  # 사용자가 입력한 원본 (한글 또는 영어)
            'translated_message': translated_text,  # 번역된 텍스트 (한글→영어 번역 시만)
            'search_used': search_text,  # 실제 검색에 사용된 텍스트
            'movies': movies,
            'total_results': total_results,  # 전체 검색 결과 수
            'displayed_results': displayed_results,  # 실제 표시되는 결과 수
            'has_more_results': total_results > 5,  # 5개 초과 여부
        }
        return render(request, 'index.html', context)
    
    # GET 요청인 경우 메인 페이지로 리다이렉트
    return render(request, 'index.html')