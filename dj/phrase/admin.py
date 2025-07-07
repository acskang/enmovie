# phrase/admin.py
from django.contrib import admin
from .models import Movie, MovieQuote, UserSearchQuery, UserSearchResult

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_url', 'poster_url', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'source_url']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'source_url')
        }),
        ('포스터 정보', {
            'fields': ('poster_url', 'poster_image', 'poster_image_path'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(MovieQuote)
class MovieQuoteAdmin(admin.ModelAdmin):
    list_display = ['movie', 'text_preview', 'start_time', 'video_url', 'created_at']
    list_filter = ['created_at', 'updated_at', 'movie']
    search_fields = ['text', 'movie__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['movie']
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = '구문 미리보기'
    
    fieldsets = (
        ('영화 정보', {
            'fields': ('movie', 'start_time')
        }),
        ('구문 정보', {
            'fields': ('text',)
        }),
        ('비디오 정보', {
            'fields': ('video_url', 'video_file', 'video_file_path'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserSearchQuery)
class UserSearchQueryAdmin(admin.ModelAdmin):
    list_display = ['original_query', 'translated_query', 'search_count', 'result_count', 'has_results', 'last_searched_at']
    list_filter = ['has_results', 'created_at', 'last_searched_at']
    search_fields = ['original_query', 'translated_query']
    ordering = ['-last_searched_at']
    readonly_fields = ['created_at', 'last_searched_at']
    
    fieldsets = (
        ('검색어 정보', {
            'fields': ('original_query', 'translated_query')
        }),
        ('통계 정보', {
            'fields': ('search_count', 'result_count', 'has_results')
        }),
        ('시간 정보', {
            'fields': ('created_at', 'last_searched_at'),
            'classes': ('collapse',)
        }),
    )
    
    # 한글 검색어만 필터링하는 액션
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs
    
    actions = ['mark_as_successful', 'mark_as_failed']
    
    def mark_as_successful(self, request, queryset):
        queryset.update(has_results=True)
        self.message_user(request, f"{queryset.count()}개 검색어를 성공으로 표시했습니다.")
    mark_as_successful.short_description = "선택된 검색어를 성공으로 표시"
    
    def mark_as_failed(self, request, queryset):
        queryset.update(has_results=False)
        self.message_user(request, f"{queryset.count()}개 검색어를 실패로 표시했습니다.")
    mark_as_failed.short_description = "선택된 검색어를 실패로 표시"

@admin.register(UserSearchResult)
class UserSearchResultAdmin(admin.ModelAdmin):
    list_display = ['search_query_text', 'movie_quote_preview', 'relevance_score', 'created_at']
    list_filter = ['created_at', 'relevance_score']
    search_fields = ['search_query__original_query', 'movie_quote__text', 'movie_quote__movie__name']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    autocomplete_fields = ['search_query', 'movie_quote']
    
    def search_query_text(self, obj):
        return obj.search_query.original_query
    search_query_text.short_description = '검색어'
    
    def movie_quote_preview(self, obj):
        return f"{obj.movie_quote.movie.name}: {obj.movie_quote.text[:30]}..."
    movie_quote_preview.short_description = '영화 구문'
    
    fieldsets = (
        ('연결 정보', {
            'fields': ('search_query', 'movie_quote')
        }),
        ('관련성 정보', {
            'fields': ('relevance_score',)
        }),
        ('시간 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

# 관리자 사이트 제목 설정
admin.site.site_header = "영화 구문 검색 관리"
admin.site.site_title = "MoviePhraseSearch Admin"
admin.site.index_title = "영화 구문 검색 시스템 관리"