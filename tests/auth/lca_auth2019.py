import os
import json

import scrapy


class LCASpider(scrapy.Spider):
    name = 'LCAsipder'
    start_urls = ['https://lca2019.linux.org.au/dashboard/']

    def parse(self, response):
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'j_username': os.getenv('lca_user'),
                'j_password': os.getenv('lca_pw')
            },
            callback=self.after_login_submit
        )

    def after_login_submit(self, response):
        return scrapy.FormRequest.from_response(
            response,
            callback=self.after_login
        )

    def after_login(self, response):
        return scrapy.http.Request(
            "http://lca2019.linux.org.au/schedule/conference.json",
            callback=self.parse_response
        )

    def parse_response(self, response):
        data = json.loads(response.body.decode('utf-8'))
        for talk in data['schedule']:
            print(talk['contact'])


# pip install scrapy
# scrapy runspider lca_auth.py
