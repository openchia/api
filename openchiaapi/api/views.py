import hashlib
import io
import logging
import os
import time
import qrcode
import qrcode.image.svg
import textwrap

from blspy import AugSchemeMPL, G1Element, G2Element
from chia.pools.pool_wallet_info import PoolState
from chia.protocols.pool_protocol import validate_authentication_token, AuthenticationPayload
from chia.util.bech32m import decode_puzzle_hash
from chia.util.byte_types import hexstr_to_bytes
from chia.util.hash import std_hash
from chia.util.ints import uint64
from datetime import datetime
from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, F, Sum, Q
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, mixins, serializers, viewsets
from rest_framework.exceptions import NotAuthenticated, NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response

from .models import (
    Block, GlobalInfo, Launcher, Partial, Payout, PayoutAddress,
    Notification,
    Transaction,
)
from .serializers import (
    BlockSerializer,
    LauncherSerializer,
    LauncherUpdateSerializer,
    LoginSerializer,
    LoginQRSerializer,
    PartialSerializer,
    PayoutSerializer,
    PayoutAddressSerializer,
    PayoutTransactionSerializer,
    StatsSerializer,
    TimeseriesSerializer,
    TransactionSerializer,
    XCHScanStatsSerializer,
)
from .utils import (
    days_to_every,
    get_influxdb_client,
    get_pool_info,
    get_pool_target_address,
    estimated_time_to_win,
)
from referral.utils import update_referral


logger = logging.getLogger('api.views')
POOL_TARGET_ADDRESS = get_pool_target_address()


class BlockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    filterset_fields = ['farmed_by', 'payout']
    ordering_fields = ['confirmed_block_index', 'farmed_height', 'payout']
    ordering = ['-farmed_height']


class LauncherFilter(django_filters.FilterSet):
    points__gt = django_filters.NumberFilter(field_name='points', lookup_expr='gt')
    points_pplns__gt = django_filters.NumberFilter(field_name='points_pplns', lookup_expr='gt')
    share_pplns__gt = django_filters.NumberFilter(field_name='share_pplns', lookup_expr='gt')

    class Meta:
        model = Launcher
        fields = [
            'points', 'points_pplns', 'share_pplns', 'is_pool_member', 'name', 'launcher_id',
            'difficulty',
        ]


class LauncherViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Launcher.objects.all()
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = LauncherFilter
    filterset_fields = ['difficulty', 'launcher_id', 'name', 'is_pool_member', 'points_pplns']
    search_fields = ['launcher_id', 'name']
    ordering_fields = ['points', 'points_pplns', 'difficulty']
    ordering = ['-points']

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'PUT':
            return LauncherUpdateSerializer
        return LauncherSerializer

    def update(self, request, pk):
        launcher_id = request.session.get('launcher_id')
        if not launcher_id and request.auth:
            launcher_id = request.auth.launcher_id

        if not launcher_id or launcher_id != pk:
            raise NotAuthenticated()
        launcher = Launcher.objects.filter(launcher_id=pk)
        if not launcher.exists():
            raise NotFound()
        launcher = launcher[0]
        s = LauncherUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        for i in (
            'name', 'email', 'notify_missing_partials_hours', 'push_missing_partials_hours',
            'push_block_farmed', 'fcm_token', 'minimum_payout', 'custom_difficulty',
        ):
            if i in s.validated_data:
                setattr(launcher, i, s.validated_data[i])

        try:
            notification = launcher.notification
        except ObjectDoesNotExist:
            notification = Notification(launcher=launcher)

        notification_changed = False
        for i in (
            'size_drop', 'size_drop_interval', 'size_drop_percent',
            'failed_partials', 'failed_partials_percent', 'payment',
        ):
            if i in s.validated_data:
                value = s.validated_data[i]
                if value is not None and i in ('payment', 'size_drop'):
                    value = list(value)
                setattr(notification, i, value)
                notification_changed = True

        try:
            update_referral(launcher, s.validated_data.get('referrer') or None)
        except ValueError as e:
            raise serializers.ValidationError({'referrer': str(e)})

        launcher.save()
        if notification_changed:
            notification.save()
        return Response(s.validated_data)


class StatsView(APIView):

    @swagger_auto_schema(responses={200: StatsSerializer(many=False)})
    def get(self, request, format=None):
        block = Block.objects.order_by('-confirmed_block_index')
        farmers = Launcher.objects.filter(is_pool_member=True)
        farmers_total = farmers.count()
        farmers_active = farmers.filter(points_pplns__gt=0).count()
        pool_info = get_pool_info()

        client = get_influxdb_client()
        query_api = client.query_api()

        try:
            q = query_api.query(
                textwrap.dedent('''from(bucket: "openchia")
                  |> range(start: duration(v: "-60m"))
                  |> filter(fn: (r) => r["_measurement"] == "pool_size")
                  |> filter(fn: (r) => r["_field"] == "global")
                  |> last()'''),
            )
            size = int(q[0].records[0]['_value'])
        except Exception:
            logger.error('Failed to get pool size', exc_info=True)
            size = 0

        globalinfo = GlobalInfo.load()
        minutes_to_win = estimated_time_to_win(
            size, int(globalinfo.blockchain_space), globalinfo.blockchain_avg_block_time,
        )
        if block.exists():
            time_since_last_win = int(time.time() - block[0].timestamp)
        else:
            time_since_last_win = None

        profitability = 0
        days30 = 30 * 24 * 60 * 60
        for b in block.filter(timestamp__gte=time.time() - days30):
            if b.pool_space > 0:
                profitability += (b.amount / 1000000000000) / (b.pool_space / 1099511627776)
        profitability /= 30

        try:
            q = query_api.query(
                textwrap.dedent('''from(bucket: "openchia")
                  |> range(start: duration(v: "-60m"))
                  |> filter(fn: (r) => r["_measurement"] == "mempool")
                  |> filter(fn: (r) => r["_field"] == "full_pct")
                  |> last()'''),
            )
            mempool_full_pct = int(q[0].records[0]['_value'])
            blockchain_duststorm = mempool_full_pct > 90
        except Exception:
            logger.error('Failed to get mempool', exc_info=True)
            mempool_full_pct = 0
            blockchain_duststorm = False

        pi = StatsSerializer(data={
            'fee': Decimal(pool_info['fee']),
            'farmers': farmers_total,
            'farmers_active': farmers_active,
            'rewards_amount': block.aggregate(total=Sum('amount'))['total'],
            'rewards_blocks': block.count(),
            'pool_space': size,
            'estimate_win': minutes_to_win,
            'time_since_last_win': time_since_last_win,
            'blockchain_height': globalinfo.blockchain_height,
            'blockchain_space': int(globalinfo.blockchain_space),
            'blockchain_duststorm': blockchain_duststorm,
            'blockchain_mempool_full_pct': mempool_full_pct,
            'reward_system': 'PPLNS',
            'last_rewards': [{
                'date': datetime.utcfromtimestamp(i.timestamp),
                'height': i.confirmed_block_index,
            } for i in block[:10]],
            'xch_current_price': globalinfo.xch_current_price,
            'pool_wallets': globalinfo.wallets,
            'average_effort': block.filter(
                ~Q(luck=-1), timestamp__gte=time.time() - days30
            ).aggregate(total=Avg('luck'))['total'],
            'xch_tb_month': profitability,
        })
        pi.is_valid()
        return Response(pi.data)


class XCHScanStatsView(APIView):

    @swagger_auto_schema(responses={200: XCHScanStatsSerializer(many=False)})
    def get(self, request, format=None):
        block = Block.objects.order_by('-confirmed_block_index')
        farmers = Launcher.objects.filter(is_pool_member=True).count()
        pool_info = get_pool_info()

        client = get_influxdb_client()
        query_api = client.query_api()

        try:
            q = query_api.query(
                textwrap.dedent('''from(bucket: "openchia")
                  |> range(start: duration(v: "-60m"))
                  |> filter(fn: (r) => r["_measurement"] == "pool_size")
                  |> filter(fn: (r) => r["_field"] == "global")
                  |> last()'''),
            )
            size = int(q[0].records[0]['_value'])
        except Exception:
            logger.error('Failed to get pool size', exc_info=True)
            size = 0

        pi = XCHScanStatsSerializer(data={
            'poolInfo': {
                'puzzle_hash': '0x' + decode_puzzle_hash(POOL_TARGET_ADDRESS).hex(),
                'fee': Decimal(pool_info['fee']) * 100,
                'minPay': 0,
            },
            'farmers': farmers,
            'capacityBytes': size,
            'farmedBlocks': [{
                'time': i.timestamp,
                'height': i.confirmed_block_index,
            } for i in block[:10]],
        })
        pi.is_valid()
        return Response(pi.data)


class PartialFilter(django_filters.FilterSet):
    min_timestamp = django_filters.NumberFilter(field_name='timestamp', lookup_expr='gte')

    class Meta:
        model = Partial
        fields = ['launcher', 'timestamp']


class LoginView(APIView):
    """
    Login using parameters from chia plotnft.
    """

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        launcher_id = hexstr_to_bytes(s.validated_data["launcher_id"])
        authentication_token = uint64(s.validated_data["authentication_token"])

        # TODO: investigate
        if 'testnet' in os.environ.get('CHIA_NETWORK', ''):
            token_timeout = 10
        else:
            token_timeout = 5

        if not validate_authentication_token(authentication_token, token_timeout):
            raise NotAuthenticated(detail='Invalid authentication_token')

        launcher = Launcher.objects.filter(launcher_id=s.validated_data["launcher_id"])
        if not launcher.exists():
            raise NotFound()
        launcher = launcher[0]

        signature = G2Element.from_bytes(hexstr_to_bytes(s.validated_data["signature"]))
        message = std_hash(
            AuthenticationPayload(
                "get_login",
                launcher_id,
                PoolState.from_bytes(launcher.singleton_tip_state).target_puzzle_hash,
                authentication_token,
            )
        )
        if not AugSchemeMPL.verify(
            G1Element.from_bytes(bytes.fromhex(launcher.authentication_public_key)),
            message,
            signature
        ):
            raise NotAuthenticated(
                detail=f"Failed to verify signature {signature} for launcher_id {launcher_id.hex()}."
            )
        request.session['launcher_id'] = s.validated_data['launcher_id']
        if not launcher.qrcode_token:
            m = hashlib.sha256()
            for v in s.validated_data.values():
                m.update(str(v).encode())
            launcher.qrcode_token = m.hexdigest()
            launcher.save()
        return Response(True)


class LoginQRView(APIView):
    """
    Login using QR Code token
    """

    @swagger_auto_schema(request_body=LoginQRSerializer)
    def post(self, request):
        s = LoginQRSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        launcher = Launcher.objects.filter(qrcode_token=s.validated_data["token"])
        if not launcher.exists():
            raise NotAuthenticated(detail='Invalid token')
        launcher = launcher[0]

        request.session['launcher_id'] = launcher.launcher_id
        return Response({
            'launcher_id': launcher.launcher_id,
            'name': launcher.name,
        })


class SVGRenderer(BaseRenderer):
    media_type = 'image/svg+xml'
    format = 'svg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class QRCodeView(APIView):
    """
    QR Code for the farmer.
    """

    renderer_classes = [SVGRenderer]

    def get(self, request):
        launcher_id = request.session.get('launcher_id')
        if not launcher_id:
            raise NotAuthenticated(detail='Not authenticated')

        launcher = Launcher.objects.filter(launcher_id=launcher_id)
        if not launcher:
            raise NotAuthenticated(detail='Not authenticated')
        launcher = launcher[0]

        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(
            launcher.qrcode_token,
            image_factory=factory,
        )
        stream = io.BytesIO()
        img.save(stream)
        img = stream.getvalue()
        stream.close()
        return Response(img, content_type='image/svg+xml')


class LoggedInView(APIView):
    """
    Get the logged in launcher id.
    """

    @swagger_auto_schema(response_body=LoginSerializer)
    def get(self, request):
        return Response({
            'launcher_id': request.session.get('launcher_id'),
        })


class PartialViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Partial.objects.all()
    serializer_class = PartialSerializer
    filterset_fields = ['launcher', 'timestamp', 'min_timestamp']
    filterset_class = PartialFilter
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']


class PayoutViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    ordering_fields = ['datetime']
    ordering = ['-datetime']


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class PayoutAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PayoutAddress.objects.all()
    serializer_class = PayoutAddressSerializer
    filterset_fields = ['payout', 'puzzle_hash', 'launcher']
    ordering_fields = ['payout', 'launcher', 'confirmed_block_index', 'amount']
    ordering = ['-payout', '-amount']


class PayoutTransactionViewSet(APIView):
    launcher = openapi.Parameter(
        'launcher',
        openapi.IN_QUERY,
        type=openapi.TYPE_STRING,
    )

    @swagger_auto_schema(
        manual_parameters=[launcher],
        responses={200: PayoutTransactionSerializer(many=True)}
    )
    def get(self, request, format=None):
        paginator = LimitOffsetPagination()
        launcher = request.GET.get('launcher')
        payouts = PayoutAddress.objects.values(
            'launcher',
            confirmed_block_index=F('transaction__confirmed_block_index'),
            created_at_time=F('transaction__created_at_time'),
            transaction_name=F('transaction__transaction'),
            xch_price=F('transaction__xch_price'),
        ).order_by('-transaction', 'launcher').annotate(amount=Sum('amount'))
        if launcher:
            payouts = payouts.filter(launcher=launcher)
        result_page = paginator.paginate_queryset(payouts, request)
        serializer = PayoutTransactionSerializer(result_page, many=True, context={
            'request': request,
        })
        return paginator.get_paginated_response(serializer.data)


class LauncherSizeView(APIView):

    days_param = openapi.Parameter(
        'days',
        openapi.IN_QUERY,
        description='Number of days (default: 7)',
        type=openapi.TYPE_INTEGER,
    )

    launcher = openapi.Parameter(
        'launcher',
        openapi.IN_QUERY,
        description='Launcher ID',
        type=openapi.TYPE_STRING,
    )

    @swagger_auto_schema(
        manual_parameters=[days_param, launcher],
        responses={200: TimeseriesSerializer(many=True)},
    )
    def get(self, request, format=None):
        client = get_influxdb_client()
        query_api = client.query_api()

        days = self.request.query_params.get('days', 7)
        every = days_to_every(int(days))

        q = query_api.query(
            textwrap.dedent('''from(bucket: "openchia")
              |> range(start: duration(v: _days), stop: now())
              |> filter(fn: (r) => r["_measurement"] == "launcher_size")
              |> filter(fn: (r) => r["launcher"] == _launcher)
              |> aggregateWindow(every: duration(v: _every), fn: mean, createEmpty: false)
              |> yield(name: "mean")'''),
            params={
                '_days': f"-{days}d",
                '_launcher': self.request.query_params['launcher'],
                '_every': every,
            },
        )

        result = []
        for table in q:
            for r in table.records:
                result.append({
                    'datetime': r['_time'],
                    'field': r['_field'],
                    'value': r['_value'],
                })

        return Response(result)


class PoolSizeView(APIView):

    days_param = openapi.Parameter(
        'days',
        openapi.IN_QUERY,
        description='Number of days (default: 7)',
        type=openapi.TYPE_INTEGER,
    )

    @swagger_auto_schema(
        manual_parameters=[days_param],
        responses={200: TimeseriesSerializer(many=True)},
    )
    def get(self, request, format=None):
        client = get_influxdb_client()
        query_api = client.query_api()

        days = self.request.query_params.get('days', 7)
        every = days_to_every(int(days))

        q = query_api.query(
            textwrap.dedent('''from(bucket: "openchia")
              |> range(start: duration(v: _days), stop: now())
              |> filter(fn: (r) => r["_measurement"] == "pool_size")
              |> aggregateWindow(every: duration(v: _every), fn: mean, createEmpty: false)
              |> yield(name: "mean")'''),
            params={
                '_days': f"-{days}d",
                '_every': every,
            },
        )

        result = []
        for table in q:
            for r in table.records:
                result.append({
                    'datetime': r['_time'],
                    'field': r['_field'],
                    'value': r['_value'],
                })

        return Response(result)


class NetspaceView(APIView):

    days_param = openapi.Parameter(
        'days',
        openapi.IN_QUERY,
        description='Number of days (default: 7)',
        type=openapi.TYPE_INTEGER,
    )

    @swagger_auto_schema(
        manual_parameters=[days_param],
        responses={200: TimeseriesSerializer(many=True)},
    )
    def get(self, request, format=None):
        client = get_influxdb_client()
        query_api = client.query_api()

        days = self.request.query_params.get('days', 7)
        every = days_to_every(int(days))

        q = query_api.query(
            textwrap.dedent('''from(bucket: "openchia")
              |> range(start: duration(v: _days), stop: now())
              |> filter(fn: (r) => r["_measurement"] == "netspace")
              |> aggregateWindow(every: duration(v: _every), fn: mean, createEmpty: false)
              |> yield(name: "mean")'''),
            params={
                '_days': f"-{days}d",
                '_every': every,
            },
        )

        result = []
        for table in q:
            for r in table.records:
                result.append({
                    'datetime': r['_time'],
                    'field': r['_field'],
                    'value': r['_value'],
                })

        return Response(result)


class XCHPriceView(APIView):

    days_param = openapi.Parameter(
        'days',
        openapi.IN_QUERY,
        description='Number of days (default: 7)',
        type=openapi.TYPE_INTEGER,
    )

    @swagger_auto_schema(
        manual_parameters=[days_param],
        responses={200: TimeseriesSerializer(many=True)},
    )
    def get(self, request, format=None):
        client = get_influxdb_client()
        query_api = client.query_api()

        days = self.request.query_params.get('days', 7)
        every = days_to_every(int(days))

        q = query_api.query(
            textwrap.dedent('''from(bucket: "openchia")
              |> range(start: duration(v: _days), stop: now())
              |> filter(fn: (r) => r["_measurement"] == "xchprice")
              |> filter(fn: (r) => contains(value: r["_field"], set: ["btc", "eth"]) == false)
              |> aggregateWindow(every: duration(v: _every), fn: mean, createEmpty: false)
              |> yield(name: "mean")'''),
            params={
                '_days': f"-{days}d",
                '_every': every,
            },
        )

        result = []
        for table in q:
            for r in table.records:
                result.append({
                    'datetime': r['_time'],
                    'field': r['_field'],
                    'value': r['_value'],
                })

        return Response(result)


class PartialView(APIView):

    launcher = openapi.Parameter(
        'launcher',
        openapi.IN_QUERY,
        description='Launcher ID',
        type=openapi.TYPE_STRING,
    )
    days_param = openapi.Parameter(
        'days',
        openapi.IN_QUERY,
        description='Number of days (default: 7)',
        type=openapi.TYPE_INTEGER,
    )

    @swagger_auto_schema(
        manual_parameters=[days_param, launcher],
        responses={200: TimeseriesSerializer(many=True)},
    )
    def get(self, request, format=None):
        client = get_influxdb_client()
        query_api = client.query_api()

        days = int(self.request.query_params.get('days', 7))
        launcher = self.request.query_params['launcher']

        if days >= 7:
            days = 7

        params = {
            '_days': f"-{days}d",
            '_every': '1h',
            '_launcher': launcher,
        }

        q = query_api.query(
            textwrap.dedent(
                '''from(bucket: "openchia_partial")
              |> range(start: duration(v: _days), stop: now())
              |> filter(fn: (r) => r["_measurement"] == "partial")
              |> filter(fn: (r) => r["launcher"] == _launcher)
              |> map(fn: (r) => ({r with error: if r.error != "" then "true" else "false"}))
              |> aggregateWindow(every: duration(v: _every), fn: sum, createEmpty: true)
              |> yield(name: "sum")

            from(bucket: "openchia_partial")
              |> range(start: duration(v: _days), stop: now())
              |> filter(fn: (r) => r["_measurement"] == "partial")
              |> filter(fn: (r) => r["launcher"] == _launcher)
              |> map(fn: (r) => ({r with error: if r.error != "" then "true" else "false"}))
              |> aggregateWindow(every: duration(v: _every), fn: count, createEmpty: true)
              |> yield(name: "count")
              '''
            ), params=params)

        result = []
        num = 0
        for table in q:
            default = table.columns[0].default_value
            for r in table.records:
                # 24 per day -- 7 days -- 2 per hour -- 2 sum/count -- breath room
                if num > 24 * 7 * 2 * 2 * 2:
                    break
                item = {
                    'result': default,
                    'datetime': r['_time'],
                    'field': r['_field'],
                    'value': r['_value'],
                    'launcher': r['launcher'],
                    'harvester': r['harvester'],
                    'error': r.values.get('error'),
                }
                result.append(item)
                num += 1

        return Response(result)


class MempoolView(APIView):

    days_param = openapi.Parameter(
        'days',
        openapi.IN_QUERY,
        description='Number of days (default: 7)',
        type=openapi.TYPE_INTEGER,
    )

    @swagger_auto_schema(
        manual_parameters=[days_param],
        responses={200: TimeseriesSerializer(many=True)},
    )
    def get(self, request, format=None):
        client = get_influxdb_client()
        query_api = client.query_api()

        days = self.request.query_params.get('days', 7)
        every = days_to_every(int(days))

        q = query_api.query(
            textwrap.dedent('''from(bucket: "openchia")
              |> range(start: duration(v: _days), stop: now())
              |> filter(fn: (r) => r["_measurement"] == "mempool")
              |> aggregateWindow(every: duration(v: _every), fn: mean, createEmpty: false)
              |> yield(name: "mean")'''),
            params={
                '_days': f"-{days}d",
                '_every': every,
            },
        )

        result = []
        for table in q:
            for r in table.records:
                result.append({
                    'datetime': r['_time'],
                    'field': r['_field'],
                    'value': r['_value'],
                })

        return Response(result)
