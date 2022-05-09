# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atex_web', '0003_update_django_1_8'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='price',
            field=models.FloatField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=models.ForeignKey(default=None, to='atex_web.Brand', null=True, on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
