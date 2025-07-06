from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    # 기본 CRUD API
    path('movies/', views.MovieListView.as_view(), name='movie-list'),
    path('movies/<int:pk>/', views.MovieDetailView.as_view(), name='movie-detail'),
    path('quotes/', views.MovieQuoteListView.as_view(), name='quote-list'),
    
    # Flutter 앱용 검색 API
    path('search/', views.search_movie_quotes, name='search-quotes'),
    path('quotes/<int:quote_id>/', views.get_movie_quote_detail, name='quote-detail'),
    path('movies/<int:movie_id>/quotes/', views.get_movie_quotes_by_movie, name='movie-quotes'),
]