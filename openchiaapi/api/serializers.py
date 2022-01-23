from rest_framework import serializers
from .models import Block, Launcher, Partial, Payout, PayoutAddress, Transaction


class LauncherSerializer(serializers.HyperlinkedModelSerializer):
    points_of_total = serializers.SerializerMethodField('get_points_of_total')

    class Meta:
        model = Launcher
        fields = [
            'launcher_id', 'name', 'p2_singleton_puzzle_hash', 'points',
            'points_pplns',
            'share_pplns',
            'difficulty',
            'is_pool_member', 'points_of_total', 'estimated_size',
            'joined_at',
        ]

    def get_points_of_total(self, instance):
        if not self.context.get('total_points'):
            return 0
        return (instance.points / self.context['total_points']) * 100

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if (self.context['request'].auth and
                self.context['request'].auth.launcher_id == ret['launcher_id']) or \
                self.context['request'].session.get('launcher_id') == ret['launcher_id']:
            ret['email'] = instance.email
            ret['notify_missing_partials_hours'] = instance.notify_missing_partials_hours
            ret['push_missing_partials_hours'] = instance.push_missing_partials_hours
            ret['push_block_farmed'] = instance.push_block_farmed
            ret['fcm_token'] = instance.fcm_token
            try:
                ret['referrer'] = instance.referral_set.filter(active=True)[0].referrer_id
            except IndexError:
                ret['referrer'] = None
        return ret


class LauncherUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, allow_null=True)
    notify_missing_partials_hours = serializers.CharField(required=False, allow_null=True)
    referrer = serializers.CharField(required=False, allow_null=True)
    fcm_token = serializers.CharField(required=False, allow_null=True)
    push_missing_partials_hours = serializers.CharField(required=False, allow_null=True)
    push_block_farmed = serializers.BooleanField(required=False)


class BlockSerializer(serializers.HyperlinkedModelSerializer):
    farmed_by = LauncherSerializer()

    class Meta:
        model = Block
        fields = '__all__'


class LoginSerializer(serializers.Serializer):
    launcher_id = serializers.CharField()
    authentication_token = serializers.IntegerField()
    signature = serializers.CharField()


class LoginQRSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class PartialSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Partial
        fields = '__all__'


class PayoutSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Payout
        fields = (
            'id', 'datetime', 'amount', 'fee', 'blocks',
        )


class TransactionSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Transaction
        fields = '__all__'


class PayoutAddressSerializer(serializers.HyperlinkedModelSerializer):
    launcher = LauncherSerializer()
    payout = PayoutSerializer()
    transaction = TransactionSerializer()

    class Meta:
        model = PayoutAddress
        fields = (
            'id', 'payout', 'puzzle_hash', 'launcher', 'amount', 'transaction',
        )


class StatsSerializer(serializers.Serializer):
    blockchain_height = serializers.IntegerField()
    blockchain_space = serializers.IntegerField()
    fee = serializers.DecimalField(max_digits=3, decimal_places=2)
    estimate_win = serializers.IntegerField()
    time_since_last_win = serializers.IntegerField()
    rewards_amount = serializers.DecimalField(max_digits=10, decimal_places=5)
    rewards_blocks = serializers.IntegerField()
    last_rewards = serializers.ListField(
        child=serializers.DictField(),
    )
    pool_space = serializers.IntegerField()
    farmers = serializers.IntegerField()
    farmers_active = serializers.IntegerField()
    reward_system = serializers.CharField()
    xch_current_price = serializers.JSONField()
    pool_wallets = serializers.JSONField()
    average_effort = serializers.IntegerField()
    xch_tb_month = serializers.DecimalField(max_digits=10, decimal_places=9)


class SpaceSerializer(serializers.Serializer):
    date = serializers.DateTimeField()
    size = serializers.IntegerField()


class XCHScanStatsSerializer(serializers.Serializer):
    poolInfo = serializers.DictField()
    farmedBlocks = serializers.ListField(
        child=serializers.DictField(),
    )
    capacityBytes = serializers.IntegerField()
    farmers = serializers.IntegerField()
