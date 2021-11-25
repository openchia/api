import os
import yaml


def custom_settings():
    django_settings = os.environ.get('DJANGO_SETTINGS_FILE')
    if django_settings and os.path.exists(django_settings):
        with open(django_settings, 'r') as f:
            django_settings = yaml.safe_load(f)
    django_settings = django_settings or {}
    return django_settings
