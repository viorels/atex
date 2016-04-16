# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atex_web', '0004_add_price_brand'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='stock',
            field=models.SmallIntegerField(null=True, choices=[(0, b'call'), (1, b'in stoc'), (2, b'la comanda'), (3, b'indisponibil')]),
        ),
        migrations.AlterField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(to='atex_web.Brand', null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='price',
            field=models.FloatField(null=True),
        ),
    ]
