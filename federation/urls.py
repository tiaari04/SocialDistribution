from django.urls import path
from federation import views

urlpatterns = [
    path('', views.newEntry, name='newEntry'),
    path('images/new/', views.newHostedImage, name='newHostedImage'),
]