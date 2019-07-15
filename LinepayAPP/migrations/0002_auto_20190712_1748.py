# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LinepayAPP', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='clientSession',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('status', models.TextField(default='default')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='member',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('lineID', models.TextField()),
                ('displayName', models.TextField()),
                ('address', models.TextField()),
                ('phone', models.TextField()),
                ('birthDay', models.TextField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='shoppingCart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('shopId', models.TextField()),
                ('itemName', models.TextField()),
                ('itemPrice', models.IntegerField()),
                ('addOnNameHistory', models.TextField()),
                ('addOnPriceHistory', models.TextField()),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('member', models.ForeignKey(to='LinepayAPP.member')),
            ],
        ),
        migrations.AddField(
            model_name='clientsession',
            name='member',
            field=models.ForeignKey(to='LinepayAPP.member'),
        ),
    ]
