from django.urls import path
from federation import views

urlpatterns = [
    path('', views.index, name='index'),
    path('entry/', views.newEntry, name='newEntry'),
]