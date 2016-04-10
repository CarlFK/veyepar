# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20160116_2037'),
    ]

    operations = [
        migrations.AlterField(
            model_name='episode',
            name='edit_key',
            field=models.CharField(default=b'65315954', max_length=32, null=True, help_text=b'key to allow unauthenticated users to edit this item.', blank=True),
            preserve_default=True,
        ),
    ]
