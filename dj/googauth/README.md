This is the code that enables someone from an event to grant access to their YouTube channel.

It uses Google's auth libaries, which I think is safe to assume are sound.

The user starts with these instructions:
https://github.com/CarlFK/veyepar/blob/master/dj/main/templates/show_parameters.html#L24-L32
The user tells Google: Yeah ok.
Google sends a token back via a redirect URL.
The token is used to retrieve some personal info about the user so we know who did it.
All this is saved to a (hopefully) secure loction.
(Currently the local file system.  If an intruder has access to the local file system, game over regardless of how this token is saved, right?)
The user is told to tell someone they have done their part.
https://github.com/CarlFK/veyepar/blob/master/dj/googauth/templates/done.html

Someone reviews the saved token, makes sure it was done by the expected person, and links it to the event.

Later this is used to upload vidoes to the event's YouTube channel.

