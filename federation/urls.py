from django import path
import views

urlpatterns = [
    path('', views.inbox, name='inbox'),
]