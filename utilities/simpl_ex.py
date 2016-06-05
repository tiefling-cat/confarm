#! /usr/bin/python3

import os, json
from time import process_time
#import matplotlib.pyplot as plt
#import networkx as nx

iroot = os.path.join('..', 'index-str')
croot = os.path.join('..', 'SynTagRus2015Conll')
jsonpath = '../static/json/default.json'

prdict = {"ОБО":"О", "ОБ":"О", "СО":"С", "ИЗО":"ИЗ", "ОТО":"ОТ",
          "ВО":"В", "КО":"К", "БЕЗО":"БЕЗ", "НАДО":"НАД", "ПОДО":"ПОД",
          "ПРЕДО":"ПЕРЕД", "ПРЕД":"ПЕРЕД", "ПЕРЕДО":"ПЕРЕД",
          "ЧРЕЗ":"ЧЕРЕЗ", "ЧЕРЕЗО":"ЧЕРЕЗ", "ЧРЕЗО":"ЧЕРЕЗ"}

relfilter = {'сент-соч', 'сочин'}
casepos = {'S':2, 'A':1, 'PARTCP':2, 'SPRO':3}
hardcap = 9000

def get_index(lemma, iroot):
    """
    Get index of all lemma entries.
    """
    idict = {}
    fname = os.path.join(iroot, lemma[0][0], '.'.join(lemma) + '.txt')
    with open(fname, 'r', encoding='utf-8') as ifile:
        for line in ifile:
            parts = line.strip().split(';')
            path = parts[0]
            if path not in idict:
                idict[path] = []
            idict[path].append(parts[1:])

    return idict

def get_relset(frame):
    reldict, relset = {}, set()
    for token in frame:
        rel = token[9]
        reldict[rel] = reldict.get(rel, 0) + 1
    for rel, count in reldict.items():
        relset.add(rel)
        for i in range(2, count + 1):
            relset.add('-'.join([rel, str(i)]))
    relset = list(relset)
    relset.sort()
    return tuple(relset)

def get_relset_dict(sents):
    relset_dict = {}
    for head_id, sent, frame in sents:
        relset = get_relset(frame)
        if relset not in relset_dict:
            relset_dict[relset] = []
        relset_dict[relset].append((head_id, sent, frame))
    return relset_dict

def make_digraph(relset_levels):
    edges = []

    for i, lower_level in enumerate(relset_levels):
        for lower_class in lower_level:
            lower_set = set(lower_class)
            found = False
            for higher_level in relset_levels[i+1:]:
                for higher_class in higher_level:
                    higher_set = set(higher_class)
                    if lower_set.issubset(higher_set):
                        edges.append((lower_class, higher_class))
                        found = True
                if found:
                    break

    #G = nx.DiGraph()
    #G.add_edges_from(edges)
    #return G

def to_str(relset):
    if relset == ():
        return 'empty'
    return ', '.join(relset)

def make_json_digraph(relset_levels, relset_ids, jsonpath):
    nodes = [{'id':i, 'label':to_str(relset), 'size':10} for relset, i in relset_ids.items()]
    edges = []
    
    level_log = open('levels.log', 'w', encoding='utf-8')

    edgecount = 0
    reversed_levels = relset_levels[::-1]
    for i, higher_level in enumerate(reversed_levels):
        for higher_class in higher_level:
            level_log.write(str(higher_class) + '\n')
            higher_set = set(higher_class)
            found = False
            for lower_level in reversed_levels[i+1:]:
                for lower_class in lower_level:
                    lower_set = set(lower_class)
                    if lower_set.issubset(higher_set):
                        edges.append({'id':'e' + str(edgecount),
                                      'source':relset_ids[lower_class],
                                      'target':relset_ids[higher_class]
                                     })
                        edgecount += 1
                        found = True
                if found:
                    break

    level_log.close()

    pos = {}
    width, dy, vloc = 100, 10, 0
    for level in relset_levels:
        dx = width / (len(level) + 1)
        if len(level) >= 5:
            yalt = dy / 10
        else:
            yalt = 0.
        
        for i, node in enumerate(level):
            pos[relset_ids[node]] = ((i + 1) * dx, vloc + yalt)
            yalt = -yalt
        vloc = vloc + dy

    for node in nodes:
        xy = pos[node['id']]
        node['x'], node['y'] = int(xy[0]), int(xy[1])

    with open(jsonpath, 'w', encoding='utf-8') as jsonfile:
        json.dump({'nodes':nodes, 'edges':edges}, jsonfile)

def get_relset_classes(relset_dict, threshold):
    relset_classes = [relset_class 
                        for relset_class in relset_dict.keys()
                            if len(relset_dict[relset_class]) >= threshold
                                or relset_class == ()]
    relset_classes.sort(key=len)
    relset_ids = {relset_class:'n' + str(i) for i, relset_class in enumerate(relset_classes)}
    return relset_classes, relset_ids

def get_relset_levels(relset_classes):
    level_dict = {}
    for relset_class in relset_classes:
        level = len(relset_class)
        if level not in level_dict:
            level_dict[level] = []
        level_dict[level].append(relset_class)
    relset_levels = sorted(level_dict.items(), key=lambda x:int(x[0]))
    return [sorted(level) for level in list(zip(*relset_levels))[1]]

def level_pos(relset_levels, width=1., dy=0.1, vloc=0):
    pos = {}
    for level in relset_levels:
        dx = width / (len(level) + 1)
        if len(level) > 5:
            yalt = dy / 16
        else:
            yalt = 0.
        
        for i, node in enumerate(level):
            pos[node] = ((i + 1) * dx, vloc + yalt)
            yalt = -yalt
        vloc = vloc - dy
    return pos

def get_children(sent, dad_id, pr=True,
                 usepos=False, usecase=False, useanim=False,
                 splice=False, strip=False, 
                 negrels=(), prnegrels=()):
    """
    Collect all direct children and mark all tokens.
    """
    children = []
    if pr:
        sent[dad_id - 1][8] = 1
        for token in sent:
            token[9] = token[7]
    for i, token in enumerate(sent):
        #if int(token[0]) == dad_id:
        #    children.append(token)
        if int(token[6]) == dad_id and \
           token[3] not in ['PUNC', 'SENT'] and \
           token[7] not in relfilter:
            if token[3] != 'PR':
                if token[7] not in negrels:
                    # direct child with allowed relation
                    if pr:
                        token[8] = 2
                        if strip and token[9].endswith('компл'):
                            token[9] = token[9][2:]
                        if usepos:
                            token[9] = ' '.join([token[9], token[3]])
                        if usecase and token[3] in casepos:
                            try:
                                token[9] = ' '.join([token[9], token[5].split(' ')[casepos[token[3]]]])
                            except IndexError:
                                token[9] = ' '.join([token[9], token[5]])
                        if useanim and token[3] == 'S':
                            token[9] = ' '.join([token[9], token[5].split(' ')[1]])
                    else:
                        token[8] = 4
                    children.append(token)
            elif pr and token[7] not in prnegrels:
                # preposition
                # deal with preposition's children
                token[8] = 3
                pr_children = get_children(sent[i+1:], i+1, pr=False)
                for child in pr_children:
                    # normalize preposition and put it after link
                    if splice and (token[9] == 'обст' or token[9].endswith('компл')):
                        token[9] = 'компл/обст'
                    elif strip and token[9].endswith('компл'):
                        token[9] = token[9][2:]
                    child[9] = ':'.join([token[9], prdict.get(token[2], token[2])])
                    if usepos:
                        child[9] = ' '.join([child[9], child[3]])
                    if usecase and child[3] in casepos:
                        try:
                            child[9] = ' '.join([child[9], child[5].split(' ')[casepos[child[3]]]])
                        except IndexError:
                            child[9] = ' '.join([child[9], child[5]])
                    if useanim and child[3] == 'S':
                        child[9] = ' '.join([child[9], child[5].split(' ')[1]])
                    children.append(child)
    for token in sent:
        if token[8] == '_':
            token[8] = 0
    return children

def extract(idict, croot, usepos, usecase, useanim, splice, strip, posfeats, negfeats, posrels, negrels, prnegrels):
    """
    Find all sentences within idict,
    get them, extract frames.
    """
    con_sents = []
    for ifname, entries in idict.items():
        path = os.path.join(croot, ifname)
        with open(path, 'r', encoding='utf-8') as ifile:
            lines = ifile.readlines()
        for entry in entries:
            # find token
            tok_line = int(entry[3])
            tok_feats = lines[tok_line].split('\t')[5].split(' ')

            # check if token feats satisfy pos and neg requirements
            if all(posfeat in tok_feats for posfeat in posfeats) and \
               not any(negfeat in tok_feats for negfeat in negfeats):
                # cut out full sentence
                tok_id = int(entry[1])
                start = tok_line - tok_id + 1
                end = tok_line + int(entry[2]) + 1
                raw_tokens = lines[start:end]
                tokens = []
                for token in raw_tokens:
                    token = token.strip().split('\t')
                    token[4] = token[3]
                    if token[5][0].isupper():
                        if token[5] == 'PUNC':
                            token[3], token[5] = 'PUNC', '_'
                        else:
                            parts = token[5].split(' ', maxsplit=1)
                            if len(parts) == 1:
                                token[5] = '_'
                            else:
                                token[5] = parts[1]
                    tokens.append(token)

                # extract frame
                frame = get_children(tokens, tok_id, usepos=usepos,
                                     usecase=usecase, useanim=useanim,
                                     splice=splice, strip=strip, 
                                     negrels=negrels, prnegrels=prnegrels)

                if posrels == [] or posrels == () or \
                   any(token[7] in posrels for token in frame if token[0] != tok_id):
                    con_sents.append((tok_id, tokens, frame))
    return con_sents

def extract_frames(lemma, iroot=iroot, croot=croot, jsonpath=jsonpath, usepos=False,
                   usecase=False, useanim=False, splice=False, strip=False, 
                   posfeats=(), negfeats=(), posrels=(), negrels=(), prnegrels=(),
                   threshold=2):
    """
    Extract frames from Alpha to Omega.
    """
    #import logging
    #logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s',
                        #level = logging.DEBUG,
    #                    filename = os.path.join(os.getcwd(), 'extract.log'))

    try:
        print('Extracting index for {}, {}'.format(*lemma))
        idict = get_index(lemma, iroot)
        print('Done extracting index')
    except FileNotFoundError:
        print('Failed')
        return {'error':'FileNotFoundError'}

    print('Extracting constructions')
    sents = extract(idict, croot, usepos, usecase, useanim, splice, strip, 
                    posfeats=posfeats, negfeats=negfeats, 
                    posrels=posrels, negrels=negrels, prnegrels=prnegrels)
    print('Done extracting constructions')

    if sents == []:
        print('No constructions found')
        return {'json':'', 'classes':[], 'frames':[], 'error':'NoExtract'}

    if len(sents) > hardcap:
        print('Too many constructions found')
        return {'json':'', 'classes':[], 'frames':[], 'error':'TooMany'}

    print('Classifying constructions')
    relset_dict = get_relset_dict(sents)
    relset_classes, relset_ids = get_relset_classes(relset_dict, threshold)
    with open('classes.log', 'w', encoding='utf-8') as clfile:
        for relset_class in relset_classes:
            clfile.write(str(relset_class) + '\n')
    relset_levels = get_relset_levels(relset_classes)
    print('Done classifying constructions')

    print('Making class graph')
    make_json_digraph(relset_levels, relset_ids, jsonpath)
    print('Done making class graph')

    relset_classes = [', '.join(relset_class) for relset_class in relset_classes]
    relset_dict = {', '.join(relset_class):frames for relset_class, frames in relset_dict.items()}

    print('Extraction successful')
    return {'json':os.path.join('.', 'static', 'json', os.path.basename(jsonpath)), 'classes':relset_classes, 'frames':relset_dict, 'error':'NoError'}

if __name__ == "__main__":
    idict = get_index(lemma, iroot)

    start = process_time()
    sents = extract(idict, croot)
    print(len(sents))
    print(process_time() - start)

    start = process_time()
    relset_dict = get_relset_dict(sents)
    relset_classes, relset_ids = get_relset_classes(relset_dict, threshold)
    relset_levels = get_relset_levels(relset_classes)

    for relset_class in relset_classes:
        if len(relset_dict[relset_class]) > threshold:
            print(relset_class, len(relset_dict[relset_class]))

    #class_volumes = [len(value) for value in relset_dict.values()]
    #plt.hist(class_volumes, bins=100)
    #plt.show()

    #G = make_digraph(relset_levels)
    print(process_time() - start)

    #pos = level_pos(relset_levels)    
    #nx.draw(G, pos=pos, with_labels=True, arrows=False, node_size=500, node_color='w')
    #plt.show()
