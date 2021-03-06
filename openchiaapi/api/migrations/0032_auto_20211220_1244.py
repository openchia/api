# Generated by Django 3.2.6 on 2021-12-20 12:44

from django.db import migrations, models
import django.db.models.deletion


def move_transaction(apps, schema_editor):
    Transaction = apps.get_model('api', 'Transaction')
    PayoutAddress = apps.get_model('api', 'PayoutAddress')
    for pa in PayoutAddress.objects.exclude(transaction=None):
        t = Transaction.objects.filter(transaction=pa.transaction)
        if not t.exists():
            t = Transaction(
                transaction=pa.transaction,
                xch_current_price=None,
                confirmed_block_index=pa.confirmed_block_index,
            )
            t.save()
        else:
            t = t[0]
        pa.transactionnew = t
        pa.save()



class Migration(migrations.Migration):

    dependencies = [
        ('api', '0031_launcher_push_block_farmed'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            options={'db_table': 'transaction'},
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction', models.CharField(max_length=64, unique=True)),
                ('xch_current_price', models.JSONField(default=None, null=True)),
                ('confirmed_block_index', models.IntegerField(default=None, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='payoutaddress',
            name='transactionnew',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.transaction'),
        ),
        migrations.RunPython(move_transaction),
        migrations.RemoveField(
            model_name='payoutaddress',
            name='confirmed_block_index',
        ),
        migrations.AddField(
            model_name='block',
            name='xch_current_price',
            field=models.JSONField(default=None, null=True),
        ),
        migrations.RemoveField(
            model_name='payoutaddress',
            name='transaction',
        ),
        migrations.RenameField(
            model_name='payoutaddress',
            old_name='transactionnew',
            new_name='transaction',
        ),
    ]
