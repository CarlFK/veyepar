#!/bin/bash -x

rsync -rtvP --exclude "test_client" ~/Videos/ juser@va.local:Videos/
