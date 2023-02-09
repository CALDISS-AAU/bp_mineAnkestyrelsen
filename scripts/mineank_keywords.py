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
data_p = join(data_dir, 'afgørelser_split-parsed.json')
cluster_p = join(output_dir, 'ada_clustering_predict.json')


# Read cases data
with open(data_p, 'r') as f:
    data = json.load(f)

# Read cluster predictions
with open(cluster_p, 'r') as f:
    cluster_pred = json.load(f)


# Load language model
nlp = spacy.load('da_core_news_sm')


# Tokenizer
def tokenizer(text): # tokenizer-funktion

    custom_words = ['fremgå', 'lægge', 'forbindelse', 'vægt', 'derudover', 'del', 'videre', 'heraf', 'desuden', 'time', 'hjælp', 'komme', 'vurdere', 'uge', 
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


# Convert to data frame
cases_df = pd.DataFrame.from_records(data)
cluster_df = pd.DataFrame(cluster_pred.items(), columns=['merge_key', 'cluster'])

# Add key
cases_df['merge_key'] = cases_df['filename'].apply(lambda name: re.search(r'^\d{1,2}(?= \-)', name).group(0)) + '-' + cases_df['no'].astype(str)

# Merge
cases_df = pd.merge(cases_df, cluster_df, on = 'merge_key', how = 'left')


# Keyword analysis simple
cases_df_long = cases_df.explode('grounds_tokens')

cluster_token_summary = cases_df_long.groupby(['grounds_tokens', 'cluster']).size().to_frame(name = 'count').reset_index()
cluster_token_summary.sort_values('count', ascending = False).groupby('cluster').head(10)

# Keyword analysis TF-IDF
def get_top_in_cluster(cases_data, cluster, n = 50):
    cluster_grounds = list(cases_data.loc[cases_df['cluster'] == str(cluster), 'grounds'])

    tfidf_vectorizer = TfidfVectorizer(tokenizer = tokenizer, max_df = 1.0, min_df = 5, ngram_range=(5,5))

    grounds_vector = tfidf_vectorizer.fit_transform(cluster_grounds)

    ### Summarize
    sum_words = grounds_vector.sum(axis=0) 
    words_freq = [(word, sum_words[0, idx]) for word, idx in tfidf_vectorizer.vocabulary_.items()]
    words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
    tfidf_top_df = pd.DataFrame(words_freq[:n])
    tfidf_top_df.columns = ['keywords', 'tfidf count']
    tfidf_top_df['keywords'] = tfidf_top_df['keywords'].str.replace(' ', ', ')

    return(tfidf_top_df)

get_top_in_cluster(cases_df, 1, n = 50) # 0 - kort oplæring

## Keyword analysis - Count (binary)
def get_top_in_cluster_bin(cases_data, cluster, n = 50):
    cluster_grounds = list(cases_data.loc[cases_df['cluster'] == str(cluster), 'grounds'])
    ### Vectorize
    
    count_vectorizer = CountVectorizer(tokenizer = tokenizer, max_df = 1.0, min_df = 5, binary = True, ngram_range=(1,10))

    grounds_vector = count_vectorizer.fit_transform(cluster_grounds)

    ### Summarize
    sum_words = grounds_vector.sum(axis=0) 
    words_freq = [(word, sum_words[0, idx]) for word, idx in count_vectorizer.vocabulary_.items()]
    words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
    count_top_df = pd.DataFrame(words_freq[:1000])
    count_top_df.columns = ['keywords', 'document count']
    count_top_df['keywords'] = count_top_df['keywords'].str.replace(' ', ', ')
    
    filter_words = []
    for kw in list(count_top_df['keywords']):
        doc_count = int(count_top_df.loc[count_top_df['keywords'] == kw, 'document count'])
        select = count_top_df.loc[count_top_df['keywords'].str.contains(kw), :]
        select = select.loc[select['keywords'] != kw]

        if len(select) > 1 and doc_count in list(select['document count']):
            filter_words.append(kw)

    count_top_df = count_top_df.loc[~count_top_df['keywords'].isin(filter_words), :]

    count_top_df = count_top_df[0:n]

    count_top_df = count_top_df.rename(columns = {'keywords': 'Nøgleord', 'document count': 'Antal sager'})

    return(count_top_df)

# Summaries
cluster_0_count_df = get_top_in_cluster_bin(cases_df, 0, n = 50)
cluster_1_count_df = get_top_in_cluster_bin(cases_df, 1, n = 50)
cluster_2_count_df = get_top_in_cluster_bin(cases_df, 2, n = 50)

## Export
#tfidf_top_df.to_excel(join(output_dir, 'afgørelser_tfidf-tælling.xlsx'), index = False)
cluster_0_count_df.to_excel(join(output_dir, 'gruppe1_nøgleord.xlsx'), index = False)
cluster_1_count_df.to_excel(join(output_dir, 'gruppe2_nøgleord.xlsx'), index = False)
cluster_2_count_df.to_excel(join(output_dir, 'gruppe3_nøgleord.xlsx'), index = False)