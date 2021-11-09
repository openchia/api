from collections import defaultdict

from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Giveaway, TicketsRound
from .serializers import ClosestTicketSerializer, GiveawaySerializer, TicketsRoundSerializer
from .utils import take_closest


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

    @swagger_auto_schema(request_body=ClosestTicketSerializer)
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

        results = set()
        for number in take_closest(list(closest.keys()), ticket.validated_data['number']):
            results.update({i.launcher_id for i in closest[number]})
        return Response(results)
