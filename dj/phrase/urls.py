from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'phrase'

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_text, name='process_text'),
]