qa.markdown - Quality Assurance
-

Spend about a minute on each, except when it is interesting then watch the whole thing - that's the biggest time sink.  Typically about 5% have problems, they take 2-3 min of trying to figure out what is going on, then 5-10 looking at code and stuff trying to figure out how it happened.  I don't expect anyone to look at the code, most of the time the problem is file permissions, encoder libs, disk space, etc.

Examples of problems:

Some are subjective like "poor sound", some are obvious like the title is wrong, or the video is a black background with white text: "INVALID" 

"INVALID" = encoder problem, like corrupted input, encoder process doesn't have read permissions to the input file, or in this case I havn't figured out what the problem is.

Soft sound.  This one is tolerable, but worth looking into putting some effort into making it better.  It has to be pretty bad to be rejected, but it is good for me to be aware of problems like this so I can maybe prevent them in the future. 

Dead air: the talk hasn't started, it sucks to watch the video, you want to fast forward to wherever it should really start.   5 seconds or so is not worth messing with, 30 is.  If you want to figure out where it should start, look at the cut list: some times an extra cut gets left on, so it is a 10 second operation to uncheck the cut, change State from Review to Encode, hit save and wait for the encoder to crunch it.  In a few hours it will be back up for review, and probably just fine.  Don't bother looking for dead air in the middle, it isn't worth the trouble.  Dead air at the end is also anoying, but only 10% of the viewers get that far anyway, so much less of an issue.  Feel free to lave a note in the coment field.  

Wrong or broken title - The vidoes are titled based on the event schedule which typicaly has some last minute changes (presenter doesn't show up so some other talk is put in its place.)  Reject it, notify whoever is managing the veyepar data (Carl) and let them sort it out.  Don't worry if the presenter has altered the title a bit, like re-wording it; close counts.  This is why it is graet to include the introduction "This is Joe talking about Foo."  If you don't have that, then you need to listen to whoever it is speak and try to figure out what they are talking about;  sometimes it isn't obvious.


