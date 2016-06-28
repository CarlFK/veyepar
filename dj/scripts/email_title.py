#!/usr/bin/python

# email_url.py
# emails the video URL to the presenters

from django.core.mail import get_connection, EmailMessage

from django.template import Context, Template

from process import process
from email_ab import email_ab
# from django.conf import settings

class email_title(email_ab):

    ready_state = None

    subject_template = '[{{ep.show.name}}] Video metadata for "{{ep.name}}"'

    body_body = """
Please review the following meta data about your talk so that mistakes can be corrected now and not after the video has gone live.

Released: {{ep.released}}
{% if ep.released %}Permission has been given to record your talk and post it online.
{% if not ep.location.active %}However, we are not planning on recording any of the talks in {{ ep.location.name }}.  {% endif %}
{% else %} "None" means it may get recorded and processed, but it will not be made public.
"False" means you have requested for the video not to be released. However the a video may be made anyway and available for review in case you change your mind.  {% endif %}
{% if image_url %}
The video will be titled with the following image:
http://veyepar.{{ep.show.client.bucket_id}}.cdn.nextdayvideo.com/veyepar/{{ep.show.client.slug}}/{{ep.show.slug}}/titles/{{ep.slug}}.png
{% endif %}
{% if ep.public_url%}The main page for the video will be here:
{{ep.public_url}} 
{% else %}Description:
  {% if ep.description%}
    === begin ===
    {{ep.description}} 
    === end description ===
  {% else %}
    (is blank.)
  {% endif %}
{% endif %}
{% if ep.show.schedule_url %}
Problems with the text should be fixed in the event database that drives: {{ep.conf_url}} 
{% endif %}
If everything looks good, you don't need to do anything. Good luck with your talk; expect another email when the video is posted.

Your talk is scheduled for {{ep.start}} in the room called {{ep.location.name}} and you have been allotted {{ep.get_minutes}} minutes. The event organizers will give you instructions on how to check in before your talk.  

"""
    py_name = "email_title.py"
 
    def more_context(self, ep):

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

        return {'image_url':image_url}

        
if __name__ == '__main__':
    p=email_title()
    p.main()

