# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20160116_2028'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='edit_key',
            field=models.CharField(default=b'46888493', max_length=32, null=True, help_text=b'key to allow unauthenticated users to edit this item.', blank=True),
            preserve_default=True,
        ),
    ]
