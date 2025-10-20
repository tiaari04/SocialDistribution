from django.urls import path
from . import views

app_name = "login"

urlpatterns = [
    path('', views.login_view, name='login'),
    path('await-approval/', views.await_approval_view, name='await_approval'),
    path('signup/', views.signup_view, name='signup'),
]
