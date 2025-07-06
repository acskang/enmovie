from rest_framework import serializers
from phrase.models import Movie, MovieQuote

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ['id', 'name', 'source_url', 'poster_url', 'poster_image', 'poster_image_path']

class MovieQuoteSerializer(serializers.ModelSerializer):
    movie_name = serializers.CharField(source='movie.name', read_only=True)
    movie_poster_url = serializers.CharField(source='movie.poster_url', read_only=True)
    movie_poster_image = serializers.CharField(source='movie.poster_image.url', read_only=True)
    
    class Meta:
        model = MovieQuote
        fields = [
            'id', 'movie', 'movie_name', 'movie_poster_url', 'movie_poster_image',
            'start_time', 'text', 'video_url', 'video_file', 'video_file_path'
        ]

class MovieQuoteSearchSerializer(serializers.ModelSerializer):
    """Flutter 앱에서 사용할 검색 결과용 시리얼라이저"""
    name = serializers.CharField(source='movie.name', read_only=True)
    posterUrl = serializers.SerializerMethodField()
    videoUrl = serializers.SerializerMethodField()
    startTime = serializers.CharField(source='start_time', read_only=True)
    
    class Meta:
        model = MovieQuote
        fields = ['name', 'startTime', 'text', 'posterUrl', 'videoUrl']
    
    def get_posterUrl(self, obj):
        if obj.movie.poster_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.movie.poster_image.url)
        return obj.movie.poster_url
    
    def get_videoUrl(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video_file.url)
        return obj.video_url