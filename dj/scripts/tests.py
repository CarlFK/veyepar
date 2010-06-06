#!/usr/bin/python

import datetime


import process
from main.models import fnify, Client, Show, Location, Episode, Raw_File, Cut_List 
from main.views import make_test_data

from django.contrib.auth.models import User

users=User.objects.all()
if not users:
    user = User.objects.create_user( 'test', 'test@example.com', 'abc' )
    user.is_superuser=True
    user.is_staff=True
    user.save()

make_test_data()
