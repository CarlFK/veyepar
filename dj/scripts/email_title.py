#!/usr/bin/python

# email_title.py
# emails the preseter: title slide URL and some other details

from django.core.mail import get_connection, EmailMessage

from django.template import Context, Template

from process import process
from email_ab import email_ab
# from django.conf import settings

class email_title(email_ab):

    ready_state = None

    subject_template = '[{{ep.show.name}}] Video metadata for "{{ep.name}}"'

    body_body = """Details about your upcoming talk:

Start: {{ep.start|date:"l"}} {{ep.start}} (that is in {{ep.start|timeuntil}})
Length: {{ep.get_minutes}}  minutes
Location: {{ep.location.name}}
Released: {{ep.released|yesno:"Yes,No,None"}}
Conference page: {{ep.conf_url}}

Projector hookup will be 720p HDMI (which is 16:9). Please bring any adapters you need. If you have any special requests or have forgotten your adapter, please contact us ASAP and we will try to accommodate you.

The video will be posted with the following:

Title: {{ep.name}}
{% if image_url %}
http://veyepar.{{ep.show.client.bucket_id}}.cdn.nextdayvideo.com/veyepar/{{ep.show.client.slug}}/{{ep.show.slug}}/titles/{{ep.slug}}.png
{% endif %}
{% if ep.public_url%}The main page for the video will be here:
{{ep.public_url}}
{% else %}Description: {% if ep.description %}
=== begin ===
{{ep.composed_description}}
=== end description ===
  {% else %}
    (is blank.)
  {% endif %}
{% endif %}
Released: "{{ep.released|yesno:"Yes,No,None"}}" means:
Yes: Permission has been given to record your talk and post it online.  Once it is up, you will get another e-mail with a URL that is not public until someone approves it.  Once it's approved it will be made public and tweeted {{ep.show.client.tweet_prefix}} {{ep.twitter_id}}.
No: You have requested for the video not to be released. However the a video may be made anyway and available for review in case you change your mind.  If you need to be absolutly sure, at the event you can ask to have the camera tuned off.
None: Permission to publish a video of this talk is unknown.  This means it may get recorded and processed, but it will not be made public and we will send another email asking for permission.  Please reply to this email stating your preference.
{% if not ep.location.active %}However, we are not planning on recording any of the talks in {{ ep.location.name }}.  {% endif %}

If everything looks good, you don't need to do anything. Good luck with your talk; expect another email when the video is posted.

"""

    def context(self, ep):

        ctx = super(email_title, self).context(ep)

        # find some urls to tell someone about
        # If there is a Richard (pyvideo) url, use that;
        if ep.public_url is None:
            image_url = True
        elif "pyvideo" in ep.public_url:
            # deal with pyvideo not showing title slide
            image_url = True
        else:
            image_url = False

        # rax upload fixed?
        image_url = True

        ctx['image_url'] = image_url
        ctx['py_name'] = "email_title.py"

        return ctx

if __name__ == '__main__':
    p=email_title()
    p.main()

