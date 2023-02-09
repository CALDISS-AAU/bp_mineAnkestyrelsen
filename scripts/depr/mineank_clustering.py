#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
import sys
from pprint import pprint 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import spacy 

from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

import gensim
import gensim.corpora as corpora
from gensim.models import CoherenceModel
from gensim.corpora.dictionary import Dictionary
from gensim.models import LdaMulticore

import tweetopic
from tweetopic.dmm import DMM
from tweetopic.btm import BTM
from tweetopic.pipeline import TopicPipeline

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
    entry['grounds_tokens'] = tokenizer(entry.get('grounds'))


# Selektér kun dokumenter med fundne begrundelser
data_select = [entry.copy() for entry in data if entry.get('grounds') != '']


# Konvertér til data frame
cases_df = pd.DataFrame.from_records(data_select)


# Vectorize 
"""
Hvis vectorizer skal bruges, er det bedst at bruge denne på det rå tekstindhold og så bruge definerede tokenizer i stedet for default i vectorizer.
sklearn vectorizers har også max_df, min_df så man kan sætte øvre og nedre grænser for, hvor mange dokumenter ord/token må være i.
"""
vectorizer = TfidfVectorizer(tokenizer = tokenizer, max_df = 0.95, min_df = 10)
#vectorizer = CountVectorizer(tokenizer = tokenizer, max_df = 0.95, min_df = 5)

grounds = [entry.get('grounds') for entry in data_select]
grounds_vector = vectorizer.fit_transform(grounds)


# DBSCAN Clustering
dbscan = DBSCAN(eps=0.5, min_samples=10)
clusters = dbscan.fit_predict(grounds_vector)


# Keyword analysis
## get vocabulary from vectorizer
vocab_from_vec = list(vectorizer.vocabulary_.keys())

## Explode df
cases_df_tidy = cases_df.explode('grounds_tokens')

## Filter
cases_df_tidy = cases_df_tidy.loc[cases_df_tidy['grounds_tokens'].isin(vocab_from_vec), :]

## Remove duplicates
cases_df_tidy = cases_df_tidy.drop_duplicates(['jnr', 'grounds_tokens'])

## Group by count
cases_df_tidy.groupby('grounds_tokens').size().sort_values(ascending = False)[0:50]

# Hvad er interessant?
## Nøgleord - hyppigste begrundelser?
## Sammenspil mellem begrundelser? (clustering af co-occurrence)
## Temaer?
## Hyppigt brugte fraser?

# Topic modelling - DMM (https://centre-for-humanities-computing.github.io/tweetopic/tweetopic.dmm.html#tweetopic-dmm)
#tf_idfvectorizer = TfidfVectorizer(tokenizer = tokenizer, max_df = 0.95, min_df = 10)
countvectorizer = CountVectorizer(tokenizer = tokenizer, max_df = 0.95, min_df = 5, ngram_range=(1,3))
dmm_model = DMM(n_components = 5)

pipeline = TopicPipeline(vectorizer = countvectorizer, topic_model = dmm_model)

fit_model = pipeline.fit_transform(grounds)

# Topic modelling - BTM (https://centre-for-humanities-computing.github.io/tweetopic/tweetopic.btm.html)
#tf_idfvectorizer = TfidfVectorizer(tokenizer = tokenizer, max_df = 0.95, min_df = 10)
countvectorizer = CountVectorizer(tokenizer = tokenizer, max_df = 0.95, min_df = 5, ngram_range=(1,3))
btm_model = BTM(n_components = 5)

pipeline = TopicPipeline(vectorizer = countvectorizer, topic_model = btm_model)

fit_model = pipeline.fit_transform(grounds)

# LDA - sklearn
def plot_top_words(model, feature_names, n_top_words, title): #https://scikit-learn.org/stable/auto_examples/applications/plot_topics_extraction_with_nmf_lda.html#sphx-glr-auto-examples-applications-plot-topics-extraction-with-nmf-lda-py
    fig, axes = plt.subplots(1, 5, figsize=(30, 15), sharex=True)
    axes = axes.flatten()
    for topic_idx, topic in enumerate(model.components_):
        top_features_ind = topic.argsort()[: -n_top_words - 1 : -1]
        top_features = [feature_names[i] for i in top_features_ind]
        weights = topic[top_features_ind]

        ax = axes[topic_idx]
        ax.barh(top_features, weights, height=0.7)
        ax.set_title(f"Topic {topic_idx +1}", fontdict={"fontsize": 30})
        ax.invert_yaxis()
        ax.tick_params(axis="both", which="major", labelsize=20)
        for i in "top right left".split():
            ax.spines[i].set_visible(False)
        fig.suptitle(title, fontsize=40)

    plt.subplots_adjust(top=0.90, bottom=0.05, wspace=0.90, hspace=0.3)
    plt.savefig('img.png')

lda = LatentDirichletAllocation(
    n_components=5,
    random_state=1337,
)

lda.fit(grounds_vector)

tf_feature_names = vectorizer.get_feature_names_out()
plot_top_words(lda, tf_feature_names, 15, "Topics in LDA model")

# LDA
## Corpus objects
id2token = corpora.Dictionary([entry.get('grounds_tokens') for entry in data_select])
#gensim.matutils.Sparse2Corpus(sparse, documents_columns=True)

### Gensim doc2bow corpus
for entry in data_select:
    entry['doc2bow'] = id2token.doc2bow(entry.get('grounds_tokens'))    
    
tokens_bow = [entry.get('doc2bow') for entry in data_select]

### Tfidf weighting of doc2bow 
tfidf = gensim.models.TfidfModel(tokens_bow)

for entry in data_select:
    entry['tfidfbow'] = tfidf[entry.get('doc2bow')]

tokens_tfidf = [entry.get('tfidfbow') for entry in data_select]

## Setup model
n_topics = 3
chunksize = 2000
passes = 20
iterations = 500

## Run
lda_model = gensim.models.LdaModel(corpus = tokens_bow, 
                                   num_topics = n_topics, 
                                   id2word = id2token, 
                                   chunksize = chunksize, 
                                   passes = passes, 
                                   iterations = iterations, 
                                   random_state = 1332,
                                   eval_every = 10,
                                   alpha = "auto",
                                   eta = "auto")

## Coherence
coherence_model_lda = CoherenceModel(model=lda_model, corpus=tokens_tfidf, coherence='u_mass')
print(coherence_model_lda.get_coherence())

topics = []
score = []
for i in range(1,20,1):
   lda_model = LdaMulticore(corpus=tokens_tfidf, id2word=id2token, iterations=iterations, num_topics=i, workers = 4, passes=20, random_state=100)
   cm = CoherenceModel(model=lda_model, corpus=tokens_tfidf, coherence='u_mass')
   topics.append(i)
   score.append(cm.get_coherence())
plt.plot(topics, score)
plt.xlabel('Number of Topics')
plt.ylabel('Coherence Score')
plt.savefig('img.png')

## Print topics
pprint(lda_model.show_topics(formatted=False, num_topics=n_topics))
