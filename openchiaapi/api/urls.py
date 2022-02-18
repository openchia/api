from django.urls import include, path, re_path
from rest_framework import routers
from .views import (
    BlockViewSet,
    LauncherSizeView,
    LauncherViewSet,
    LoginView,
    LoginQRView,
    LoggedInView,
    PartialViewSet,
    PayoutAddressViewSet,
    PayoutTransactionViewSet,
    PayoutViewSet,
    PoolSizeView,
    QRCodeView,
    StatsView,
    SpaceView,
    TransactionViewSet,
    XCHScanStatsView,
)
from giveaway.views import ClosestTicketView, GiveawayViewSet, TicketsViewSet
from referral.views import ReferralViewSet

router = routers.DefaultRouter()
router.register('block', BlockViewSet)
router.register('launcher', LauncherViewSet)
router.register('partial', PartialViewSet)
router.register('payout', PayoutViewSet)
router.register('payoutaddress', PayoutAddressViewSet)
router.register('transaction', TransactionViewSet)

router.register('giveaway/round', GiveawayViewSet)
router.register('giveaway/tickets', TicketsViewSet)
router.register('referral', ReferralViewSet)

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('giveaway/closest', ClosestTicketView.as_view()),
    re_path(r'launcher_size/?', LauncherSizeView.as_view()),
    re_path(r'pool_size/?', PoolSizeView.as_view()),
    path('login', LoginView.as_view()),
    path('login_qr', LoginQRView.as_view()),
    re_path(r'payouttransaction/?', PayoutTransactionViewSet.as_view()),
    path('qrcode', QRCodeView.as_view()),
    path('loggedin', LoggedInView.as_view()),
    path('stats', StatsView.as_view()),
    path('xchscan_stats', XCHScanStatsView.as_view()),
    path('space', SpaceView.as_view()),
]
