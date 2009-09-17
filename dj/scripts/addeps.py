#!/usr/bin/python

# adds episodes from an external source, like a csv

import datetime 
from csv import DictReader
from datetime import timedelta
from dateutil.parser import parse

from process import process

from main.models import Client, Show, Location, Episode


DJANGOCON_START_DATE = datetime.date(2009, 9, 8)


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
      current_date = DJANGOCON_START_DATE
      last_start = None
      for row in DictReader(open(self.csv_pathname)):
        seq+=1
        print row
# "ID","Talk Title","Speakers","Startime","Endtime","Room","Released"
# "Multnomah/Holladay"
        room=row['Room']
        if room=="Multnomah/Holladay": room="Holladay"

        location,created = Location.objects.get_or_create(
            show=show,name=room,slug=fnify(room))
        name = row['Talk Title'].strip()
    
        # Remove #N from the start of PhOhio talk titles:
        # if name.startswith('#'): name = ' '.join(name.split()[1:])
        start = datetime.time(*map(int, row['Startime'].split(':')))
        end = datetime.time(*map(int, row['Endtime'].split(':')))

        if last_start and last_start > start:
            current_date = current_date + datetime.timedelta(days=1)

        last_start = start

        start_date = datetime.datetime.combine( current_date,start )
        end_date = datetime.datetime.combine( current_date, end)

        ep = Episode(
           sequence=seq,
           location=location, 
           name=name,
           slug=fnify(name),
           primary=row['ID'],
           authors=row['Speakers'], 
           start=start_date, end=end_date,
           state=self.state_done)
        print ep.__dict__
        ep.save()

    def add_more_options(self, parser):
        parser.add_option('-f', '--filename', default="talks.csv",
          help='csv file' )

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
            Location.objects.filter(show=show).delete()
        self.csv_pathname = options.filename
        self.one_show(show)

if __name__ == '__main__':
    p=process_csv()
    p.main()

