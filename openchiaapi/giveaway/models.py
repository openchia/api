from django.db import models


class Giveaway(models.Model):

    draw_datetime = models.DateTimeField(unique=True)
    selected_number = models.IntegerField(null=True)
    total_tickets = models.IntegerField()
    prize_amount = models.BigIntegerField()
    winner = models.ForeignKey('api.Launcher', on_delete=models.SET_NULL, null=True)


class TicketsRound(models.Model):
    giveaway = models.ForeignKey(Giveaway, on_delete=models.CASCADE)
    launcher = models.ForeignKey('api.Launcher', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    estimated_size = models.BigIntegerField()
    number_tickets = models.IntegerField()
    tickets = models.JSONField()
