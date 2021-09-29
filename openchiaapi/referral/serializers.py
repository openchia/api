from rest_framework import serializers

from .models import Referral
from api.serializers import LauncherSerializer


class ReferralSerializer(serializers.HyperlinkedModelSerializer):
    launcher = LauncherSerializer()
    referrer = LauncherSerializer()

    class Meta:
        model = Referral
        fields = '__all__'
