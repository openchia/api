from django.urls import include, path
from rest_framework import routers
from .views import (
    BlockViewSet,
    LauncherViewSet,
    LoginView,
    LoggedInView,
    PartialViewSet,
    PayoutAddressViewSet,
    PayoutViewSet,
    StatsView,
    SpaceView,
    XCHScanStatsView,
)
from referral.views import ReferralViewSet

router = routers.DefaultRouter()
router.register('block', BlockViewSet)
router.register('launcher', LauncherViewSet)
router.register('partial', PartialViewSet)
router.register('payout', PayoutViewSet)
router.register('payoutaddress', PayoutAddressViewSet)
router.register('referral', ReferralViewSet)

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('login', LoginView.as_view()),
    path('loggedin', LoggedInView.as_view()),
    path('stats', StatsView.as_view()),
    path('xchscan_stats', XCHScanStatsView.as_view()),
    path('space', SpaceView.as_view()),
]
