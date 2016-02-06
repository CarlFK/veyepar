#!/usr/bin/python

# email_url.py
# emails the video URL to the presenters

from email_ab import email_ab

class email_url(email_ab):

    ready_state = 7

    subject_template = "[{{ep.show.name}}] Video up: {{ep.name}}" 
    body_body = """
The video of your talk is posted:
    {{url}}
    {% if ep.state == 7 %}
Look at it, make sure the title is spelled right and the audio sounds reasonable.
If you are satisfied, tweet it, blog it, whatever it.  No point in making videos if no one watches them.

To approve it click the Approve button at
    http://veyepar.nextdayvideo.com/main/approve/{{ep.id}}/{{ep.slug}}/{{ep.edit_key}}/  

    As soon as you or someone approves your video, it will be tweeted on @NextDayVideo{% if ep.show.client.tweet_prefix %} tagged {{ep.show.client.tweet_prefix}}{% endif %}.  It will also be sent to the event organizers in hopes that they add it to the event website.  
    {% endif %}
    {% if ep.twitter_url %}
It has been tweeted: {{ ep.twitter_url }} 
Re-tweet it, blog it, whatever it.  No point in making videos if no one watches them.
    {% endif %}
    """ 

    body_ryan = """
Your LCA2016 talk has been published on Youtube:
    {{url}}

    The video will shortly also be available as WebM on the LA mirror at http://mirror.linux.org.au/linux.conf.au/2016/
    
    Please retweet, blog, share the video!

    {% if ep.twitter.url %}
    Your video has already been tweeted at: {{ ep.twitter_url }}
    {% endif %}

    If there are any issues with the video, please reply to this email.

    Thanks,

    LCA2016 AV Video Team
    
    """

    body_body = body_ryan

    py_name = "email_url.py"

    def more_context(self, ep):

        # If there is a Richard (pyvideo) url, use that;
        #  else use the youtube url.
        url = ep.public_url or ep.host_url
        return {'url':url}


if __name__ == '__main__':
    p=email_url()
    p.main()

