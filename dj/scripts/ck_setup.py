#!/usr/bin/python

# ck_setup.py - checks the veyepar setup - reports what features are ready.

from process import process

from main.models import Show, Location, Client

from django.conf import settings

from django.template.defaultfilters import slugify

import pw

import rax_uploader
import archive_uploader
import steve.richardapi

import os
import xml.etree.ElementTree
import requests

# from the blender build scripts
# https://svn.blender.org/svnroot/bf-blender/trunk/blender/build_files/scons/tools/bcolors.py

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def p_print(text):
    print(text)
    return 

def p_okg(text):
    print((bcolors.OKGREEN + text +bcolors.ENDC))
    return 

def p_warn(text):
    print((bcolors.WARNING + text +bcolors.ENDC))
    return 

def p_fail(text):
    print((bcolors.FAIL + text +bcolors.ENDC))
    return 

class ck_setup(process):

    client=None
    show=None

    def ck_pw(self,
            service,
            client_id_field=None,
            cred_keys=[]):

        try: 
            creds = getattr(pw, service)
        except AttributeError as e:
            # 'module' object has no attribute 'foo'
            p_fail('pw.py does not have: "{}"'.format(service))
            return False

        keys = list(creds.keys())
        print("keys for service {}: {}".format( service, keys ))

        key = getattr(self.client, client_id_field, None)

        # import code; code.interact(local=locals())

        print('checking client.{} & pw.py for "{}" in: "{}={{..."'.format(
                client_id_field,key,service))

        if not key:
            p_warn('client.{} is blank'.format(client_id_field))
            return False
        elif key in keys:
            p_okg('key "{}" found in "{}" keys.'.format(key,service))
        else:
            p_warn('key "{}" not found in "{}" keys.'.format(key,service))
            raise AttributeError

        secrets = creds[key]
        # try not to display secret values
        print(('names of secrets in pw.py {}:{}'.format( 
            key, list(secrets.keys()) )))
        print(('checking for existance of {}'.format(cred_keys)))
        for cred_key in cred_keys:
            if cred_key not in secrets:
                p_warn('"{}" NOT found.'.format(cred_key))

        return secrets

    
    def ck_client(self):
        try:
            client_slug = self.options.client
        except AttributeError as e:
            p_fail("No client set in config file or command line.")
            raise e
        p_okg("client_slug: {}".format(client_slug))

        try:
            self.client = Client.objects.get(slug=client_slug)
        except Client.DoesNotExist as e:
            p_fail("client slug not found in db.")
            raise e

        return 

    def ck_show(self):
        try:
            show_slug = self.options.show
        except AttributeError as e:
            p_fail("No show set in config file or command line.")
            raise e
        p_okg("show_slug: {}".format(show_slug))

        try:
            self.show = Show.objects.get(slug=show_slug)
        except Show.DoesNotExist as e:
            p_fail( "show slug not found in db." )
            raise e

        return 

    def ck_dir(self):
        if os.path.exists(self.show_dir):
            print(("~/Videos/showdir exits: {}".format(self.show_dir)))
        else:
            # print(bcolors.FAIL + "~/Videos/showdir not created yet.  run mk_dirs.py"+bcolors.ENDC)
            p_fail("~/Videos/showdir not created yet.  run mk_dirs.py")


    def ck_title(self):

        title_svg = self.client.title_svg
        print(('client.title_svg: {}'.format(title_svg)))
        title_svg = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "bling", 
                title_svg)
        p_okg(title_svg)
        if not os.path.exists(title_svg):
            p_fail("title_svg not found.")

        raw_svg=open(title_svg).read()
        tree=xml.etree.ElementTree.XMLID(raw_svg)
        keys = [ 'client',
            'show',
            'title',
            'title2',
            'tag1',
            'presenternames',  # authors
            'presentertitle',
            'twitter_id',
            'date',
            'time',
            'room',
            'license', ]
        print(("checking title_svg for object IDs: {}".format(keys) ))
        print("found:")
        found=[]
        for key in keys:
            if key in tree[1]:
                found.append(key)
                print((key,tree[1][key].text))
        if not found:
            p_warn("no keys found in {}".format(title_svg))

    def ck_mlt(self):

        mlt = self.client.template_mlt
        print(('client.template_mlt: {}'.format(mlt)))

        if not mlt:
            p_fail("client.template_mlt not set.")

        mlt = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                mlt)
        p_okg(mlt)
        if not os.path.exists(mlt):
            p_fail("mlt not found.")

    def ck_foot(self):

        credits_img = self.client.credits

        if not credits_img:
            p_fail("client.credits not set.")

        credits_img =  os.path.join(
                self.show_dir,
                "assets", 
                 credits_img)

        if not os.path.exists(credits_img):
            p_fail("credits_img not found: {}".format(credits_img))
 
        p_okg("credits: {}".format(self.client.credits))

    def ck_email(self):
        if self.client.contacts:
            p_okg("client.contacts: {}".format(self.client.contacts))
        else:
            p_warn("client.contacts: blank")

        try:
            p_okg("sender: {}".format(settings.EMAIL_SENDER))
            # some of these are needed:
            """
            EMAIL_USE_TLS 
            EMAIL_HOST
            EMAIL_PORT
            EMAIL_HOST_USER
            EMAIL_HOST_PASSWORD
            """
        except AttributeError as e:
            p_warn("settings.EMAIL_SENDER not set.")

    def ck_richard(self, secrets):

        category_key = self.client.category_key
        if category_key:
            p_print("client.category_key: {}".format(category_key))
        else: 
            p_warn("client.category_key not set.")
            return False

        print("checking for category...")
        endpoint = "http://{}/api/v2/".format( secrets['host'] )

        """
        print(endpoint)

        try: 
            category = steve.richardapi.get_category(endpoint, category_key)
            print("category: {}".format(category) )
        except steve.richardapi.DoesNotExist:
            print("category: {} not found".format(category_key) )


        category_slug = slugify(category_key)
        try: 
            category = steve.richardapi.get_category(
                    endpoint, category_slug)
            print("category: {}".format(category) )
        except steve.richardapi.DoesNotExist:
            print("category slug: {} not found".format(category_slug) )
        """

        categories = steve.richardapi.get_all_categories(endpoint)
        cat_titles = [cat['title'] for cat in categories]
        print(("found {} categories. last 5: {}".format(
            len(categories), cat_titles[-5:] )))
        if category_key in cat_titles:
            p_okg('client.category_key:"{}" found.'.format(category_key))
        else:
            p_fail('client.category_key:"{}" NOT found.'.format(category_key))
        return 

    def ck_cdn(self, secrets):
        if self.client.rax_id:
            rax_id = self.client.rax_id
            p_okg("client.rax_id: {}".format(rax_id))
        else:
            p_warn("client.rax_id not set.")
            return 

        if self.client.bucket_id:
            bucket_id = self.client.bucket_id
            p_okg("client.bucket_id: {}".format(bucket_id))
        else:
            p_fail("client.bucket_id not set.")

        print("checking for valid bucket...")
        cf = rax_uploader.auth(rax_id)
        containers = cf.get_all_containers()
        container_names = [container.name for container in containers]
        print("container_names", container_names)
        if bucket_id in container_names:
            p_okg('"{}" found.'.format(bucket_id))
        else:
            p_fail('"{}" not found.'.format(bucket_id))

        # not sure what to do with this...
        # container = cf.get_container(bucket_id)
        return

    def ck_archive(self, secrets):
        if self.client.archive_id:
            archive_id = self.client.archive_id
            p_okg("client.archive_id: {}".format(archive_id))
        else:
            p_warn("client.archive_id not set.")
            return 

        if self.client.bucket_id:
            bucket_id = self.client.bucket_id
            p_okg("client.bucket_id: {}".format(bucket_id))
        else:
            p_fail("client.bucket_id not set.")

        print("auth...")
        service = archive_uploader.auth(archive_id)

        print("checking for valid bucket...")
        buckets = service.get_all_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        print("bucket_names", bucket_names)
        if bucket_id in bucket_names:
            p_okg('"{}" found.'.format(bucket_id))
        else:
            p_fail('"{}" not found.'.format(bucket_id))
            p_fail('Either create it or set client.bucket_id to one of the above.')

        bucket = service.get_bucket(bucket_id,headers={})
        # not sure what to do with this...
        # container = cf.get_container(bucket_id)
        return


    def ck_youtube(self, secrets):
        ret = True
        print("looking for client_secrets.json...")
        if not os.path.exists('client_secrets.json'):
            p_fail("client_secrets.json NOT found.")
            ret = False
        print(("looking for {}".format(secrets['filename'])))
        if not os.path.exists(secrets['filename']):
            p_fail("{} NOT found.".format(secrets['filename']))
            ret = False

        return ret

    def ck_schedule_api(self):
        schedule_url = self.show.schedule_url
        if schedule_url:
            p_okg("show.schedule_url: {}".format(schedule_url))
        else:
            p_warn("no show.schedule_url")
            return 

        if schedule_url.startswith('file'):
            url = schedule_url[7:]
            if not os.path.exists(url):
                print(("{} NOT found.".format(url)))
        else:
            print("getting...")
            session = requests.session()
            response = session.get(schedule_url, verify=False)
            text = response.text
            print(text[:75])

        auth = pw.addeps.get(self.show.slug, None)
        if auth is not None:
            print(("found in pw.addeps:{}".format(list(auth.keys()))))


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
            self.ck_foot()
            self.ck_mlt()

            self.ck_schedule_api()

            # email uses local_settings.py
            # self.ck_pw("smtp","email_id")
            self.ck_email()

            secrets = self.ck_pw( "richard","richard_id",
                    ['host', 'api_key', ])
            if secrets:
                self.ck_richard(secrets)

            secrets = self.ck_pw("rax","rax_id",['api_key', 'user'])
            if secrets:
                self.ck_cdn(secrets)

            secrets = self.ck_pw( "yt","youtube_id",['filename', ])
            if secrets:
                self.ck_youtube(secrets)

            secrets = self.ck_pw( "archive","archive_id",['access','secret'])
            if secrets:
                self.ck_archive(secrets)


        except Exception as e:
            print("tests stopped at")
            print(e.message) 
            print(e.__class__, e)
            # import code; code.interact(local=locals())
            # raise e

        return 

if __name__ == '__main__':
    p=ck_setup()
    p.main()

