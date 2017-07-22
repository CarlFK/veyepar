#!/usr/bin/python

# email_url.py
# emails the video URL to the presenters

from django.core.mail import get_connection, EmailMessage

from django.template import Context, Template

from process import process
from post_yt import post
from email_ab import email_ab
# from django.conf import settings

class email_title(email_ab):

    ready_state = None

    subject_template = '[{{ep.show.name}}] how to enter: *missing* metadata for "{{ep.name}}"'

    body_body = """Dear PyOhio presenter,

It's me and my robot again!

There are now twiter and rewviewer fields in your PyOhio Speaker profile page.  Please enter it there, even if you have already emailed it to me.

https://pyohio.org/speaker/edit/

Sorry for the noise, the changes just hit production a few min ago.

Also, I need 3 bonus rewviewers for the Opening and two Lighting Talk videos. Lighting talks will have some extra work:   Once they are over, email me a list of Names and Talk titles (I suggest getting your hands on the signup sheet before someone throws it out.)   Let me know if you are up for this and you get extra thanks.

For those of you that missed the first blurt, keep reading.  The rest of you can stop now.   Thanks!


I need two more datas from you: twitter handle and reviewer email address.

Twitter I assume you understand, and if you don’t twitter just skip it.

Reviewer will need some explanation:

To help process videos I have a new feature that requires a little data from you:
pick someone to be given the chance to review your video as soon as it is available.

If they don’t, oh well, we tried.   So don’t fret too much over reliability, and given how late in the game we are, I wouldn’t even bother asking them – just pick a person and get their email address added to the  PyOhio conference database.   (It is unclear today how that will happen, give us 24 hours to figure that out.)

If they do, then your video will be released to the public sooner than waiting for me.

They will also be given the pre-show email that you will get showing the title slide, one more set of eyes who should have some idea what your talk is about and may catch problems earlier than later.

You can fwd this message and here is more description
https://github.com/CarlFK/veyepar/wiki/Reviewer

Sorry for the extra spam this year, next year will be different ;)

Carl
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

        p = post()
        description = p.construct_description(ep)

        ctx['description'] = description
        ctx['image_url'] = image_url
        ctx['py_name'] = "email_rfd.py"

        return ctx

if __name__ == '__main__':
    p=email_title()
    p.main()

