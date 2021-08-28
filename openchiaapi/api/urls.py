from django.urls import include, path
from rest_framework import routers
from .views import (
    BlockViewSet,
    LauncherViewSet,
    LoginView,
    PartialViewSet,
    PayoutAddressViewSet,
    PayoutViewSet,
    StatsView,
    SpaceView,
    XCHScanStatsView,
)

router = routers.DefaultRouter()
router.register('block', BlockViewSet)
router.register('launcher', LauncherViewSet)
router.register('partial', PartialViewSet)
router.register('payout', PayoutViewSet)
router.register('payoutaddress', PayoutAddressViewSet)

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('login', LoginView.as_view()),
    path('stats', StatsView.as_view()),
    path('xchscan_stats', XCHScanStatsView.as_view()),
    path('space', SpaceView.as_view()),
]
