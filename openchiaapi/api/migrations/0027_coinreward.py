# Generated by Django 3.2.6 on 2021-11-05 10:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_singleton'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoinReward',
            fields=[
                ('name', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('payout', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.payout')),
            ],
            options={
                'db_table': 'coin_reward',
            },
        ),
    ]
