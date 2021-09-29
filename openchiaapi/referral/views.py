from rest_framework import viewsets

from .models import Referral
from .serializers import ReferralSerializer


class ReferralViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Referral.objects.filter(active=True)
    serializer_class = ReferralSerializer
    filterset_fields = ['launcher', 'referrer']
    search_fields = ['launcher', 'referrer']
    ordering_fields = ['total_income']
    ordering = ['-total_income']
