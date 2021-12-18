from django.utils import timezone
from django.db import models


class Block(models.Model):

    class Meta:
        db_table = 'block'

    name = models.CharField(max_length=64)
    singleton = models.CharField(max_length=64)
    timestamp = models.BigIntegerField()
    farmed_height = models.BigIntegerField(unique=True)
    confirmed_block_index = models.BigIntegerField()
    puzzle_hash = models.CharField(max_length=64)
    amount = models.BigIntegerField()
    absorb_fee = models.IntegerField(default=0)
    farmed_by = models.ForeignKey('api.Launcher', on_delete=models.SET_NULL, null=True)
    pool_space = models.BigIntegerField(default=0)
    estimate_to_win = models.BigIntegerField(default=-1)
    luck = models.IntegerField(default=-1)
    payout = models.ForeignKey(
        'Payout', related_name='blocks', on_delete=models.SET_NULL, null=True, default=None,
    )


class Launcher(models.Model):

    class Meta:
        db_table = 'farmer'

    launcher_id = models.CharField(primary_key=True, max_length=64)
    name = models.CharField(max_length=200, null=True)
    delay_time = models.BigIntegerField()
    delay_puzzle_hash = models.TextField()
    authentication_public_key = models.TextField()
    singleton_tip = models.BinaryField()
    singleton_tip_state = models.BinaryField()
    p2_singleton_puzzle_hash = models.CharField(max_length=64)
    points = models.BigIntegerField()
    points_pplns = models.BigIntegerField()
    share_pplns = models.DecimalField(max_digits=21, decimal_places=20)
    difficulty = models.BigIntegerField()
    payout_instructions = models.TextField()
    is_pool_member = models.BooleanField()
    estimated_size = models.BigIntegerField(default=0)
    joined_at = models.DateTimeField(default=None, null=True)
    left_at = models.DateTimeField(default=None, null=True)
    email = models.EmailField(default=None, null=True)
    notify_missing_partials_hours = models.IntegerField(default=1, null=True)
    fcm_token = models.CharField(max_length=500, default=None, null=True)
    qrcode_token = models.CharField(max_length=64, default=None, null=True, db_index=True)
    push_missing_partials_hours = models.IntegerField(null=True, default=None)
    push_failed_partials_percent = models.IntegerField(null=True, default=None)
    push_payment = models.BooleanField(default=False)


class Singleton(models.Model):

    class Meta:
        db_table = 'singleton'

    launcher = models.ForeignKey(Launcher, on_delete=models.CASCADE)
    singleton_name = models.CharField(max_length=64)
    singleton_tip = models.BinaryField()
    singleton_tip_state = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)


class Partial(models.Model):

    class Meta:
        db_table = 'partial'

    launcher = models.ForeignKey(Launcher, on_delete=models.CASCADE)
    timestamp = models.IntegerField()
    difficulty = models.IntegerField()
    error = models.CharField(max_length=25, null=True, default=None)
    harvester_id = models.CharField(max_length=64, null=True, default=None)


class PendingPartial(models.Model):

    class Meta:
        db_table = 'pending_partial'

    partial = models.JSONField(default=dict)
    time_received = models.BigIntegerField()
    points_received = models.IntegerField()


class Payout(models.Model):

    class Meta:
        db_table = 'payout'

    datetime = models.DateTimeField(default=timezone.now)
    amount = models.BigIntegerField()
    fee = models.BigIntegerField(default=0)
    referral = models.BigIntegerField(default=0)


class CoinReward(models.Model):

    class Meta:
        db_table = 'coin_reward'

    name = models.CharField(max_length=64, primary_key=True)
    payout = models.ForeignKey(Payout, on_delete=models.CASCADE)


class PayoutAddress(models.Model):

    class Meta:
        db_table = 'payout_address'

    payout = models.ForeignKey(Payout, on_delete=models.CASCADE)
    payout_round = models.IntegerField(default=1)
    fee = models.BooleanField(default=False)
    tx_fee = models.BigIntegerField(default=0)
    puzzle_hash = models.CharField(max_length=64)
    pool_puzzle_hash = models.CharField(max_length=64, default='')
    launcher = models.ForeignKey(Launcher, on_delete=models.SET_NULL, null=True, default=None)
    amount = models.BigIntegerField()
    referral = models.ForeignKey('referral.Referral', null=True, default=None, on_delete=models.SET_NULL)
    referral_amount = models.BigIntegerField(default=0)
    transaction = models.CharField(max_length=100, null=True)
    confirmed_block_index = models.IntegerField(null=True, default=None)


class Space(models.Model):

    class Meta:
        db_table = 'space'

    date = models.DateTimeField()
    size = models.BigIntegerField()


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class GlobalInfo(SingletonModel):

    class Meta:
        db_table = 'globalinfo'

    blockchain_height = models.BigIntegerField(default=0)
    blockchain_space = models.CharField(default='0', max_length=128)
    blockchain_avg_block_time = models.BigIntegerField(default=0, null=True)
    xch_current_price = models.JSONField(default=dict)
    wallets = models.JSONField(default=dict)
