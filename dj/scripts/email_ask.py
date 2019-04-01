#!/usr/bin/python

# email_title.py
# emails the preseter: title slide URL and some other details

from django.core.mail import get_connection, EmailMessage

from django.template import Context, Template

from process import process
from post_yt import post
from email_ab import email_ab
# from django.conf import settings

class email_title(email_ab):

    ready_state = None

    subject_template = '[{{ep.show.name}}] Video metadata for "{{ep.name}}"'

    body_body = """We have your {{ep.show.client.name}} talk scheduled, but we need some information from you to produce a video.

Most important, we need your permission to livestream your talk and to upload the resulting video to YouTube. Please hit reply and either say:
No. (you don't need to explain why.)
or provide the following:
    1. a description of your talk for YouTube
    2. an email of a reviewer for your video (see https://github.com/CarlFK/veyepar/wiki/Reviewer)
    3. (optional) your Twitter handle so that we can tag you when the video URL is tweeted.

Once we have a reply from everyone a 2nd message will go out asking for your confirmation.  This is to double check our manual data entry and allow you to review the image that will be at the front of your video.  So please respond right away to help move this process quickly.

"""

    cap_note = """
{% if ep.name != ep.titlecase %}
NB: Your capitalization doesn't follow the New York Times Manual of Style.
It doesn't have to.  If you care, now is the time to do something about it.

NYTMS: {{ep.titlecase}} {% endif %}
Yours: {{ep.name}}
"""

    def context(self, ep):

        ctx = super(email_title, self).context(ep)

        p = post()
        description = p.construct_description(ep)

        # ctx['name_propper'] = ep.titlecase
        ctx['description'] = description
        ctx['py_name'] = "email_ask.py"

        return ctx

if __name__ == '__main__':
    p=email_title()
    p.main()

