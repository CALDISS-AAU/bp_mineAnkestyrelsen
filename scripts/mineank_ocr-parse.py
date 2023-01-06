#!/usr/bin/env python
# coding: utf-8

## source
#https://towardsdatascience.com/extracting-text-from-scanned-pdf-using-pytesseract-open-cv-cd670ee38052


## Requires:
#sudo apt-get install poppler-utils - https://pdf2image.readthedocs.io/en/latest/installation.html
#sudo apt-get install tesseract-ocr

import re
import os
from os.path import join
import json
import sys

from pdf2image import convert_from_path
import cv2
from PIL import Image
import pytesseract


# Paths
project_p = join('/work', '214477', 'bp_mineAnkest')
data_dir = join(project_p, 'data')
#out_p = join(data_dir, 'afgørelser_split-parsed.json')


# Data files
pdf_files = [file for file in os.listdir(data_dir) if file.endswith('.pdf')]


# Test OCR
test_file = pdf_files[0]
test_file_p = join(data_dir, test_file)

subfolder = test_file.split(' ')[0]
os.mkdir(join(data_dir, subfolder))

pdfs = test_file_p
pages = convert_from_path(pdfs, 350)

i = 1
for page in pages:
    image_name = "Page_" + str(i) + ".jpg"  
    page.save(join(data_dir, subfolder, image_name), "JPEG")
    i = i+1     

# function for marking relevant regions
def mark_region(image_path):
    
    im = cv2.imread(image_path)

    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9,9), 0)
    thresh = cv2.adaptiveThreshold(blur,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV,11,30)

    # Dilate to combine adjacent text contours
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
    dilate = cv2.dilate(thresh, kernel, iterations=4)

    # Find contours, highlight text areas, and extract ROIs
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    line_items_coordinates = []
    for c in cnts:
        area = cv2.contourArea(c)
        x,y,w,h = cv2.boundingRect(c)

        if y >= 600 and x <= 1000:
            if area > 10000:
                image = cv2.rectangle(im, (x,y), (2200, y+h), color=(255,0,255), thickness=3)
                line_items_coordinates.append([(x,y), (2200, y+h)])

        if y >= 2400 and x<= 2000:
            image = cv2.rectangle(im, (x,y), (2200, y+h), color=(255,0,255), thickness=3)
            line_items_coordinates.append([(x,y), (2200, y+h)])


    return image, line_items_coordinates

# trying with page 2
image_path = join(data_dir, subfolder, 'Page_3.jpg')

img = cv2.imread(image_path) # read an image

text = pytesseract.image_to_string(img) # extract text
print(text)


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

