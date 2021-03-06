import os
import re
import esra
import json
import glob
import pickle
import pandas as pd

from esra.extractors import ESRAE
from esra.utils import nlp_split


def clean_abstract(abstract):
    
    # remove other language
    pos = abstract.find('----')
    if pos > len(abstract) / 3:
        abstract = abstract[:pos]
    
    abstract = re.sub(r'\s+', ' ', abstract)
    abstract = re.sub(r'\\\'', '\'', abstract)
    abstract = re.sub(r'\\\`', '\'', abstract)
    
    # \begin{text}
    abstract = re.sub(r'\\citep?\{([^\}]+)\}', r'', abstract)
    
    # \cite{xxxxxxx}
    abstract = re.sub(r'\\[a-zA-Z]{1,15}\{([^\}]+)\}', r'\1', abstract)
    
    # {\it text}
    abstract = re.sub(r'\{\\[a-zA-Z]{1,15} ([^\}]+)\}', r'\1', abstract)

    # $formula$
    abstract = re.sub(r'\$(.{1,30})\$', r'\1', abstract)
    
    # _{lower_text}
    abstract = re.sub(r'\_\{([^\}]+)\}', r' \1', abstract)
    
    # ^{upper_text}
    abstract = re.sub(r'\^\{([^\}]+)\}', r' \1', abstract)
    
    abstract = ' '.join(abstract.split()[:400])
    return abstract.strip()

df = pd.read_csv('data/arxiv/kaggle-arxiv-cscl-2020-12-18.csv')
df.abstract = df.abstract.apply(clean_abstract)

for i in range(24):
    start = i * 1000
    end = (i + 1) * 1000
    
    filename = f'data/pickle/kaggle_arxiv_{start}_{end}.pickle'
    print(filename)
    if os.path.isfile(filename):
        continue
    
    abstracts = df.abstract.iloc[start:end].to_list()
    ids = df.id[start:end].to_list()
    r = ESRAE.extract(abstracts)

    # label their id
    for doc, id in zip(r, ids):
        doc['id'] = id

    with open(filename, 'wb') as f:
        pickle.dump(r, f)
