
Summary: 

yt_service.ProgrammaticLogin() fails on some boxes but not others.  I can't figure out what's different.

I think it is the same problem here:
https://groups.google.com/forum/?fromgroups#!topic/youtube-api-gdata/_E93pqoWOt0

clue:
"Info=WebLoginRequired"
I get that on the Next Day Video account, 
but not my personal cfkarsten account.

my test files:
https://github.com/CarlFK/veyepar/tree/master/tests/you_tube

to run test:

install gdata:
make a virtualenv, activate it (or use a test box, whatever)
wget http://gdata-python-client.googlecode.com/files/gdata-2.0.17.tar.gz
tar xvf gdata-2.0.17.tar.gz
cd gdata-2.0.17
python setup.py install

get goog_auth.py:
git clone git://github.com/CarlFK/veyepar.git
cd veyepar/tests/you_tube/
cp goog_auth_sample_pw.py goog_auth_pw.py
edit, fill in your user/pw

python goog_auth.py 

should see:
 <gdata.youtube.service.YouTubeService object at 0x1079ed0>

not:
  raise BadAuthentication, 'Incorrect username or password'
