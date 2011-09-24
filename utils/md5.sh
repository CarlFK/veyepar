#!/bin/bash -xe

if [ -f index.md5 ]; then
  md5sum --check index.md5
else
  find ./ -type f -exec md5sum {} \; | tee index.md5
fi
