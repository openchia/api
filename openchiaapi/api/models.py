from django.utils import timezone
from django.db import models


class Block(models.Model):

    class Meta:
        db_table = 'block'

    name = models.CharField(max_length=64)
    singleton = models.CharField(max_length=64)
    timestamp = models.BigIntegerField()
    confirmed_block_index = models.IntegerField()
    puzzle_hash = models.CharField(max_length=64)
    amount = models.BigIntegerField()
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
    email = models.EmailField(default=None, null=True)
    notify_missing_partials_hours = models.IntegerField(default=1, null=True)


class Partial(models.Model):

    class Meta:
        db_table = 'partial'

    launcher = models.ForeignKey(Launcher, on_delete=models.CASCADE)
    timestamp = models.IntegerField()
    difficulty = models.IntegerField()
    error = models.CharField(max_length=25, null=True, default=None)
    harvester_id = models.CharField(max_length=64, null=True, default=None)


class Payout(models.Model):

    class Meta:
        db_table = 'payout'

    datetime = models.DateTimeField(default=timezone.now)
    amount = models.BigIntegerField()
    fee = models.BigIntegerField(default=0)


class PayoutAddress(models.Model):

    class Meta:
        db_table = 'payout_address'

    payout = models.ForeignKey(Payout, on_delete=models.CASCADE)
    puzzle_hash = models.CharField(max_length=64)
    launcher = models.ForeignKey(Launcher, on_delete=models.SET_NULL, null=True, default=None)
    amount = models.BigIntegerField()
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
    xch_current_price = models.JSONField(default=dict)
