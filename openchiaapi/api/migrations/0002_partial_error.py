# Generated by Django 3.2.3 on 2021-07-21 19:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='partial',
            name='error',
            field=models.CharField(default=None, max_length=25, null=True),
        ),
    ]
