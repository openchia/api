# Generated by Django 3.2.6 on 2022-02-08 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0034_auto_20220131_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='created_at_time',
            field=models.DateTimeField(null=True),
        ),
    ]
