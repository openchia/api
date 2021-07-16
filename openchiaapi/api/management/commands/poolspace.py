import time

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from django.utils import timezone
from api.models import Points, Space

class Command(BaseCommand):

    def handle(self, *args, **options):
        total = Points.objects.filter(timestamp__gte=time.time() - 60 * 60 * 24).aggregate(
            total=Sum('points')
        )['total'] or 0
        Space.objects.create(date=timezone.now(), size=int(total * 10472848254.5664))
