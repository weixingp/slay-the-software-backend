from django.urls import path, include
from .views import *

urlpatterns= [
    path('api/leaderboard/', LeaderboardView.as_view()),
    path('api/worlds/', WorldView.as_view()),
    path('api/worlds/<int:id>/', WorldDetails.as_view()),
    path('api/worlds/custom/', CustomWorldView.as_view()),
    path('api/worlds/custom/<str:access_code>/', CustomWorldDetails.as_view())
]

question_urls = [
    path('api/questions/world/', QuestionView.as_view()),
    path('api/questions/world/check/', CheckAnswerView.as_view()),
    path('api/questions/', CustomQuestionView.as_view()),
    path('api/questions/<int:pk>/', CustomQuestionListView.as_view()),
    # path('api/questions/answers/<int:id>/', EditAnswerView.as_view()),
]

misc_urls = [
    path('api/score/', UserScore.as_view()),
    path('api/difficulty/', QuestionDifficulty.as_view())
]

position_urls = [
    path('api/position/', GetPositionView.as_view())
]
urlpatterns += position_urls
urlpatterns += question_urls
urlpatterns += misc_urls
