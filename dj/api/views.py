from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from phrase.models import Movie, MovieQuote
from api.serializers import MovieSerializer, MovieQuoteSerializer, MovieQuoteSearchSerializer

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
    Flutter 앱에서 사용할 영화 구문 검색 API
    GET /api/search/?q=검색어&limit=5
    """
    query = request.GET.get('q', '').strip()
    
    # limit 파라미터 안전하게 처리
    try:
        limit_param = request.GET.get('limit', '5')
        # 숫자가 아닌 문자 제거 (예: '5~' -> '5')
        limit_clean = ''.join(filter(str.isdigit, limit_param))
        limit = int(limit_clean) if limit_clean else 5
        # 최소 1, 최대 50으로 제한
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
        # 먼저 기존 DB에서 검색
        quotes = MovieQuote.objects.select_related('movie').filter(
            Q(text__icontains=query) | 
            Q(movie__name__icontains=query)
        ).order_by('-created_at')[:limit]
        
        # 검색 결과가 없으면 외부 API에서 데이터 가져오기
        if not quotes.exists():
            try:
                # 외부 데이터 처리 함수 호출
                new_movies = process_external_search(query)
                
                # 새로 추가된 데이터로 다시 검색
                quotes = MovieQuote.objects.select_related('movie').filter(
                    Q(text__icontains=query) | 
                    Q(movie__name__icontains=query)
                ).order_by('-created_at')[:limit]
                
                # 여전히 결과가 없으면
                if not quotes.exists():
                    return Response({
                        'query': query,
                        'count': 0,
                        'limit': limit,
                        'results': [],
                        'message': f'"{query}"에 대한 검색 결과를 찾을 수 없습니다.'
                    })
                    
            except Exception as e:
                # 외부 API 호출 실패 시에도 빈 결과 반환
                return Response({
                    'query': query,
                    'count': 0,
                    'limit': limit,
                    'results': [],
                    'message': f'"{query}"에 대한 검색 결과를 찾을 수 없습니다.',
                    'external_search_error': str(e)
                })
        
        serializer = MovieQuoteSearchSerializer(
            quotes, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'query': query,
            'count': len(serializer.data),
            'limit': limit,
            'results': serializer.data
        })
    
    except Exception as e:
        return Response({
            'error': f'검색 중 오류가 발생했습니다: {str(e)}',
            'results': [],
            'query': query,
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


# 기존 함수들을 phrase 앱에서 import
from phrase.application.get_movie_info import get_movie_info
from phrase.application.clean_data import extract_movie_info  
from phrase.application.load_to_db import load_to_db

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
