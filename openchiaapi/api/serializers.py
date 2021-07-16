from rest_framework import serializers
from .models import Block, Launcher, Payout, PayoutAddress


class BlockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'


class LauncherSerializer(serializers.HyperlinkedModelSerializer):
    points_of_total = serializers.SerializerMethodField('get_points_of_total')

    class Meta:
        model = Launcher
        fields = [
            'launcher_id', 'name', 'p2_singleton_puzzle_hash', 'points', 'difficulty',
            'is_pool_member', 'points_of_total',
        ]

    def get_points_of_total(self, instance):
        if not self.context['total_points']:
            return 0
        return (instance.points / self.context['total_points']) * 100


class PayoutSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Payout
        fields = '__all__'


class PayoutAddressSerializer(serializers.HyperlinkedModelSerializer):
    payout = PayoutSerializer()

    class Meta:
        model = PayoutAddress
        fields = '__all__'


class StatsSerializer(serializers.Serializer):
    blockchain_height = serializers.IntegerField()
    blockchain_space = serializers.IntegerField()
    fee = serializers.DecimalField(max_digits=3, decimal_places=2)
    estimate_win = serializers.IntegerField()
    rewards_amount = serializers.DecimalField(max_digits=10, decimal_places=5)
    rewards_blocks = serializers.IntegerField()
    pool_space = serializers.IntegerField()
    farmers = serializers.IntegerField()


class SpaceSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    size = serializers.IntegerField()
