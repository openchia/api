from datetime import datetime
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
    farmed_by = models.CharField(max_length=64, null=True)
    payout = models.ForeignKey('Payout', on_delete=models.SET_NULL, null=True, default=None)


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
    difficulty = models.BigIntegerField()
    payout_instructions = models.TextField()
    is_pool_member = models.BooleanField()


class Partial(models.Model):

    class Meta:
        db_table = 'partial'

    launcher = models.ForeignKey(Launcher, on_delete=models.CASCADE)
    timestamp = models.IntegerField()
    difficulty = models.IntegerField()
    error = models.CharField(max_length=25, null=True, default=None)


class Payout(models.Model):

    class Meta:
        db_table = 'payout'

    datetime = models.DateTimeField(default=datetime.now)
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
