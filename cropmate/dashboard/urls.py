from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('weather/', views.weather_view, name='weather'),
    path('sensors/', views.sensors_view, name='sensors'),
    path('agronomist/', views.agronomist_view, name='agronomist'),
    path('ask-agronomist/', views.ask_agronomist, name='ask_agronomist'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
]