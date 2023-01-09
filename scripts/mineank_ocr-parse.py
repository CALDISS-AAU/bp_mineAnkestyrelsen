#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
import numpy as np
from pdf2image import convert_from_path
import cv2
from PIL import Image
import pytesseract
import sys

project_p = join('/work', '214477', 'bp_mineAnkest')
modules_p = join(project_p, 'modules')
sys.path.append(modules_p)

from ocr_parse_funs import *


# Paths
data_dir = join(project_p, 'data')
ocr_dir = join(data_dir, 'ocr')

if not os.path.isdir(ocr_dir):
    os.mkdir(ocr_dir)

# PDF files
pdf_files = [file for file in os.listdir(data_dir) if file.endswith('.pdf')]

# Proces PDF files

for pdf_file in pdf_files:
    
    outfile = f'{pdf_file.split(" ")[0]}_split-ocr.json'
    out_p = join(ocr_dir, outfile)
    
    pdf_path = join(data_dir, pdf_file)

    pdf_processed = process_pdf(pdf_path)

    with open(out_p, 'w') as f:
        json.dump(pdf_processed)

# Split into individual case texts
#n_total = 227 # der bør være 227 afgørelser i alt

#all_cases = []