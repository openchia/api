from django.urls import include, path
from rest_framework import routers
from .views import (
    BlockViewSet,
    LauncherViewSet,
    StatsView,
    SpaceView,
)

router = routers.DefaultRouter()
router.register('block', BlockViewSet)
router.register('launcher', LauncherViewSet)

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('stats', StatsView.as_view()),
    path('space', SpaceView.as_view()),
]
