import datetime
import logging
import math
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from giveaway.models import Giveaway, TicketsRound
from api.models import Launcher

logger = logging.getLogger('giveaway_round')


def get_distributed_tickets(giveaway):
    tickets = set()
    for tr in TicketsRound.objects.filter(giveaway=giveaway):
        tickets.update(tr.tickets)
    return tickets


class Command(BaseCommand):

    def handle(self, *args, **options):
        now = datetime.datetime.now(datetime.timezone.utc)
        giveaway = Giveaway.objects.order_by('draw_datetime').filter(draw_datetime__gt=now)[0]

        available_tickets = set(range(1, giveaway.total_tickets + 1))
        distributed_tickets = get_distributed_tickets(giveaway)

        available_tickets = list(available_tickets - distributed_tickets)
        logger.error(f'{len(available_tickets)} available tickets')

        with transaction.atomic():
            for launcher in Launcher.objects.filter(is_pool_member=True):
                size_tib = launcher.estimated_size / 1024 ** 4
                num_tickets = 0
                # Tiering tickets
                # 0-100 TiB gets 1 ticket per 1 TiB
                # 100-200 TiB gets 1 ticket per 2 TiB
                # 200-500 TiB gets 1 ticket per 3 TiB
                # 500-1000 TiB gets 1 ticket per 4 TiB
                # 1000+ TiB gets 1 ticket per 5 TiB
                for start, end, per_tib in (
                    (0, 100, 1),
                    (100, 200, 2),
                    (200, 500, 3),
                    (500, 1000, 4),
                    (1000, 1000000, 5),  # 1000000 == infinite
                ):
                    if size_tib - start > 0:
                        num_tickets += math.floor(min(size_tib - start, end - start) / per_tib)
                tickets = []
                for _ in range(num_tickets):
                    tickets.append(
                        available_tickets.pop(random.randint(0, len(available_tickets) - 1))
                    )
                TicketsRound.objects.create(
                    giveaway=giveaway,
                    launcher=launcher,
                    estimated_size=launcher.estimated_size,
                    number_tickets=len(tickets),
                    tickets=sorted(tickets),
                )
