#!/usr/bin/python

# email_public.py
# emails the confirmation of the public video to presenters

import itertools
from pprint import pprint

from email_ab import email_ab

class email_url(email_ab):

    ready_state = 7

    subject_template = "[{{ep.show.name}}] Video public: {{ep.name}}"
    body_body = """
Your video has been approved and made public:
    {% for url in urls %} {{url}}
    {% endfor %}

    {% if ep.twitter_url %}
It has also been tweeted: {{ ep.twitter_url }}
    {% endif %}

Please help us promote your talk by retweeting it, blogging it, and sharing it with your networks.

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
        ctx['py_name'] = "email_public.py"

        return ctx


if __name__ == '__main__':
    p=email_public()
    p.main()

