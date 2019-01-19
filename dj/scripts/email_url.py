#!/usr/bin/python

# email_url.py
# emails the video URL to the presenters

import itertools
from pprint import pprint

from email_ab import email_ab

class email_url(email_ab):

    ready_state = 7

    subject_template = "[{{ep.show.name}}] Video up: {{ep.name}}"
    body_body = """
Your video has been uploaded but it has not been made public:
    {% for url in urls %} {{url}}
    {% endfor %}
It will be made public once the video is approved.  To do this yourself, please check for the following:
    - The title is spelled correctly
    - The start and end cuts at the correct time
    - The audio sounds reasonable

If you're satisfied, click the 'Approve' button at
   {{ep.approve_url}}

Then feel free to tweet it, blog it, and share it with your networks.

As soon as either you or the AV team approves your video, it will be tweeted on @NextDayVideo{% if ep.show.client.tweet_prefix %} tagged {{ep.show.client.tweet_prefix}}{% endif %}.  It will also be sent to the event organizers to add to the event website.
    """


    def context(self, ep):
        ctx = super(email_url, self).context(ep)

        # dig around for URLs that might be relevant
        urls = filter( None,
                [ep.public_url,
                    ep.host_url,
                    ep.archive_ogv_url,
                    ep.archive_mp4_url] )

        ctx['urls'] = urls
        ctx['py_name'] = "email_url.py"

        return ctx


if __name__ == '__main__':
    p=email_url()
    p.main()

