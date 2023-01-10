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

from mineank_funs import get_info_main
from mineank_funs import get_info_cpr
from mineank_funs import get_info_meta
from mineank_funs import get_grounds

# Paths
data_dir = join(project_p, 'data')
ocr_dir = join(data_dir, 'ocr')
out_p = join(data_dir, 'afgørelser_split-extracted.json')

ocr_files = [file for file in os.listdir(ocr_dir) if file.endswith('.json')]

# Read cases to combined list
n_total = 227 # der bør være 227 afgørelser i alt

all_cases = []

for file in ocr_files:
    
    with open(join(ocr_dir, file), 'r') as f:
        doc_cases = json.load(f)

    all_cases = all_cases + doc_cases

print(f'Der mangler {n_total-len(all_cases)} afgørelser')

# Extract info from cases
for entry in all_cases:
    entry.update(get_info_main(entry.get('text')))
    entry.update(get_info_cpr(entry.get('metapage_text')))
    entry.update(get_info_meta(entry.get('meta')))

    case_grounds = get_grounds(entry.get('text'))
    entry['grounds'] = case_grounds


# Save data as JSON
with open(out_p, 'w') as f:
    json.dump(all_cases, f)