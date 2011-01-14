from django.db.models.signals import post_syncdb
import django.contrib.sites.models 
# import django.contrib.sites.management

"""
whack sites record to workaround "view on site"  bug:
http://code.djangoproject.com/ticket/8960
which has ben fixed.  today.  
which I figured out riht after I figured out the workaround.

Leaving this in here untill the fix hits the repos.
it is pretty harmless, so no need to rush it out.
"""

"""
# get rid of this alltogher given:
http://code.djangoproject.com/changeset/13980#file12
 	153	For code which relies on getting the current domain but cannot be certain 
 	154	that the sites framework will be installed for any given project
"""

# def init_data(sender, **kwargs):
#     django.contrib.sites.models.Site.objects.all().delete()

# post_syncdb.connect(init_data, sender=django.contrib.sites.models)
# post_syncdb.disconnect(django.contrib.sites.management.create_default_site)

