from rest_framework import serializers
from .models import Block, Launcher, Partial, Payout, PayoutAddress


class LauncherSerializer(serializers.HyperlinkedModelSerializer):
    points_of_total = serializers.SerializerMethodField('get_points_of_total')

    class Meta:
        model = Launcher
        fields = [
            'launcher_id', 'name', 'p2_singleton_puzzle_hash', 'points', 'difficulty',
            'is_pool_member', 'points_of_total',
        ]

    def get_points_of_total(self, instance):
        if not self.context.get('total_points'):
            return 0
        return (instance.points / self.context['total_points']) * 100


class LauncherUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)


class BlockSerializer(serializers.HyperlinkedModelSerializer):
    farmed_by = LauncherSerializer()

    class Meta:
        model = Block
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    launcher_id = serializers.CharField()
    authentication_token = serializers.IntegerField()
    signature = serializers.CharField()


class PartialSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Partial
        fields = '__all__'


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
