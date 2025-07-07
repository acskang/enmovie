# phrase/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class Movie(models.Model):
    name = models.CharField(max_length=255)  # 영화 제목
    source_url = models.URLField(max_length=500, db_index=True)  # IMDb 링크
    poster_url = models.URLField(max_length=500, blank=True, null=True)  # 포스터 이미지 URL
    poster_image = models.ImageField(upload_to='posters/', blank=True, null=True)  # 포스터 이미지 파일
    poster_image_path = models.CharField(max_length=500, blank=True)  # 포스터 이미지 파일 경로
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 일자
    updated_at = models.DateTimeField(auto_now=True)  # 수정 일자

    def __str__(self):
        return self.name
    
class MovieQuote(models.Model):
    movie = models.ForeignKey(Movie, related_name='quotes', on_delete=models.CASCADE)  # Movie 테이블과의 1:N 관계 설정
    start_time = models.CharField(max_length=20)
    text = models.TextField()  # 영어 구문
    video_url = models.URLField(db_index=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.movie.name} - {self.text[:30]}..."


class UserSearchQuery(models.Model):
    """사용자가 입력한 검색어를 저장하는 테이블"""
    original_query = models.CharField(max_length=500, db_index=True)  # 사용자가 입력한 원본 검색어 (한글 포함)
    translated_query = models.CharField(max_length=500, blank=True, null=True)  # 번역된 검색어 (영어)
    search_count = models.IntegerField(default=1)  # 검색 횟수
    last_searched_at = models.DateTimeField(auto_now=True)  # 마지막 검색 시간
    created_at = models.DateTimeField(auto_now_add=True)  # 최초 생성 시간
    
    # 검색 결과 관련 정보
    result_count = models.IntegerField(default=0)  # 검색 결과 개수
    has_results = models.BooleanField(default=False)  # 검색 결과가 있는지 여부

    class Meta:
        ordering = ['-last_searched_at']
        indexes = [
            models.Index(fields=['original_query']),
            models.Index(fields=['translated_query']),
            models.Index(fields=['-last_searched_at']),
        ]

    def __str__(self):
        if self.translated_query and self.translated_query != self.original_query:
            return f"{self.original_query} → {self.translated_query} ({self.search_count}회)"
        return f"{self.original_query} ({self.search_count}회)"


class UserSearchResult(models.Model):
    """사용자 검색어와 검색된 영화 구문을 연결하는 테이블"""
    search_query = models.ForeignKey(UserSearchQuery, related_name='results', on_delete=models.CASCADE)
    movie_quote = models.ForeignKey(MovieQuote, related_name='search_results', on_delete=models.CASCADE)
    relevance_score = models.FloatField(default=1.0)  # 검색 결과의 관련성 점수
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['search_query', 'movie_quote']
        ordering = ['-relevance_score', '-created_at']

    def __str__(self):
        return f"{self.search_query.original_query} → {self.movie_quote.movie.name}"