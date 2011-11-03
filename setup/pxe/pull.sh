#!/bin/bash -x

rsync --files-from pxe-files.txt root@shaz:/ srv

