import functools
from collections import defaultdict

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Launcher
from api.serializers import LauncherSerializer

from openchiaapi.utils import custom_settings

from .models import Giveaway, TicketsRound
from .serializers import ClosestTicketSerializer, ClosestWinnerSerializer, GiveawaySerializer, TicketsRoundSerializer
from .utils import take_closest


@functools.cache
def get_giveaway_pw():
    settings = custom_settings()
    return settings['giveaway']['password']


class GiveawayViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Giveaway.objects.all()
    serializer_class = GiveawaySerializer
    filterset_fields = ['winner']
    ordering_fields = ['draw_datetime']
    ordering = ['-draw_datetime']


class TicketsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TicketsRound.objects.all()
    serializer_class = TicketsRoundSerializer
    filterset_fields = ['launcher', 'giveaway']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class ClosestTicketView(APIView):

    serializer_class = ClosestWinnerSerializer

    @swagger_auto_schema(query_serializer=ClosestTicketSerializer)
    def get(self, request):
        ticket = ClosestTicketSerializer(data=request.GET)
        ticket.is_valid(raise_exception=True)

        closest = defaultdict(list)
        for tr in TicketsRound.objects.filter(
            giveaway__id=ticket.validated_data['giveaway'],
            number_tickets__gt=0,
        ):
            value = take_closest(tr.tickets, ticket.validated_data['number'])[0]
            closest[value].append(tr.launcher)

        results = []
        for number in take_closest(list(closest.keys()), ticket.validated_data['number']):
            for i in closest[number]:
                instance = Launcher.objects.get(pk=i.launcher_id)
                s = LauncherSerializer(instance, context={'request': request})
                results.append(s.to_representation(instance))
        return Response(results)

    @swagger_auto_schema(request_body=ClosestWinnerSerializer)
    def post(self, request):
        winner = ClosestWinnerSerializer(data=request.POST)
        winner.is_valid(raise_exception=True)

        if get_giveaway_pw() != winner.validated_data['password']:
            raise PermissionDenied()

        giveaway = Giveaway.objects.get(pk=winner.validated_data['giveaway'])
        launcher = Launcher.objects.get(launcher_id=winner.validated_data['winner'])
        giveaway.winner = launcher
        giveaway.selected_number = winner.validated_data['number']
        giveaway.save()

        return Response('OK')
