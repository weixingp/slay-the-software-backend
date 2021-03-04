from django.urls import path, include
from .views import *

urlpatterns= [
    path('leaderboard/', LeaderboardView.as_view()),
    path('worlds/', WorldView.as_view()),
    path('worlds/<int:id>/', WorldDetails.as_view()),
    path('worlds/custom/', CustomWorldView.as_view()),
    path('worlds/custom/<str:access_code>/', CustomWorldDetails.as_view())
]

question_urls = [
    path('api/question/mainworld', QuestionView.as_view()).
    path('api/questions/', CreateQuestionView.as_view()),
]

urlpatterns += question_urls
