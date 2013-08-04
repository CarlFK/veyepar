#!/usr/bin/python

# email_url.py
# emails the video URL to the presenters

from django.core.mail import get_connection, EmailMessage

from process import process
from email_ab import email_ab
from django.conf import settings

class email_url(email_ab):

    ready_state = 7
    subject_template = "{{ep.show.name}} Video up: {{ep.name}}" 
    body_template = """
    The video of your talk is posted:
    {{url}}

    Look at it, make sure the title is spelled right, let me know if it is OK.
    If you are satisfied, tweet it, blog it, whatever it.  No point in making videos if no one watches them.
    
    As soon as you or someone approves your video, it will be tweeted on @NextDayVideo which is what the attendees were told to follow.  It will also be sent to the event organizers in hopes that they add it to the event website.  

    """ 

    def more_context(self, ep):

        # If there is a Richard (pyvideo) url, use that;
        #  else use the youtube url.
        url = ep.public_url or ep.host_url
        return {'url':url}


if __name__ == '__main__':
    p=email_url()
    p.main()

