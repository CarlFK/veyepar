#!/bin/bash

# vv - Vocto Veyepar - Easy Bake Video Producer

# This is the top level script that does it all.

# 1. run voctomix
# 2. load data into Veyepar
# 3. launch browser to let user add metadata and tweek cuts
# 4. encode, upload to youtube, email user review/approve URL

ebcnc
python3 adddv.py
firefox http://localhost:8000/main/mk_episode/cnc/
python3 eb.py --poll 30 &&

