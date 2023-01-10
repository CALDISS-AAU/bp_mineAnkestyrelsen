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

from mineank_funs import text_splitter
from mineank_funs import get_info
from mineank_funs import get_grounds


# Functions
def pdf_reader(pdf):
    
    reader = PdfReader(pdf)
    pages = [page.extract_text() for page in reader.pages]
    pdf_text = '{PB}'.join(pages)
    
    return(pdf_text)


# Paths
data_dir = join(project_p, 'data')
out_p = join(data_dir, 'afgørelser_split-parsed.json')


# Data files
pdf_files = [file for file in os.listdir(data_dir) if file.endswith('.pdf')]

all_files = []

for pdf in pdf_files:
    pdf_dic = {}
    
    file_p = join(data_dir, pdf)
    text_pypdf = pdf_reader(file_p)
    
    pdf_dic['filename'] = pdf
    pdf_dic['text_pypdf'] = text_pypdf
    
    all_files.append(pdf_dic)


# Split into individual case texts
n_total = 227 # der bør være 227 afgørelser i alt

all_cases = []

for file in all_files:
    
    doc_cases = text_splitter(file)

    all_cases = all_cases + doc_cases

print(f'Der mangler {n_total-len(all_cases)} afgørelser') 


# Extract info from cases
for entry in all_cases:
    entry.update(get_info(entry.get('text')))

    case_grounds = get_grounds(entry.get('text'))
    entry['grounds'] = case_grounds


# Save data as JSON
with open(out_p, 'w') as f:
    json.dump(all_cases, f)