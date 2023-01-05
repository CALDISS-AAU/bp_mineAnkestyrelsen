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

# Read cases data
with open(data_p, 'r') as f:
    data = json.load(f)


# Create output tables
cases_df = pd.DataFrame.from_records(data)
info_df = cases_df[['filename', 'n', 'jnr', 'birthyear', 'gender', 'kommune', 'caseworker']]

grounds_df = cases_df[['jnr', 'grounds']]
grounds_df = grounds_df.loc[~grounds_df['grounds'].isna(),:]

info_df.to_excel(info_out, index = False)
grounds_df.to_excel(grounds_out, index = False)