# Generated by Django 3.2.6 on 2021-10-19 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_auto_20211016_2016'),
    ]

    operations = [
        migrations.AddField(
            model_name='block',
            name='absorb_fee',
            field=models.IntegerField(default=0),
        ),
    ]