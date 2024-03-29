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
  {% else %} (is blank.)
  {% endif %}
{% endif %}
{% if no_releases %}
If you do not want your talk video published, contact the event organizers (reply to this email.)
{% else %}
Released: "{{ep.released|yesno:"Yes,No,None"}}" means:
Yes: Permission has been given to record your talk and post it online.  Once it is up, you will get another e-mail with a URL that is not public until someone approves it.  Once it's approved it will be made public and tweeted {{ep.show.client.tweet_prefix}} {{ep.twitter_id}}.
No: You have requested for the video not to be released. This request will be honored.  However the a video may be produced and available for review in case you change your mind.  If you need to be absolutely sure, at the event you can ask to have the camera turned off.
None: Permission to publish a video of this talk is unknown.  This means it may get recorded and processed, but it will not be made public and we will send another email asking for permission.  Please reply to this email stating your preference.
{% if not ep.location.active %}However, we are not planning on recording any of the talks in {{ ep.location.name }}.  {% endif %}
{% if not ep.reviewers %}
If you would like someone to double check your video, (mostly for technical defects, see https://github.com/CarlFK/veyepar/wiki/Reviewer) hit reply, add a name and email to the top, hit send.  They will then get CCed when your video is ready for review.
{% endif %}
{% endif %}

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

