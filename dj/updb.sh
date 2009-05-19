./manage.py  dumpdata --settings dj.settings >vp.json 
rm vp.db 
./manage.py syncdb --noinput
./manage.py  loaddata vp.json 
