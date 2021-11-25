
from django.db.models import Sum
from rest_framework import serializers

from api.serializers import LauncherSerializer
from .models import Giveaway, TicketsRound


class GiveawaySerializer(serializers.HyperlinkedModelSerializer):
    issued_tickets = serializers.SerializerMethodField('get_issued_tickets')
    winner = LauncherSerializer()

    class Meta:
        model = Giveaway
        fields = '__all__'

    def get_issued_tickets(self, instance):
        return TicketsRound.objects.filter(giveaway=instance).aggregate(
            total=Sum('number_tickets')
        )['total']


class TicketsRoundSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TicketsRound
        fields = '__all__'


class ClosestTicketSerializer(serializers.Serializer):
    giveaway = serializers.IntegerField()
    number = serializers.IntegerField()


class ClosestWinnerSerializer(serializers.Serializer):
    giveaway = serializers.IntegerField()
    winner = serializers.CharField()
    number = serializers.IntegerField()
    password = serializers.CharField(style={'input_type': 'password'})

    def __init__(self, *args, **kwargs):
        if 'context' in kwargs:
            request = kwargs['context']['request']
            kwargs['data'] = request.query_params
        super().__init__(*args, **kwargs)
