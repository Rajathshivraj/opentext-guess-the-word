from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('game/new/', views.new_game, name='new_game'),
    path('game/<int:pk>/', views.game_view, name='game_view'),
    path('reports/daily/', views.daily_report, name='daily_report'),
    path('reports/user/', views.user_report, name='user_report'),
]
