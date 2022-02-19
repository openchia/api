import datetime

from django.core.management.base import BaseCommand
from giveaway.models import Giveaway


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days=days_ahead)


class Command(BaseCommand):

    def handle(self, *args, **options):
        next_draw = next_weekday(datetime.datetime.now(datetime.timezone.utc), 6)  # 6 = Sunday
        next_draw = next_draw.replace(hour=20, minute=0, second=0, microsecond=0)

        Giveaway.objects.create(
            draw_datetime=next_draw,
            total_tickets=1000000,  # 1 ticket per TiB = 1EiB room
            prize_amount=1 * (10 ** 12),  # mojos
        )
