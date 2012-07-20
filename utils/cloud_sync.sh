rsync -rtvP -e 'ssh -p 222' --exclude="**.dv" -v --copy-dirlinks  enthought veyepar@nextdayvideo.com:Videos/veyepar/ 
# rsync -rtvP  --exclude="**.dv" -v  --bwlimit=350 vt@71.239.168.206:Videos/veyepar/flourish/ .
