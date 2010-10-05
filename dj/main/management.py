from django.db.models.signals import post_syncdb
import django.contrib.sites.models 

def init_data(sender, **kwargs):
    django.contrib.sites.models.Site.objects.all().delete()

post_syncdb.connect(init_data, sender=django.contrib.sites.models)

