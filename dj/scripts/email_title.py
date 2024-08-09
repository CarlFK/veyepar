#!/usr/bin/python

# email_title.py
# emails the preseter: title slide URL and some other details

from django.core.mail import get_connection, EmailMessage

from django.template import Context, Template

from process import process
from email_ab import email_ab

class email_title(email_ab):

    ready_state = None

    subject_template = '[{{ep.show.name}}] Video metadata for "{{ep.name}}"'

    body_body = """Details about your upcoming talk:

Start: {{ep.start|date:"l"}} {{ep.start}} (that is in {{ep.start|timeuntil}})
Length: {{ep.get_minutes}} minutes
Location: {{ep.location.name}}
Projector hookup: HDMI 720p
Slide aspect: 16:9 aka wide screen
Conference page: {{ep.conf_url}}
{% if not no_releases %}
Released: {{ep.released|yesno:"Yes,No,None"}}
{% endif %}

The video will be posted with the following:

Title: {{ep.name}}
{% if image_url %}
{{MEDIA_URL}}/{{ep.show.client.slug}}/{{ep.show.slug}}/titles/{{ep.slug}}.png
{% endif %}
{% if ep.public_url%}The main page for the video will be here:
{{ep.public_url}}
{% else %}Description: {% if ep.description %}
=== begin ===
{{ep.composed_description}}
=== end description ===
  {% else %} (is blank.) {% endif %}
{% endif %}

{% if no_releases %}
If you do not want your talk video published, contact the event organizers (reply to this email.)
{% endif %}

https://github.com/CarlFK/veyepar/wiki/Recording-Policy
https://github.com/CarlFK/veyepar/wiki/Privacy-Policy
https://github.com/CarlFK/veyepar/wiki/Reviewer#for-presenters

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
        ctx['no_releases'] = self.options.no_releases

        return ctx

    def add_more_options(self, parser):
        parser.add_option('--no-releases',
                action="store_true",
                default=False,
                help="No release info yet.  aka: No Permit.")

        super(email_title, self).add_more_options(parser)


if __name__ == '__main__':
    p=email_title()
    p.main()

