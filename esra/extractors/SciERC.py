import re
import os
import json
import glob
import copy
import random
import string
import subprocess

from ..utils import nlp_split


def _hash_list(l:list):
    
    return str(hash(str(l) + str(random.random())))

def _split_punc(abstract):
    """abstract preprocessing"""
    if isinstance(abstract, str):
        new_abs = [[]]
        for word in nlp_split(abstract):
            new_abs[-1] += [word.text]
            if word.text == '.':
                new_abs += [[]]
        if new_abs[-1] == []:
            return new_abs[:-1]
        return new_abs
    elif isinstance(abstract, list):
        return [_split_punc(a) for a in abstract]


def _dump_json_data(abstracts):
    """export the abstract(s) to data.json format"""
    
    data = [{"clusters": [],
            "sentences": abstract,
            "ner": [[] for _ in range(len(abstract))],
            "relation": [[] for _ in range(len(abstract))],
            "doc_key": _hash_list(abstract)} for abstract in abstracts]
        
    with open('./data/processed_data/json/dev.json', 'w') as f:
        for line in data:
            json.dump(line, f)
            f.write('\n')
            

def _interpret(result):
    tokens = copy.deepcopy(result['tokens'])
    entities = copy.deepcopy(result['ner'])
    relations = copy.deepcopy(result['relation'])
    corefs = copy.deepcopy(result['coref'])

    out_entities = []
    out_relations = []
    out_corefs = []
    _ent_index = {}

    assert len(tokens) == len(entities) == len(relations)
    
    # unrolling
    acc = 0
    for i in range(len(tokens)):
        tok_i = tokens[i]
        ent_i = entities[i]
        rel_i = relations[i]
        for e in ent_i:
            e[0] += acc
            e[1] += acc
        for r in rel_i:
            r[0] += acc
            r[1] += acc
            r[2] += acc
            r[3] += acc
        acc += len(tok_i)
    tokens = [t for l in tokens for t in l]
    entities = [e for l in entities for e in l]
    relations = [r for l in relations for r in l]

    for e in entities:
        _ent_index[(e[0], e[1])] = len(_ent_index)
        word = ' '.join(tokens[e[0]:e[1]+1])
        out_entities += [[e[2], word]]
        
        # for bugs of parentheses
        if len(tokens) > e[1]+1 and tokens[e[1]+1] == '(':
            _i = 1
            while tokens[e[1]+_i] != ')':
                _i += 1
            _ent_index[(e[0], e[1] + _i)] = len(_ent_index)
            word = ' '.join(tokens[e[0]:e[1]+_i+1])
            out_entities += [[e[2], word]]

            out_corefs += [[len(_ent_index)-2, len(_ent_index)-1]]

    for r in relations:
        try: 
            out_relations += [[r[4], _ent_index[(r[0], r[1])], _ent_index[(r[2], r[3])]]]
        except KeyError:
            print('bug was found here')

    for c in corefs:
        out_corefs += [[_ent_index[(e[0], e[1])] for e in c]]
    
    return {'entities': out_entities, 'relations': out_relations, 'coreferences': out_corefs}


def extract(abstracts, interpret=True):
    
    os.chdir('./SciERC')
    
    abstracts = _split_punc(abstracts)
    _dump_json_data(abstracts)
    
    # bug alert!
    subprocess.call(["python3", "generate_elmo.py", "--input", "./data/processed_data/json/dev.json", "--output", "./data/processed_data/elmo/dev.hdf5"])
    subprocess.call(["python3", "write_single.py", "scientific_best_coref"])
    
    # read output file
    filepath = "output.json"
    out = []
    with open(filepath) as f:
        for i, line in enumerate(f):
            out.append(json.loads(line))
            out[-1]['tokens'] = abstracts[i]
    
    os.chdir('..')

    if interpret:
        return [_interpret(ab) for ab in out]
    else:
        return out
