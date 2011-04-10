#!/bin/bash -x


# http://www.blip.tv/?cmd=delete&s=file&id=(long)&reason=(string)&skin=api 

# cmd=delete&s=file&id=(long)&reason=(string)&skin=api 


curl -s "http://blip.tv/dashboard/episode_detailed/4840010?users_id=613931&userlogin=veyepar_test&password=bdff6680&skin=json" 
curl -s "http://blip.tv/dashboard/episode_detailed/4840010?users_id=613931&password=bdff6680&skin=json" 

exit

curl -s "http://blip.tv/dashboard/episode_detailed/4840010?users_id=613931&skin=json&userlogin=veyepar_test&password=bdff6680" | grep -A 1 8907864
curl -s --cookie kookie "http://www.blip.tv/?userlogin=veyepar_test&password=bdff6680&section=posts&cmd=delete&id=8907864&reason=%28string%29&users_id=613931&skin=json"
exit

# curl -s --cookie-jar kookie "http://blip.tv/" \

curl -s 'http://podalaya.blip.tv/upload?session=613931BLIP29711342&skin=json' \
-F file4_id=9104580 \
-F file4_del=1 \
-F id=4836207 \
-F interactive_post=1 \
-F new_dashboard=1 \
-F otter_auth=3GQDFrvK47Yhw46G7I2m9w9P9BLIPk68 \
-F userlogin=veyepar_test \
-F password=bdff6680 \
-F categories_id=7 \
-F skin=json 
exit


curl --cookie kookie "http://www.blip.tv/?cmd=delete&s=file&section=file&item_id=9104580&reason=test&skin=json"


exit
otter_auth=3pjGIlNVq596F7ny15F19I59qBLIPpbwr
sBjDFtYNMc6o8ecqEi71K18SPBLIPpbwr
sBjDFtYNMc6o8ecqEi71K18SPBLIPpbwr

curl --cookie kookie "http://www.blip.tv/?cmd=delete&s=file&section=file&id=9104580&item_id=9104580&reason=test&userlogin=veyepar_test&password=bdff6680&skin=json"

exit


exit

curl http://blip.tv \
-F section=file \
-F cmd=delete \
-F reason=test \
-F id=9104580 \
-F userlogin=veyepar_test \
-F password=bdff6680 \
-F skin=json 

exit

curl http://blip.tv \
-F cmd=delete \
-F s=file \
-F users_id=613931 \
-F id="9104580" \
-F userlogin=veyepar_test \
-F password=bdff6680 \
-F skin=json \
-F reason=test
