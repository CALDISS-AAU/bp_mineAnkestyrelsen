#!/usr/bin/env python
# coding: utf-8

## source
#https://towardsdatascience.com/extracting-text-from-scanned-pdf-using-pytesseract-open-cv-cd670ee38052
#https://pyimagesearch.com/2020/08/03/tesseract-ocr-for-non-english-languages/
## download danish language model from here: https://github.com/tesseract-ocr/tessdata/raw/4.00/dan.traineddata (https://github.com/tesseract-ocr/tessdoc/blob/main/Data-Files.md)
## move to /usr/share/tesseract-ocr/<version>/tessdata

## Requires:
#sudo apt-get install poppler-utils - https://pdf2image.readthedocs.io/en/latest/installation.html
#sudo apt-get install tesseract-ocr

import re
import os
from os.path import join
import json
import sys

import numpy as np
from pdf2image import convert_from_path
import cv2
from PIL import Image
import pytesseract

def page_to_txt(page, docpageno = 1, filename = None):
    """For converting a single page from the pdf to text.

    Args:
        page: single page/image converted from pdf with pdf2image
        docpageno (int, optional): The pagenumber in the original pdf. Defaults to 1.
        filename (str, optional): Filename of the original pdf. Defaults to None.
    """
    # PIL to numpy
    img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

    # Crop
    #img.shape
    main_img = img[:int(img.shape[0]), :int((0.76*img.shape[1]))] # Main text in first 3/4 of the width of document
    meta_img = img[:int(img.shape[0]), int((0.76*img.shape[1])):] # Meta test in last 1/4 of the width of document - blank on pages with no metadata
    bottom_img = img[int((0.9*img.shape[0])):, int((0.7*img.shape[1])):int((0.8*img.shape[1]))] # Page number in bottom right

    # Write to test
    #cv2.imshow('cropped', crop_img)
    #cv2.imwrite('cropped_test.jpg', bottom_img)

    # To text
    main_text = pytesseract.image_to_string(main_img, lang = 'dan') # extract main text
    meta_text = pytesseract.image_to_string(meta_img, lang = 'dan') # extract meta text
    bottom_text = pytesseract.image_to_string(bottom_img, lang = 'eng', config='--psm 10 --oem 3 -c tessedit_char_whitelist=0123456789') # extract pagenumber - the config helps to recognize numbers

    # To data structure
    ## Assign pagenumber
    pageno_regex = re.compile(r'^\d{1,2}\b') # regular expression for pagenumber

    if pageno_regex.match(bottom_text) is None:
        pageno = 0 # pagenumber 0 for pages with no pagenumber
    else:
        pageno = pageno_regex.match(bottom_text).group(0)

    ## Data structure (dictionary)
    page_data = {'main': main_text,
                'meta': meta_text,
                'pageno': pageno,
                'filename': filename,
                'docpageno': docpageno}

    return(page_data)


def comb_case_pages(case_pages):
    """Combines OCR-scanned pages to a single dictionary. Pagenumber for where metadata is located in original document is stored in order to read this information in with another reader (black bars are confusing the OCR).

    Args:
        case_pages (list): List of pages as processed by page_to_text.
    """
    meta = ''.join([page.get('meta') for page in case_pages]) # Meta as one string
    text = '\n'.join([page.get('main') for page in case_pages]) # Text as one large string (no use for keeping it on separate pages)
    metadocpageno = case_pages[0].get('docpageno') # Pagenumber for where metadata is in original document

    # Convert to dictionary
    case_conv = {'meta': meta,
                 'text': text,
                 'metadocpageno': metadocpageno}

    return(case_conv)


def process_pdf(filepath):
    """Processes PDF file from filepath.

    Args:
        filepath: Path to PDF document to process.
    """

    # Convert PDF pages to images (pdf2image)
    pages = convert_from_path(filepath, 500)

    # Filename for document
    filename = filepath.split('/')[-1]

    # List for converted/processed pages
    pages_conv = []

    for c, page in enumerate(pages, start = 1):
        # Process page with page_to_txt function
        page_conv = page_to_txt(page, docpageno = c, filename = filename)

        # Append to list
        pages_conv.append(page_conv)
    

    # Combine processed pages to cases 
    ## List for cases
    cases_conv = []

    ## Starting parameters for loop
    case_pages = [] # List for pages for a case
    prev_page_no = 0 # Starting point for previous page no

    ## Iterate over processed pages
    for i in range(len(pages_conv)):
        
        # Extract current processed page
        current_page = pages_conv[i]
        # Extract pagenumber - used to identify when new case starts
        current_page_no = int(current_page.get('pageno'))
        
        # First page of document is always irrelevant
        if i == 0:

            continue
        
        # Check whether it is the last page and that page is relevant (relevant pages have a page number, except first page in a case. A case is never just one page.)
        if i == max(range(len(pages_conv))) and current_page_no > 0:
            # A case is never just one page
            if len(case_pages) > 1:
                # Append last page to case
                case_pages.append(current_page)
                # Combine case pages with comb_case_pages function
                case_conv = comb_case_pages(case_pages)
                # Append to list of cases
                cases_conv.append(case_conv)
        
        # Check whether page is irrelevant - A new case will start with a page with no pagenumber with the next page having a pagenumber. Other pages with no pagenumbers are appendices
        if current_page_no == 0 and prev_page_no == 0:
            # Replace last entry if case_pages is not empty
            if len(case_pages) > 0:
                case_pages[-1] = current_page
            # Add as first entry of case_pages if empty
            else:
                case_pages.append(current_page)

        # Check for new case - repeated "blank" pagenumbers handled by if-statement above    
        elif current_page_no == 0 and prev_page_no > 0:
            # A case is never just one page
            if len(case_pages) > 1:
                # Combine case pages with comb_case_pages function
                case_conv = comb_case_pages(case_pages)
                # Append to list of cases
                cases_conv.append(case_conv)
                # Start new list of pages for new case
                case_pages = []

            # Add current page to case_pages (new or existing depending on evaluation of if-statement above)
            case_pages.append(current_page)
        
        # Check whether current pagenumber is above previous pagenumber - if so it is still part of the same case
        elif current_page_no > prev_page_no and len(case_pages) > 0:
            # Append to list of cases
            case_pages.append(current_page)

        # Update previous pagenumber
        prev_page_no = current_page_no
    
    return(cases_conv)
