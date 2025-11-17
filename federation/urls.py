from django.urls import path
from . import views

urlpatterns = [
    path('entry/', views.newEntry, name='newEntry'),
]