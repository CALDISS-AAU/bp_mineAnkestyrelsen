#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
from PyPDF2 import PdfReader
import sys

project_p = join('/work', '214477', 'bp_mineAnkest')
modules_p = join(project_p, 'modules')
sys.path.append(modules_p)

from mineank_funs import *
from ocr_parse_funs import cases_split

# Paths
data_dir = join(project_p, 'data')
ocr_dir = join(data_dir, 'ocr')
out_p = join(data_dir, 'afgørelser_split-parsed.json')

ocr_files = [file for file in os.listdir(ocr_dir) if file.endswith('all-pages.json')]

all_metas = []

for file in ocr_files:
    with open(join(ocr_dir, file), 'r') as f:
        pages = json.load(f)
    
    metas = [page.get('meta') for page in pages]

    all_metas = all_metas + metas


all_metas = [clean_text(meta) for meta in all_metas]

jnr_re = re.compile(r'j\.nr\.?\s+([0-9]+\s?.{1,3}\s?[0-9]+)', re.IGNORECASE)

jnr_re = re.compile(r'j.{1,2}nr{1,2}', re.IGNORECASE)

all_jnr = [jnr_re.search(meta).group(0) for meta in all_metas if bool(jnr_re.search(meta))]
# 

#metas = [ocr_file.get('meta')]