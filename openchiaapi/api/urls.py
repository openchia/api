from django.urls import include, path
from rest_framework import routers
from .views import (
    BlockViewSet,
    LauncherViewSet,
    LoginView,
    PartialViewSet,
    PayoutViewSet,
    StatsView,
    SpaceView,
)

router = routers.DefaultRouter()
router.register('block', BlockViewSet)
router.register('launcher', LauncherViewSet)
router.register('partial', PartialViewSet)
router.register('payout', PayoutViewSet)

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('login', LoginView.as_view()),
    path('stats', StatsView.as_view()),
    path('space', SpaceView.as_view()),
]
