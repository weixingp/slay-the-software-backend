from django.urls import path, include
from .views import *

urlpatterns= [
    path('leaderboard', LeaderboardView.as_view())
]