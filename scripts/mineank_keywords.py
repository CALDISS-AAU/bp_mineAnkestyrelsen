#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
import sys
from pprint import pprint 
import pandas as pd
import spacy 

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer

# Paths
project_p = join('/work', '214477', 'bp_mineAnkest')
data_dir = join(project_p, 'data')
output_dir = join(project_p, 'output')

## Filenames
data_p = join(data_dir, 'afgørelser_split-extracted.json')


# Read cases data
with open(data_p, 'r') as f:
    data = json.load(f)


# Load language model
nlp = spacy.load('da_core_news_sm')


# Tokenizer
def tokenizer(text): # tokenizer-funktion

    custom_words = ['lægge', 'forbindelse', 'vægt', 'derudover', 'del', 'videre', 'heraf', 'desuden']
    stop_words = list(nlp.Defaults.stop_words) + custom_words # stop words fra spacy er ikke en liste by default
    number_regex = re.compile(r'^\d.*')

    pos_tags = ['ADJ', 'NOUN', 'VERB', 'ADV'] # gemmer kun visse parts of speech (tillægsord, navneord, verber, biord/adverbier)

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


# Konvertér til data frame
cases_df = pd.DataFrame.from_records(data_select)


# Keyword analysis 
"""
Hvis vectorizer skal bruges, er det bedst at bruge denne på det rå tekstindhold og så bruge definerede tokenizer i stedet for default i vectorizer.
sklearn vectorizers har også max_df, min_df så man kan sætte øvre og nedre grænser for, hvor mange dokumenter ord/token må være i.
"""
grounds = [entry.get('grounds') for entry in data_select]
## Keyword analysis - TFIDF
### Vectorize
tfidf_vectorizer = TfidfVectorizer(tokenizer = tokenizer, max_df = 1.0, min_df = 5, ngram_range=(1,3))

grounds_vector = tfidf_vectorizer.fit_transform(grounds)

### Summarize
sum_words = grounds_vector.sum(axis=0) 
words_freq = [(word, sum_words[0, idx]) for word, idx in tfidf_vectorizer.vocabulary_.items()]
words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
tfidf_top_df = pd.DataFrame(words_freq[:100])
tfidf_top_df.columns = ['keywords', 'tfidf count']
tfidf_top_df['keywords'] = tfidf_top_df['keywords'].str.replace(' ', ', ')

## Keyword analysis - Count (binary)
### Vectorize
count_vectorizer = CountVectorizer(tokenizer = tokenizer, max_df = 1.0, min_df = 5, binary = True, ngram_range=(1,3))

grounds_vector = count_vectorizer.fit_transform(grounds)

### Summarize
sum_words = grounds_vector.sum(axis=0) 
words_freq = [(word, sum_words[0, idx]) for word, idx in count_vectorizer.vocabulary_.items()]
words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
count_top_df = pd.DataFrame(words_freq[:100])
count_top_df.columns = ['keywords', ' document count']
count_top_df['keywords'] = count_top_df['keywords'].str.replace(' ', ', ')

## Export
tfidf_top_df.to_excel(join(output_dir, 'afgørelser_tfidf-tælling.xlsx'), index = False)
count_top_df.to_excel(join(output_dir, 'afgørelser_dok-med-ord-tælling.xlsx'), index = False)