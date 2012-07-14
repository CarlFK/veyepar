#!/bin/bash -x

rsync -rtvP --exclude "test_client" ~/Videos vt@vfs.local:Videos/
