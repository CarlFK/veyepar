#!/usr/bin/python

# adds episodes from an external source, like a csv

from csv import DictReader
from datetime import timedelta
from dateutil.parser import parse

from process import process

from main.models import Client, Show, Location, Episode

def fnify(text):
    """
    file_name_ify - make a file name out of text, like a talk title.
    convert spaces to _, remove junk like # and quotes.
    like slugify, but more file name friendly.
    """
    fn = text.replace(' ','_')
    fn = ''.join([c for c in fn if c.isalpha() or c.isdigit() or (c in '_') ])
    return fn


class process_csv(process):
   
    state_done=2

    def one_show(self, show):
      seq=0
      for row in DictReader(open(self.csv_pathname)):
        seq+=1
        print row

        location,created = Location.objects.get_or_create(
            show=show,name=row['room'],slug=fnify(row['room']))
        name = row['title'] 
    
        # Remove #N from the start of PhOhio talk titles:
        # if name.startswith('#'): name = ' '.join(name.split()[1:])

        dt = row['date']+' '+ row['time']
        start=parse(dt)
        minutes = int(row['min'])
        end=start+timedelta(minutes=minutes)

        ep = Episode(
           sequence=seq,
           location=location, 
           name=name,
           slug=fnify(name),
           primary=row['id'],
           authors=row['presenters'], 
           start=start, end=end,
           state=self.state_done
            )
        ep.save()

    def add_more_options(self, parser):
        parser.add_option('-f', '--filename', default="sched.csv",
          help='csv file' )
        parser.add_option('--whack', action="store_true", 
          help="whack current episodes, use with care." )

    def main(self):
      options, args = self.parse_args()

      if options.list:
        for client in Client.objects.all():
            print "\nName: %s  Slug: %s" %( client.name, client.slug )
            for show in Show.objects.filter(client=client):
                print "\tName: %s  Slug: %s" %( show.name, show.slug )
                print "\t--client %s --show %s" %( client.slug, show.slug )
      elif options.client and options.show:
        client,created = Client.objects.get_or_create(
            name=options.client, slug=options.client)
        show,created = Show.objects.get_or_create(client=client,
            name=options.show, slug=options.show)
        if options.whack:
# clear out previous runs for this show
            Episode.objects.filter(location__show=show).delete()
            # Location.objects.filter(show=show).delete()
        self.csv_pathname = options.filename
        self.one_show(show)

if __name__ == '__main__':
    p=process_csv()
    p.main()

