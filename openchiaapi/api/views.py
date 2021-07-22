from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, mixins, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Block, Launcher, Partial, Payout, PayoutAddress, Space
from .serializers import (
    BlockSerializer,
    LauncherSerializer,
    PartialSerializer,
    PayoutSerializer,
    PayoutAddressSerializer,
    StatsSerializer,
    SpaceSerializer,
)
from .utils import (
    get_pool_info, get_node_info_sync, estimated_time_to_win_sync,
)


POOL_DEFAULT_TARGET_ADDRESS = None


class BlockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    filterset_fields = ['farmed_by', 'payout']
    ordering_fields = ['confirmed_block_index', 'payout']
    ordering = ['-confirmed_block_index']


class LauncherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Launcher.objects.filter(is_pool_member=True)
    serializer_class = LauncherSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['difficulty', 'launcher_id', 'name']
    search_fields = ['launcher_id', 'name']
    ordering_fields = ['points', 'difficulty']
    ordering = ['-points']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['total_points'] = Launcher.objects.filter(is_pool_member=True).aggregate(
            total=Sum('points')
        )['total']
        return context


class StatsView(APIView):

    @swagger_auto_schema(responses={200: StatsSerializer(many=False)})
    def get(self, request, format=None):
        coinrecord = Block.objects.order_by('-confirmed_block_index')
        last_cr = coinrecord[0] if coinrecord.exists() else None
        farmers = Launcher.objects.filter(is_pool_member=True).count()
        pool_info = get_pool_info()
        try:
            size = Space.objects.latest('id').size
        except Space.DoesNotExist:
            size = 0

        blockchain_state = get_node_info_sync()
        minutes_to_win = estimated_time_to_win_sync(size, blockchain_state['space'])
        pi = StatsSerializer(data={
            'fee': Decimal(pool_info['fee']),
            'farmers': farmers,
            'rewards_amount': coinrecord.aggregate(total=Sum('amount'))['total'],
            'rewards_blocks': coinrecord.count(),
            'pool_space': size,
            'estimate_win': minutes_to_win,
            'blockchain_height': blockchain_state['peak'].height,
            'blockchain_space': blockchain_state['space'],
        })
        pi.is_valid()
        return Response(pi.data)



class PartialFilter(django_filters.FilterSet):
    min_timestamp = django_filters.NumberFilter(field_name='timestamp', lookup_expr='gte')

    class Meta:
        model = Partial
        fields = ['launcher', 'timestamp']


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


class PayoutAddressViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PayoutAddress.objects.all()
    serializer_class = PayoutAddressSerializer
    filterset_fields = ['payout', 'puzzle_hash', 'launcher']
    ordering_fields = ['payout', 'launcher', 'confirmed_block_index']
    ordering = ['-payout']


class SpaceView(APIView):
    DEFAULT_DAYS = 30
    days_param = openapi.Parameter(
        'days',
        openapi.IN_QUERY,
        description=f'Number of days (default: {DEFAULT_DAYS})',
        type=openapi.TYPE_INTEGER,
    )

    @swagger_auto_schema(
        manual_parameters=[days_param],
        responses={200: SpaceSerializer(many=True)}
    )
    def get(self, request, format=None):
        days = self.request.query_params.get('days') or self.DEFAULT_DAYS
        size = Space.objects.filter(date__gte=datetime.now() - timedelta(days=int(days)))
        return Response([{'date': i.date, 'size': i.size} for i in size])
