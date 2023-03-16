#!/usr/bin/python

from datetime import datetime
from pprint import pprint

from process import process

class Easy_Bake(process):

 ready_state = 2

 def encode(self, episode):
  import enc
  p=enc.enc()
  p.process_ep(self,episode)

 def post_yt(self, episode):
  import post_yt
  p=post_yt.post()
  p.process_ep(self,episode)

 def email_url(self, episode):
  import email_url
  p=email_url.email_url()
  p.process_ep(self,episode)


 def process_ep(self, episode):

    self.encode()
    self.post_yt()
    self.email_url()
    episode.state=8
    episode.save()

if __name__=='__main__':
    eb = Easy_Bake()
    eb.main()

