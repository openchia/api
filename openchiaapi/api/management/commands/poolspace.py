import time

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone
from api.models import Partial, Space


class Command(BaseCommand):

    def handle(self, *args, **options):
        interval = 60 * 60 * 24
        total = Partial.objects.filter(error=None, timestamp__gte=time.time() - interval).aggregate(
            total=Sum('difficulty')
        )['total'] or 0
        size = int(total / (interval * 1.088e-15))
        Space.objects.create(date=timezone.now(), size=size)
