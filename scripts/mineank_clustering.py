#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import spacy 

from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import CountVectorizer

from gensim.corpora.dictionary import Dictionary


# Paths
project_p = join('/work', '214477', 'bp_mineAnkest')
data_dir = join(project_p, 'data')
output_dir = join(project_p, 'output')

## Filenames
data_p = join(data_dir, 'afgørelser_split-parsed.json')


# Read cases data
with open(data_p, 'r') as f:
    data = json.load(f)


# Load language model
nlp = spacy.load('da_core_news_sm')


# Tokenizer
def tokenizer(text): # tokenizer-funktion

    stop_words = list(nlp.Defaults.stop_words) # stop words fra spacy er ikke en liste by default

    pos_tags = ['ADJ', 'NOUN', 'VERB', 'ADV'] # gemmer kun visse parts of speech (tillægsord, navneord, verber, biord/adverbier)

    doc = nlp(text) # bruger sprogmodel på textstykke

    tokens = [] # liste til tokens 
    
    for word in doc: # Looper igennem hvert ord i tweet
        if (len(word.lemma_) < 3): # Ord må ikke være mindre end 3 karakterer - går videre til næste ord, hvis det er
            continue
        if (word.pos_ in pos_tags) and (word.lemma_ not in stop_words): # Tjek at ordets POS-tag indgår i listen af accepterede tags og at ordet ikke er stopord
            tokens.append(word.lemma_) # Tilføj ordets lemma til tokens, hvis if-betingelse er opfyldt
                
    return(tokens)


# Wrapper til at tokenize begrundelser (Måske ikke nødvendig, hvis der bruges vectorizers fra sklearn)
#def tokenize_grounds(grounds_list):
#
#    grounds_combined = '\n'.join(grounds_list)
#
#    grounds_tokens = tokenizer(grounds_combined)
#
#    return(gorunds_tokens)


# Sammensæt begrundelser til samlede tekster
for entry in data:
    entry['grounds'] = '\n'.join(entry.get('grounds'))


# Tokenize
for entry in data:
    entry['grouds_tokens'] = tokenizer(entry.get('grounds'))


# Konvertér til data frame
cases_df = pd.DataFrame.from_records(data)

# Vectorize 
"""
Hvis vectorizer skal bruges, er det bedst at bruge denne på det rå tekstindhold og så bruge definerede tokenizer i stedet for default i vectorizer.
sklearn vectorizers har også max_df, min_df så man kan sætte øvre og nedre grænser for, hvor mange dokumenter ord/token må være i.
"""
vectorizer = TfidfVectorizer(tokenizer = tokenizer, max_df = 0.95, min_df = 2)

grounds = [entry.get('grounds') for entry in data]
grounds_vector = vectorizer.fit_transform(grounds)


# DBSCAN Clustering
dbscan = DBSCAN(eps=0.5, min_samples=3)
clusters = dbscan.fit_predict(grounds_vector)


