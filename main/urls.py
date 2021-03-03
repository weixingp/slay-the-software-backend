from django.urls import path, include
from .views import *

urlpatterns= [
    path('leaderboard/', LeaderboardView.as_view()),
    path('worlds/', WorldView.as_view()),
    path('worlds/<int:id>/', WorldView.as_view()),
]