# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('click', models.DateTimeField(help_text=b'When Cut was Clicked.')),
                ('location', models.ForeignKey(to='main.Location')),
                ('show', models.ForeignKey(to='main.Show')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='episode',
            name='edit_key',
            field=models.CharField(default=b'69474658', max_length=32, null=True, help_text=b'key to allow unauthenticated users to edit this item.', blank=True),
            preserve_default=True,
        ),
    ]
