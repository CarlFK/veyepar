# ck_shced.py
# check schedule - compairs the html schedule to what is in veyepar

from process import process
from main.models import Client, Show, Episode 

class ck_sched(process):

    def scrape_schedule(self, schedule_html):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(schedule_html)
        sched = soup.find(id="schedule-conference")
        title_spans = sched.find_all('span', class_="title" )
        events = []
        for ts in title_spans:
            ta = ts.find('a')
            text = ta.text
            events.append(text)
    
        return events

    def compare(self, events, eps):
        for ep in eps:
            if ep not in events:
                print("json:", ep) 
                break
        for event in events:
            if event not in eps:
                print("html:", event)
                break
                

    def one_show(self, show):
        if self.options.verbose:  print("show:", show.slug)
        f = open('schedules/pyconca2013.html')
        events = self.scrape_schedule(f)
        print(events[0])
        eps = Episode.objects.filter(show=show)
        eps = [ep.name for ep in eps]
        print(eps[0])
        self.compare(events,eps)
        
        

    def work(self):
        """
        find and process show
        """
        if self.options.client and self.options.show:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(client=client, slug=self.options.show)
            self.one_show(show)

        return

if __name__=='__main__': 
    p=ck_sched()
    p.main()

