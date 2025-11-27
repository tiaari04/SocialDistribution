from django.urls import path
from federation import views

urlpatterns = [
    path('', views.newEntry, name='newEntry'),
    path('images/new/', views.newHostedImage, name='newHostedImage'),
    path('like/', views.newLike, name='newLike'),
    path('comment/', views.newComment, name='newComment'),
]