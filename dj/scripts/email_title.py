#!/usr/bin/python

# email_url.py
# emails the video URL to the presenters

from django.core.mail import get_connection, EmailMessage

from django.template import Context, Template

from process import process
from email_ab import email_ab
from django.conf import settings

class email_title(email_ab):

    ready_state = None
    subject_template = "{{ep.show.name}}: Video metadata for your talk {{ep.name}}"

    body_template = """
Hi,

This is Veyepar, the automated video processing system.

Please review the following meta data about your talk so that mistakes can be corrected now and not after the video has gone live.

Released: {{ep.released}}

* "True" means you have given us permission to record your talk and post it online.
{% if not ep.location.active %}However, we are not planning on recording any of the talks in {{ ep.location.name }}.
 {% endif %}
* "None" means it may get recorded and processed, but it will not be made public.
* "False" means you have requested not to be recorded, however the data is available for review in case you change your mind.

The video will be titled with the following image:
http://veyepar.nextdayvideo.com/static/{{ep.show.client.slug}}/{{ep.show.slug}}/titles/{{ep.slug}}.png

And the main page for the video will be here:
{{ep.public_url}}

Problems with the text will need to be fixed in the event database that drives this page:
{{ep.conf_url}}
Except for odd word wrap on the title image.  If it bothers you, let us know how you would like it and we will try to accommodate. 

If everything looks good, you don't need to do anything. Good luck with your talk, expect another email when the video is posted.

Your talk is scheduled for {{ep.start}} in the room called {{ep.location.name}} and you have been alloted {{ep.duration}} (h:m:s). The event organizers will give you instructions on how to check in before your talk.  
"""
    py_name = "email_title.py"
         
if __name__ == '__main__':
    p=email_title()
    p.main()

