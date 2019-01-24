#!/usr/bin/python

# email_conf.py
# emails the confirmation of the public video to presenters

import itertools
from pprint import pprint

from email_ab import email_ab

class email_conf(email_ab):

    ready_state = 12

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
        ctx = super(email_conf, self).context(ep)

        # dig around for URLs that might be relevant
        urls = filter( None,
                [ep.public_url,
                    ep.host_url,
                    ep.archive_ogv_url,
                    ep.archive_mp4_url] )

        ctx['urls'] = urls
        ctx['py_name'] = "email_conf.py"

        return ctx


if __name__ == '__main__':
    p=email_conf()
    p.main()

