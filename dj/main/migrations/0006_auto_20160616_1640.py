# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20160616_1624'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='edit_key',
            field=models.CharField(default='56049041', blank=True, null=True, max_length=32, help_text='key to allow unauthenticated users to edit this item.'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='location',
            name='hours_offset',
            field=models.IntegerField(help_text='Adjust for bad clock setting', blank=True, null=True),
            preserve_default=True,
        ),
    ]
