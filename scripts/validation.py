#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
from PyPDF2 import PdfReader
import sys
import pandas as pd

project_p = join('/work', '214477', 'bp_mineAnkest')
modules_p = join(project_p, 'modules')
sys.path.append(modules_p)

from mineank_funs import *
from ocr_parse_funs import cases_split

# Paths
data_dir = join(project_p, 'data')
ocr_dir = join(data_dir, 'ocr')
data_all_p = join(data_dir, 'afgørelser_split-parsed.json')

ocr_files = [file for file in os.listdir(ocr_dir) if file.endswith('all-pages.json')]

jnr_re = re.compile(r'j\.nr\.?\s+([0-9]+\s?.{1,3}\s?[0-9]+)', re.IGNORECASE)

all_jnr = []

for file in ocr_files:
    with open(join(ocr_dir, file), 'r') as f:
        pages = json.load(f)
    
    filename = pages[0].get('filename')

    metas = [page.get('meta') for page in pages]

    for meta in metas:
        txt = clean_text(meta)

        if jnr_re.search(txt):

            info = {'filename': filename,
                    'jnr': jnr_re.search(txt).group(1)}
            
            all_jnr.append(info)


# data frames
all_jnr_df = pd.DataFrame.from_records(all_jnr)

data_df = pd.read_json(data_all_p, orient = 'records')
data_df = data_df[['filename', 'jnr']]

# Identify what values are in TableB and not in TableA
key_diff = set(all_jnr_df.jnr).difference(data_df.jnr)

missing_jnr = all_jnr_df.loc[all_jnr_df['jnr'].isin(key_diff) & (all_jnr_df['jnr'] != '22-40320'), :] # 22-40320 er sagsnummer for forskerens aktindsigt
if missing_jnr.shape[0] == 0:
    print('All J.nr. included')
else:
    print(f'{missing_jnr.shape[0]} j.nr missing')