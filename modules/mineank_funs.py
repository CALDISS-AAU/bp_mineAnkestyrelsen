#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
import unicodedata

def is_pua(c): #https://stackoverflow.com/questions/56337705/removing-all-invalid-characters-e-g-uf0b7-from-text
    """
    Detecting invalid unicode characters. Returns bool.
    """
    
    return unicodedata.category(c) in ['Co', 'Cc', 'Cf', 'Cs', 'Co', 'Cn']

def text_splitter(file):
    """
    Split document to individual cases. Returns list of strings (one string per case).
    """

    #pattern = re.compile(r'\s{0,5}\n(?=\s{0,4}Ankestyrelsen\s{0,4}\n)', re.DOTALL)
    #pattern = re.compile(r'\s{0,5}\n\s{0,5}A ?n ?k ?e ?s ?t ?y ?r ?e ?l ?s ?e ?n ?\s{0,5}\n\s{0,5}(?!.{0,2}7998)', re.DOTALL)
    pattern = re.compile(r'{PB}(?=.{0,1000}A\s?f\s?g\s?ø\s?r\s?e\s?l\s?s\s?e\s?r?\s{0,5}\n\s{0,5}D\s?u\s? \s?h\s?a\s?r\s? \s?k\s?l\s?a\s?g\s?e\s?t\s? \s?o\s?v\s?e\s?r\s?)', re.DOTALL)
    pattern_replace = re.compile(r'(?<=\n)G\'(?=\s)')
    num_sq_replace = re.compile(r'\[\s?\d\s?\]')
    
    doc_text = file.get('text_pypdf')
    text_strip = doc_text.replace('\n', '{LINJESKIFT}')
    text_strip = ''.join(c for c in text_strip if not is_pua(c))
    text_strip = text_strip.replace('{LINJESKIFT}', '\n')
    text_strip = text_strip.replace('{PB}', '\n')
    text_strip = re.sub(pattern_replace, '', text_strip)
    text_strip = re.sub(num_sq_replace, ' ', text_strip)
    text_strip = text_strip.replace('  ', ' ')
    text_strip = text_strip.replace(' -', '-')
    text_strip = text_strip.replace('- ', '-')
    
    
    texts_split = pattern.split(text_strip)
    texts_split.pop(0) # første fundet tekst altid overflødig
    
    texts_return = []
    n = 1
    for text in texts_split:
        if len(text) < 200:
            continue
        
        text_returndict = {'filename': file.get('filename'),
                           'text': text,
                           'n': n,
                           'doc_text': file.get('text_pdfminer')}
        
        texts_return.append(text_returndict)
        
        n = n + 1
    
    return(texts_return)

def clean_text(text):

    # regexes
    pattern_replace = re.compile(r'(?<=\n)G\'(?=\s)')
    num_sq_replace = re.compile(r'\[\s?\d\s?\]')

    text_strip = text.replace('\n', '{LINJESKIFT}')
    text_strip = ''.join(c for c in text_strip if not is_pua(c))
    text_strip = text_strip.replace('{LINJESKIFT}', '\n')
    text_strip = re.sub(pattern_replace, '', text_strip)
    text_strip = re.sub(num_sq_replace, ' ', text_strip)
    text_strip = text_strip.replace('  ', ' ')
    text_strip = text_strip.replace('—', '-')
    text_strip = text_strip.replace(' -', '-')
    text_strip = text_strip.replace('- ', '-')
    text_strip = text_strip.replace('-\n', '')
    
    return(text_strip)


def get_info_meta(text):
    """
    Extract info from meta information in case document (right margin on first page)
    """

    # regexes
    jnr_re = re.compile(r'j\.nr\.?\s+([0-9]+\s?[-—]\s?[0-9]+)', re.IGNORECASE)
    date_re = re.compile(r'(?<=\n)\d{1,2}\..{0,3}\w{3,10}\s?\d{4}')

    text = clean_text(text)

    info_dict = {}

    try:
        jnr = jnr_re.search(text).group(1)
    except:
        jnr = 'not found'

    try:
        date = date_re.search(text).group(0)
    except:
        date = 'not found'

    info_dict['jnr'] = jnr
    info_dict['date'] = date
    
    return(info_dict)


def get_info_cpr(text):
    """
    Extract CPR info from case document.
    """

    # regexes
    cpr_re = re.compile(r'\nCpr\.\s?nr\.\s+(\d+)\s+(\d+)', re.IGNORECASE)

    text = clean_text(text)

    info_dict = {}

    try:
        birthyear = cpr_re.search(text).group(1)
        if int(birthyear) > 21:
            birthyear = '19' + birthyear
        else:
            birthyear = '20' + birthyear
        
    except:
        birthyear = 'not found'
        
    try:
        gender = cpr_re.search(text).group(2)
        
        if int(gender) % 2 == 0:
            gender = 'female'
        else:
            gender = 'male' 
    except:
        gender = 'not found'

    info_dict['birthyear'] = birthyear
    info_dict['gender'] = gender

    return(info_dict)


def get_info_main(text):
    """
    Extract info from main text in case document, including grounds.
    """
    
    # regexes
    kommune_re = re.compile(r'Du har klaget over ([a-zæøå]+(?:\-[a-zæøå]+)?)\s\s?[K]\w+', re.IGNORECASE) # kommunenavn
    caseworker_re = re.compile(r'venlig hilsen\s{1,5}([a-zæøå]+\s[a-zæøå]+(\s[a-zæøå]+)?)', re.IGNORECASE) # sagsbehandler
    crit_re = re.compile(r'(?<=\n)vi kritiserer', re.IGNORECASE) # kritiserer kommunen
    subsid_am_re = re.compile(r'revalidering.{2,25}subsidiær.{5,40}arbejdsmarkedsordninger', re.IGNORECASE | re.DOTALL) # subsidiær ift. arbejdsmarked
    subsid_udd_re = re.compile(r'revalidering.{2,25}subsidiær.{5,40}uddannelsesordninger', re.IGNORECASE | re.DOTALL) # subsidiær ift. uddannelse
    usikkert_re = re.compile(r'usikkert.{4,8}revalidering.{4,8}nødvendigt', re.IGNORECASE | re.DOTALL) # usikkert om revalidering er nødvendigt - "usikkert" bruges ikke i andre sammenhæng

    ## begrundelser
    ### - Vi lægger vægt …
    ### - Vi lægger også vægt på … 
    ### - Vi lægger desuden vægt på …

    #important_regex = re.compile(r'(?<=\n)((?:[\w\s]{0,25})?(?:vi )?lægger (?:vi )?(?:[\w\s]{3,30})? ?vægt på.*?)(?=\s{1,3}\n\s{1,3}\n)', re.IGNORECASE|re.DOTALL) 
    important_regex = re.compile(r'(?<=\n)((?:[\w\s]{0,25})?(?:vi )?lægger (?:vi )?(?:[\w\s]{3,30})? ?vægt på.*?)(?=\n\n)', re.IGNORECASE|re.DOTALL) 

    ## åbenlyst
    ## - "vurderes åbenlyst, at du ikke opfylder betingelserne"
    obv_re = re.compile(r'.{50}åbenlys.{150}', re.IGNORECASE | re.DOTALL)

    # Clean text
    text = clean_text(text)

    # Dictionary for info
    info_dict = {}


    try:
        kommune = kommune_re.search(text).group(1)
    except:
        kommune = 'not found'
    
    try:
        caseworker = caseworker_re.search(text).group(1)
    except:
        caseworker = 'not found'
    
    grounds = important_regex.findall(text)
    grounds_len = len(''.join(grounds))
    
    info_dict['kommune'] = kommune
    info_dict['caseworker'] = caseworker
    info_dict['kritik_kommune'] = bool(crit_re.search(text))
    info_dict['subsid_am'] = bool(subsid_am_re.search(text))
    info_dict['subsid_udd'] = bool(subsid_udd_re.search(text))
    info_dict['usikkert'] = bool(usikkert_re.search(text))
    info_dict['grounds'] = grounds
    info_dict['grounds_nchar'] = grounds_len
    info_dict['vurdering_åbenlys'] = bool(obv_re.search(text))
    
    return(info_dict)