# Generated by Django 3.2.6 on 2022-02-16 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0037_auto_20220215_1325'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendingpartial',
            name='req_metadata',
            field=models.JSONField(default=dict),
        ),
    ]