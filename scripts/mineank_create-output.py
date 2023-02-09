#!/usr/bin/env python
# coding: utf-8

import re
import os
from os.path import join
import json
import sys
import pandas as pd


# Paths
project_p = join('/work', '214477', 'bp_mineAnkest')
data_dir = join(project_p, 'data')
output_dir = join(project_p, 'output')

## Filenames
data_p = join(data_dir, 'afgørelser_split-parsed.json')
info_out = join(output_dir, 'afgørelser_oversigt.xlsx')
grounds_out = join(output_dir, 'agørelser_begrundelser.xlsx')
cluster_p = join(output_dir, 'ada_clustering_predict.json')


# Read cases data
with open(data_p, 'r') as f:
    data = json.load(f)


# Read cluster predictions
with open(cluster_p, 'r') as f:
    cluster_pred = json.load(f)


# Convert to data frame
cases_df = pd.DataFrame.from_records(data)
cluster_df = pd.DataFrame(cluster_pred.items(), columns=['merge_key', 'cluster'])

# Add key
cases_df['merge_key'] = cases_df['filename'].apply(lambda name: re.search(r'^\d{1,2}(?= \-)', name).group(0)) + '-' + cases_df['no'].astype(str)

# Merge
cases_df = pd.merge(cases_df, cluster_df, on = 'merge_key', how = 'left')


# Create output table
info_df = cases_df[['filename', 'no', 'docpageno_range', 'jnr', 'date', 'caseworker', 'kommune', 'birthyear', 
                    'gender', 'kritik_kommune', 'subsid_am', 'subsid_udd', 'vurdering_åbenlys', 'grounds_nchar', 'cluster']]


# Recode clusters
cluster_rename = {'0': 'Gruppe 1', '1': 'Gruppe 2', '2': 'Gruppe 3', '4': 'Gruppe 4'}

info_df.loc[info_df['cluster'].isna(), 'cluster'] = 'Ukendt'
info_df['cluster'] = info_df['cluster'].replace(cluster_rename)

# Recode gndr
gndr_recode = {'male': 'Mand', 'female': 'Kvinde'}

info_df['gender'] = info_df['gender'].replace(gndr_recode)

# Rename columns
columns_rename = {'filename': 'Filnavn', 
                  'no': 'Nr. i fil', 
                  'docpageno_range': 'Sidetal i fil', 
                  'jnr': 'J. Nr.', 
                  'date': 'Dato', 
                  'caseworker': 'Sagsbehandler',
                  'kommune': 'Kommune', 
                  'birthyear': 'Borger, fødselsår', 
                  'gender': 'Borger, køn', 
                  'kritik_kommune': 'Frase: Kritik af kommune', 
                  'subsid_am': 'Frase: Subsidiær, AM', 
                  'subsid_udd': 'Frase: Subsidiær, udd.', 
                  'vurdering_åbenlys': 'Frase: Vurder åbenlys', 
                  'grounds_nchar': 'Antal tegn, begrundelse', 
                  'cluster': 'Begrundelsesgruppe'}

info_df = info_df.rename(columns = columns_rename)

# Export
info_df.to_excel(info_out, index = False)


# Table for grounds
#grounds_df = cases_df[['jnr', 'grounds']]
#grounds_df = grounds_df.loc[~grounds_df['grounds'].isna(),:]
#grounds_df.to_excel(grounds_out, index = False)