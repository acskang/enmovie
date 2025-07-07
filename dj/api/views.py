# api/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from phrase.models import Movie, MovieQuote, UserSearchQuery, UserSearchResult
from api.serializers import MovieSerializer, MovieQuoteSerializer, MovieQuoteSearchSerializer

# phrase 앱의 함수들을 import
from phrase.application.get_movie_info import get_movie_info
from phrase.application.clean_data import extract_movie_info  
from phrase.application.load_to_db import load_to_db
from phrase.application.translate import LibreTranslator
from phrase.application.search_history import SearchHistoryManager

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class MovieListView(generics.ListAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer
    pagination_class = StandardResultsSetPagination

class MovieDetailView(generics.RetrieveAPIView):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

class MovieQuoteListView(generics.ListAPIView):
    queryset = MovieQuote.objects.select_related('movie').all()
    serializer_class = MovieQuoteSerializer
    pagination_class = StandardResultsSetPagination

@api_view(['GET'])
def search_movie_quotes(request):
    """
    Flutter 앱에서 사용할 영화 구문 검색 API (한글 번역 우선 처리)
    GET /api/search/?q=검색어&limit=5
    """
    query = request.GET.get('q', '').strip()
    
    # limit 파라미터 안전하게 처리
    try:
        limit_param = request.GET.get('limit', '5')
        limit_clean = ''.join(filter(str.isdigit, limit_param))
        limit = int(limit_clean) if limit_clean else 5
        limit = max(1, min(limit, 50))
    except (ValueError, TypeError):
        limit = 5
    
    if not query:
        return Response({
            'error': '검색어를 입력해주세요.',
            'results': [],
            'query': '',
            'count': 0
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 1단계: 번역기 초기화
        translator = LibreTranslator()
        original_query = query
        translated_query = None
        search_query = query  # 실제 검색에 사용할 쿼리
        
        # 2단계: 한글 인식 및 번역
        if translator.is_korean(query):
            print(f"🔍 [API] 한글 검색어 감지: '{query}'")
            
            # 한글을 영어로 번역
            translated_query = translator.translate_to_english(query)
            search_query = translated_query  # DB와 외부 API 검색에는 영어 사용
            
            print(f"🔄 [API] 한글 → 영어 번역: '{query}' → '{translated_query}'")
        else:
            print(f"🔍 [API] 영어 검색어: '{query}'")
        
        # 3단계: 먼저 기존 DB에서 검색 (번역된 영어로)
        print(f"🗄️ [API] DB 검색 시작: '{search_query}'")
        quotes = MovieQuote.objects.select_related('movie').filter(
            Q(text__icontains=search_query) | 
            Q(movie__name__icontains=search_query)
        ).order_by('-created_at')[:limit]
        
        # 4단계: 검색 결과가 없으면 외부 API에서 데이터 가져오기
        if not quotes.exists():
            print(f"🌐 [API] 외부 검색 시작: '{search_query}'")
            try:
                # 외부 데이터 처리 함수 호출 (번역된 영어로)
                new_movies = process_external_search(search_query)
                
                # 새로 추가된 데이터로 다시 검색
                quotes = MovieQuote.objects.select_related('movie').filter(
                    Q(text__icontains=search_query) | 
                    Q(movie__name__icontains=search_query)
                ).order_by('-created_at')[:limit]
                
                print(f"📊 [API] 외부 검색 후 DB 결과: {quotes.count()}개")
                
            except Exception as e:
                print(f"❌ [API] 외부 검색 처리 중 오류: {e}")
        
        # 5단계: 검색 기록 저장
        if 'SearchHistoryManager' in globals():
            search_history = SearchHistoryManager.save_search_query(
                original_query=original_query,
                translated_query=translated_query,
                result_count=quotes.count()
            )
            
            # 검색 결과 저장
            if quotes.exists():
                SearchHistoryManager.save_search_results(search_history, quotes)
        
        # 6단계: 응답 생성
        serializer = MovieQuoteSearchSerializer(
            quotes, 
            many=True, 
            context={'request': request}
        )
        
        response_data = {
            'query': original_query,  # 사용자가 입력한 원본
            'count': len(serializer.data),
            'limit': limit,
            'results': serializer.data
        }
        
        # 번역된 검색어가 있으면 추가
        if translated_query:
            response_data['translated_query'] = translated_query
            response_data['search_used'] = search_query
        
        # 검색 결과가 없으면 메시지 추가
        if not serializer.data:
            if translated_query:
                response_data['message'] = f'"{original_query}" (번역: "{translated_query}")에 대한 검색 결과를 찾을 수 없습니다.'
            else:
                response_data['message'] = f'"{original_query}"에 대한 검색 결과를 찾을 수 없습니다.'
        
        print(f"✅ [API] 검색 완료: {len(serializer.data)}개 결과")
        return Response(response_data)
    
    except Exception as e:
        print(f"❌ [API] 검색 중 오류: {e}")
        return Response({
            'error': f'검색 중 오류가 발생했습니다: {str(e)}',
            'results': [],
            'query': original_query,
            'count': 0
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def process_external_search(query):
    """
    외부 API (playphrase.me)에서 데이터를 가져와 DB에 저장하는 함수
    """
    try:
        # playphrase.me에서 영화 정보를 가져오기
        playphrase_data = get_movie_info(query)
        
        # API 응답이 없거나 비어있는 경우 처리
        if not playphrase_data:
            print(f"playphrase.me에서 '{query}'에 대한 데이터를 찾을 수 없습니다.")
            return []
        
        # 내가 원하는 영화 정보만 추출
        movies = extract_movie_info(playphrase_data)
        
        # 추출된 영화 정보가 없는 경우 처리
        if not movies:
            print(f"'{query}'에 대한 영화 정보를 추출할 수 없습니다.")
            return []
        
        # 영화 정보를 DB에 저장하고 최종 영화 정보 리스트를 반환
        saved_movies = load_to_db(movies)
        
        return saved_movies
        
    except Exception as e:
        print(f"외부 검색 처리 중 오류: {e}")
        raise e


@api_view(['GET'])
def get_movie_quote_detail(request, quote_id):
    """
    특정 영화 구문의 상세 정보 조회
    GET /api/quotes/{quote_id}/
    """
    try:
        # quote_id가 숫자인지 확인
        if not str(quote_id).isdigit():
            return Response(
                {'error': '잘못된 구문 ID입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        quote = MovieQuote.objects.select_related('movie').get(id=quote_id)
        serializer = MovieQuoteSearchSerializer(quote, context={'request': request})
        return Response(serializer.data)
        
    except MovieQuote.DoesNotExist:
        return Response(
            {'error': '해당 구문을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'오류가 발생했습니다: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_movie_quotes_by_movie(request, movie_id):
    """
    특정 영화의 모든 구문 조회
    GET /api/movies/{movie_id}/quotes/
    """
    try:
        # movie_id가 숫자인지 확인
        if not str(movie_id).isdigit():
            return Response(
                {'error': '잘못된 영화 ID입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        movie = Movie.objects.get(id=movie_id)
        quotes = MovieQuote.objects.filter(movie=movie).order_by('start_time')
        serializer = MovieQuoteSearchSerializer(
            quotes, 
            many=True, 
            context={'request': request}
        )
        return Response({
            'movie': movie.name,
            'movie_id': movie.id,
            'quotes_count': len(serializer.data),
            'quotes': serializer.data
        })
        
    except Movie.DoesNotExist:
        return Response(
            {'error': '해당 영화를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'오류가 발생했습니다: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_search_history(request):
    """
    검색 기록 조회 API
    GET /api/search-history/?type=recent&limit=10
    type: recent(최근), popular(인기), korean(한글)
    """
    history_type = request.GET.get('type', 'recent')
    
    try:
        limit = int(request.GET.get('limit', 10))
        limit = max(1, min(limit, 50))  # 1-50 사이로 제한
    except (ValueError, TypeError):
        limit = 10
    
    try:
        if history_type == 'popular':
            searches = SearchHistoryManager.get_popular_searches(limit)
        elif history_type == 'korean':
            searches = SearchHistoryManager.get_korean_searches(limit)
        else:
            searches = SearchHistoryManager.get_recent_searches(limit)
        
        data = []
        for search in searches:
            data.append({
                'original_query': search.original_query,
                'translated_query': search.translated_query,
                'search_count': search.search_count,
                'result_count': search.result_count,
                'has_results': search.has_results,
                'last_searched_at': search.last_searched_at.isoformat(),
            })
        
        return Response({
            'type': history_type,
            'count': len(data),
            'searches': data
        })
        
    except Exception as e:
        return Response({
            'error': f'검색 기록 조회 중 오류가 발생했습니다: {str(e)}',
            'searches': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_statistics(request):
    """
    검색 통계 API
    GET /api/statistics/
    """
    try:
        # 전체 통계
        total_searches = UserSearchQuery.objects.count()
        total_movies = Movie.objects.count()
        total_quotes = MovieQuote.objects.count()
        
        # 한글 검색 통계
        korean_searches = UserSearchQuery.objects.filter(
            original_query__regex=r'[가-힣]'
        ).count()
        
        # 인기 한글 검색어 Top 5
        popular_korean = SearchHistoryManager.get_korean_searches(5)
        popular_korean_data = [
            {
                'query': search.original_query,
                'count': search.search_count,
                'results': search.result_count
            } 
            for search in popular_korean
        ]
        
        return Response({
            'total_searches': total_searches,
            'total_movies': total_movies,
            'total_quotes': total_quotes,
            'korean_searches': korean_searches,
            'korean_percentage': round((korean_searches / total_searches * 100), 1) if total_searches > 0 else 0,
            'popular_korean_queries': popular_korean_data
        })
        
    except Exception as e:
        return Response({
            'error': f'통계 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def health_check(request):
    """
    API 상태 확인
    GET /api/health/
    """
    try:
        # 간단한 DB 연결 테스트
        movie_count = Movie.objects.count()
        quote_count = MovieQuote.objects.count()
        
        return Response({
            'status': 'healthy',
            'timestamp': request.build_absolute_uri(),
            'database': 'connected',
            'movies': movie_count,
            'quotes': quote_count,
            'translation': 'available'
        })
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)