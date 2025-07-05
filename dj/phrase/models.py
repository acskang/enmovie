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
    text = models.TextField()
    video_url = models.URLField(db_index=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_file_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.movie.name} - {self.text[:30]}..."

