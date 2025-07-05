from django.urls import path
from . import views

app_name = 'phrase'

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_text, name='process_text'),
]