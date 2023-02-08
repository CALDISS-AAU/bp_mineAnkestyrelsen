#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
import sys
from pprint import pprint 
import numpy as np

import pandas as pd
import spacy 

from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.utils import resample
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier

# Paths
project_p = join('/work', '214477', 'bp_mineAnkest')
data_dir = join(project_p, 'data')
output_dir = join(project_p, 'output')

## Filenames
data_p = join(data_dir, 'afgørelser_split-parsed.json')
cluster_out_p = join(output_dir, 'ada_clustering_predict.json')

# Read cases data
with open(data_p, 'r') as f:
    data = json.load(f)


# Load language model
nlp = spacy.load('da_core_news_sm')


# Tokenizer
def tokenizer(text): # tokenizer-funktion

    custom_words = ['lægge', 'forbindelse', 'vægt', 'derudover', 'del', 'videre', 'heraf', 'desuden', 'time', 'hjælp', 'komme', 'vurdere', 'uge', 
                   'herunder', 'august', 'kommune', 'februar', 'kontakt' 'marts', 'sag', 'afklare', 'borger', 'oktober', 'give', 'mulighed', 'september',
                   'juni', 'december', 'januar', 'henvendelse', 'findes', 'tage', 'strukturere', 'forberedende', 'iværksætte',
                   'lovgivning', 'lovgivning', 'enkelt', 'sigt', 'tilfælde', 'erhvervsrette'] #### put more words in 
    stop_words = list(nlp.Defaults.stop_words) + custom_words # stop words fra spacy er ikke en liste by default
    number_regex = re.compile(r'^\d.*')

    pos_tags = ['ADJ', 'NOUN', 'VERB', 'ADV'] # gemmer kun visse parts of speech (tillægsord, navneord, verber, biord/adverbier) #### adjust 

    doc = nlp(text) # bruger sprogmodel på textstykke

    tokens = [] # liste til tokens 
    
    for word in doc: # Looper igennem hvert ord i tweet
        if (len(word.lemma_) < 3): # Ord må ikke være mindre end 3 karakterer - går videre til næste ord, hvis det er
            continue
        if number_regex.match(word.text):
            continue
        if (word.pos_ in pos_tags) and (word.lemma_ not in stop_words): # Tjek at ordets POS-tag indgår i listen af accepterede tags og at ordet ikke er stopord
            tokens.append(word.lemma_) # Tilføj ordets lemma til tokens, hvis if-betingelse er opfyldt
                
    return(tokens)

# Sammensæt begrundelser til samlede tekster
for entry in data:
    entry['grounds'] = '\n'.join(entry.get('grounds'))


# Tokenize
for entry in data:
    entry['grounds_tokens'] = tokenizer(entry.get('grounds'))


# Selektér kun dokumenter med begrundelser med mere end 10 tokens (korte begrundelser betyder, at de blot refererer til kommunens begrundelse)
data_select = [entry.copy() for entry in data if len(entry.get('grounds_tokens')) >  10]


# FEATURES
## Tokens
grounds_tokens = [entry.get('grounds_tokens') for entry in data_select]

## Vectorizer
def return_tokens(tokens):
    return(tokens)

vectorizer = TfidfVectorizer(tokenizer = return_tokens, lowercase = False)

## Features
feature_vectors = vectorizer.fit_transform(grounds_tokens)


# CLUSTERING
## Hierarchical cluster 
agg_clustering = AgglomerativeClustering(n_clusters=5) 

agg_clustering.fit(feature_vectors.toarray())

cluster_labels = agg_clustering.labels_


## Adaboost 
n_samples = 1000
clustering_ada =  []

for i in range(n_samples): 
    bootstrap_sample, bootstrap_labels = resample(feature_vectors, cluster_labels)
    boosting = AdaBoostClassifier(n_estimators=100, random_state=0)
    boosting.fit(bootstrap_sample, bootstrap_labels)
    
    clustering_ada.append(boosting.predict(feature_vectors))

final_ada_clustering = np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, 
                                       arr=np.array(clustering_ada))

## Add to data
text_key = [re.search(r'^\d{1,2}(?= \-)', entry.get('filename')).group(0) + '-' + str(entry.get('no')) for entry in data_select]
cluster_pred = dict(zip(text_key, final_ada_clustering))

## Save to file
with open(cluster_out_p, 'w', encoding = 'utf-8') as f:
    json.dump(cluster_pred, f)