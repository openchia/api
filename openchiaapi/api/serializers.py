from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum
from rest_framework import serializers

from pool.util import days_pooling, stay_fee_discount, size_discount

from .models import Block, Launcher, Partial, Payout, PayoutAddress, Transaction
from .utils import get_pool_fees


POOL_FEES = get_pool_fees()


class LauncherSerializer(serializers.HyperlinkedModelSerializer):
    points_of_total = serializers.SerializerMethodField('get_points_of_total')
    payout = serializers.SerializerMethodField('get_payout')
    fee = serializers.SerializerMethodField('get_fee')

    class Meta:
        model = Launcher
        fields = [
            'launcher_id', 'name', 'p2_singleton_puzzle_hash', 'points',
            'points_pplns',
            'share_pplns',
            'difficulty',
            'is_pool_member',
            'estimated_size',
            'joined_at',
            'payout',
            'fee',
            'points_of_total',
        ]

    def get_points_of_total(self, instance):
        return float(instance.share_pplns)

    def get_fee(self, instance):
        if 'view' not in self.context or self.context['view'].get_view_name() != 'Launcher Instance':
            return {}
        days = days_pooling(instance.joined_last_at, instance.left_last_at, instance.is_pool_member)
        stay_length = float(stay_fee_discount(POOL_FEES['stay_discount'], POOL_FEES['stay_length'], days))
        size = float(size_discount(instance.estimated_size, POOL_FEES['size_discount']))
        return {
            'stay_length_days': days,
            'stay_length_days_max': POOL_FEES['stay_length'],
            'stay_length_discount': POOL_FEES['pool'] * stay_length,
            'stay_length_discount_max': POOL_FEES['pool'] * POOL_FEES['stay_discount'],
            'size_discount': POOL_FEES['pool'] * size,
            'pool': POOL_FEES['pool'],
            'final': POOL_FEES['pool'] * (1 - stay_length - size),
        }

    def get_payout(self, instance):
        if 'view' not in self.context or self.context['view'].get_view_name() != 'Launcher Instance':
            return {}
        return {
            'total_paid': instance.payoutaddress_set.exclude(
                transaction__confirmed_block_index=None
            ).aggregate(total_paid=Sum('amount'))['total_paid'] or 0,
            'total_unpaid': instance.payoutaddress_set.filter(
                transaction__confirmed_block_index=None
            ).aggregate(total_unpaid=Sum('amount'))['total_unpaid'] or 0,
            'total_transactions': instance.payoutaddress_set.exclude(
                transaction__confirmed_block_index=None
            ).values('transaction__transaction').order_by('transaction__transaction').aggregate(
                transactions=Count('transaction__transaction', distinct=True)
            )['transactions']
        }

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
            ret['custom_difficulty'] = instance.custom_difficulty
            ret['minimum_payout'] = instance.minimum_payout
            ret['payout_instructions'] = instance.payout_instructions
            try:
                notification = instance.notification
                ret['size_drop'] = notification.size_drop
                ret['size_drop_interval'] = notification.size_drop_interval
                ret['size_drop_percent'] = notification.size_drop_percent
                ret['failed_partials'] = notification.failed_partials
                ret['failed_partials_percent'] = notification.failed_partials_percent
                ret['payment'] = notification.payment
            except ObjectDoesNotExist:
                ret['size_drop'] = []
                ret['size_drop_interval'] = None
                ret['size_drop_percent'] = None
                ret['failed_partials'] = None
                ret['failed_partials_percent'] = None
                ret['payment'] = []
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
    custom_difficulty = serializers.ChoiceField(required=False, allow_null=True, choices=(
        ('LOWEST', 'Lowest'),
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('HIGHEST', 'Highest'),
    ))
    minimum_payout = serializers.IntegerField(required=False, allow_null=True)

    payment = serializers.MultipleChoiceField(choices=(
        ('PUSH', 'Push'),
        ('EMAIL', 'Email'),
    ), required=False)
    size_drop = serializers.MultipleChoiceField(choices=(
        ('PUSH', 'Push'),
        ('EMAIL', 'Email'),
    ), required=False)
    size_drop_interval = serializers.IntegerField(
        required=False, allow_null=True, min_value=45, max_value=60 * 24,
    )
    size_drop_percent = serializers.IntegerField(
        required=False, allow_null=True, min_value=20, max_value=100,
    )


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
        exclude = ['remote']


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


class PayoutTransactionSerializer(serializers.Serializer):
    transaction_name = serializers.CharField()
    created_at_time = serializers.CharField()
    launcher = serializers.CharField()
    amount = serializers.IntegerField()
    confirmed_block_index = serializers.IntegerField()
    xch_price = serializers.DictField()


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


class TimeseriesSerializer(serializers.Serializer):
    datetime = serializers.CharField(required=True)
    field = serializers.IntegerField(required=True)
    value = serializers.IntegerField(required=True)
