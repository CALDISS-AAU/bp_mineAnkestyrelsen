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
from ocr_parse_funs import cases_split

# Paths
data_dir = join(project_p, 'data')
ocr_dir = join(data_dir, 'ocr')
out_p = join(data_dir, 'afgørelser_split-parsed.json')

ocr_files = [file for file in os.listdir(ocr_dir) if file.endswith('all-pages.json')]

# Create combined list of all cases - read, split, add metapagetext
all_cases = []

for file in ocr_files:
    
    # Read OCR scanned pages
    with open(join(ocr_dir, file), 'r') as f:
        doc_pages = json.load(f)
    
    # Get PDF filepath for where pages are from
    pdf_path = join(data_dir, doc_pages[0].get('filename'))

    # Split into cases
    doc_cases = cases_split(doc_pages)

    # Add page with meta as read by pdf-reader (reads CPR better)
    reader = PdfReader(pdf_path)

    for case in doc_cases:
        metapageno = case.get('metadocpageno') - 1

        metapage_text = reader.pages[metapageno].extract_text()

        case['metapage_text'] = metapage_text

    # Add cases to combined list
    all_cases = all_cases + doc_cases


# Check how many missing
n_total = 183 # der bør være 183 afgørelser i alt
print(f'Der mangler {n_total-len(all_cases)} afgørelser')


# Extract info from cases
for entry in all_cases:
    entry.update(get_info_main(entry.get('text')))
    entry.update(get_info_cpr(entry.get('metapage_text')))
    entry.update(get_info_meta(entry.get('meta')))


# Add file counter (acts as ID for missing JNR)
n = 1
prev_filename = ''
for entry in all_cases:
    if entry.get('filename') != prev_filename:
        n = 1
    else:
        n = n + 1
    
    entry['no'] = n

    prev_filename = entry.get('filename')


# Save data as JSON
with open(out_p, 'w') as f:
    json.dump(all_cases, f)