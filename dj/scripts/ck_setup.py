#!/usr/bin/python

# ck_setup.py - checks the veyepar setup - reports what features are ready.

from process import process

from main.models import Show, Location, Client

import pw
import rax_uploader

import os
import xml.etree.ElementTree

class ck_setup(process):

    client=None
    show=None

    def ck_pw(self,service,id_field):

        key = getattr(self.client, id_field)

        print 'checking client and pw.py - key:"{}" in:"{}"'.format(
                key,service)

        try: 
            creds = getattr(pw, service)
        except AttributeError as e:
            # 'module' object has no attribute 'foo'
            print "pw.py does not have:", service
            raise e

        keys = creds.keys()
        print "keys for service {}: {}".format( service, keys )

        if not id:
            print '{} is blank'.format(id_field)
            raise AttributeError
        elif key in keys:
            print 'key "{}" found in keys.'.format(key)
        else:
            print 'key "{}" NOT found in keys.'.format(key)
            raise AttributeError

    
    def ck_client(self):
        try:
            client_slug = self.options.client
        except AttributeError as e:
            print "No client set in config file or command line."
            raise e
        print "client_slug:", client_slug

        try:
            self.client = Client.objects.get(slug=client_slug)
        except Client.DoesNotExist as e:
            print "client slug not found in db."
            raise e

        return 

    def ck_show(self):
        try:
            show_slug = self.options.show
        except AttributeError as e:
            print "No show set in config file or command line."
            raise e
        print "show_slug:", show_slug

        try:
            self.show = Show.objects.get(slug=show_slug)
        except Show.DoesNotExist as e:
            print "show slug not found in db."
            raise e

        return 

    def ck_dir(self):
        if os.path.exists(self.show_dir):
            print("~/Videos/showdir exits: {}".format(self.show_dir))
        else:
            print("~/Videos/showdir not created yet.  run mk_dirs.py")


    def ck_title(self):

        title_svg = self.client.title_svg
        if title_svg:
            print('show.title_svg: {}'.format(title_svg))
        else:
            print('show.title_svg is blank. using <show.slug>_title.svg')
            title_svg = "%s_title.svg" % (self.show.slug,)
        title_svg = os.path.join(self.show_dir, "bling", title_svg)
        print title_svg
        if not os.path.exists(title_svg):
            print("title_svg not found.")

        raw_svg=open(title_svg).read()
        tree=xml.etree.ElementTree.XMLID(raw_svg)
        keys = [ 'client',
            'show',
            'title',
            'title2',
            'tag1',
            'authors', 'presenternames',
            'presentertitle',
            'date',
            'time',
            'license', ]
        print("checking title_svg for object IDs, found:")
        for key in keys:
            if tree[1].has_key(key):
                print(key,tree[1][key].text)


    def ck_cdn(self):
        if self.client.rax_id:
            rax_id = self.client.rax_id
            print "client.rax_id:", rax_id
        else:
            print "client.rax_id not set."

        if self.client.bucket_id:
            bucket_id = self.client.bucket_id
            print "client.bucket_id:", bucket_id
        else:
            print "client.bucket_id not set."
            return

        print "checking for valid bucket..."
        cf = rax_uploader.auth(rax_id)
        containers = cf.get_all_containers()
        container_names = [container.name for container in containers]
        print "container_names", container_names
        if bucket_id in container_names:
            print('"{}" found.'.format(bucket_id))
        else:
            print('"{}" not found.'.format(bucket_id))
            raise

        container = cf.get_container(bucket_id)


    def work(self):
        """
        what has happened so far:
        files=config.read(['veyepar.cfg','~/veyepar.cfg'
        self.options, self.args = parser.parse_args()
        """

        try:
            self.ck_client()
            self.ck_show()
            self.set_dirs(self.show)

            self.ck_dir()
            self.ck_title()
            self.ck_pw("rax","rax_id")
            self.ck_cdn()

        except Exception as e:
            print "tests stopped at"
            print e.message 
            raise e
            #  import code; code.interact(local=locals())

        return 

if __name__ == '__main__':
    p=ck_setup()
    p.main()

