from django.utils import timezone

from api.models import Launcher
from referral.models import Referral


def update_referral(launcher, referrer):
    referrals = Referral.objects.filter(launcher=launcher, active=True)
    if referrer:
        ref_launcher = Launcher.objects.filter(launcher_id=referrer)
        if not ref_launcher.exists():
            raise ValueError('Referrer does not exist.')
        ref_launcher = ref_launcher[0]
        if ref_launcher.launcher_id == launcher.launcher_id:
            raise ValueError('You cannot refer youself.')

        # Make sure we are not closing a loop of referrers
        # A <- B <- C <- D <- A
        referrers_loop = [launcher.launcher_id]
        prev_ref_launcher = ref_launcher
        while True:
            prev_ref = Referral.objects.filter(launcher=prev_ref_launcher, active=True)
            if prev_ref.exists():
                if prev_ref[0].referrer.launcher_id in referrers_loop:
                    raise ValueError('A loop of referrals is not allowed.')
                else:
                    referrers_loop.append(prev_ref[0].referrer.launcher_id)
                    prev_ref_launcher = prev_ref[0].referrer
            else:
                break

        if referrals.exists():
            referrals.update(active=False)

        ref = Referral.objects.filter(launcher=launcher, referrer=ref_launcher)
        if ref.exists():
            ref.update(active=True)
        else:
            Referral.objects.create(
                launcher=launcher,
                referrer=ref_launcher,
                total_income=0,
                active=True,
                active_date=timezone.now(),
            )
    else:
        if referrals.exists():
            referrals.update(active=False)
