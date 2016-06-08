import os, json

prdict = {"ОБО":"О", "ОБ":"О", "СО":"С", "ИЗО":"ИЗ", "ОТО":"ОТ",
          "ВО":"В", "КО":"К", "БЕЗО":"БЕЗ", "НАДО":"НАД", "ПОДО":"ПОД",
          "ПРЕДО":"ПЕРЕД", "ПРЕД":"ПЕРЕД", "ПЕРЕДО":"ПЕРЕД",
          "ЧРЕЗ":"ЧЕРЕЗ", "ЧЕРЕЗО":"ЧЕРЕЗ", "ЧРЕЗО":"ЧЕРЕЗ"}

subjrels = {'предик', 'дат-субъект', 'агент', 'квазиагент', 'несобст-агент'}
relfilter = {'сент-соч', 'сочин', 'соч-союзн'}
coord_set = {'сочин', 'соч-союзн'}
emergency_coord_set = {'сравн-союзн', 'подч-союзн'}
casepos = {'S':2, 'PARTCP':2, 'SPRO':3}
hardcap = 9000

short_marker_set = [0, 1, 2, 3, 4]
long_marker_set = [0, 5, 6, 7, 8]

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
    """
    Form relation signature.
    """
    subj, other = {}, {}
    for token in frame:
        rel = token[9]
        for subjrel in subjrels:
            if rel.startswith(subjrel):
                subj[rel] = subj.get(rel, 0) + 1
                break
        else:
            other[rel] = other.get(rel, 0) + 1

    subjlist = []
    for rel, count in subj.items():
        subjlist.append(rel)
        for i in range(2, count + 1):
            subjlist.append('-'.join([rel, str(i)]))
    subjlist.sort()

    otherlist = []
    for rel, count in other.items():
        otherlist.append(rel)
        for i in range(2, count + 1):
            otherlist.append('-'.join([rel, str(i)]))
    otherlist.sort()

    return tuple(subjlist + otherlist)

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

def get_relset_classes(relset_dict):
    relset_classes = list(relset_dict.keys())
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

def token_signature(token, usepos, usecase, useanim, strip):
    signature = token[9]
    feats = token[5].split(' ')
    pos = token[3]

    if strip and signature.endswith('компл'):
        signature = signature[2:]
    if usepos:
        signature = ' '.join([signature, token[3]])
    if usecase:
        if pos in casepos:
            try:
                signature = ' '.join([signature, feats[casepos[token[3]]]])
            except IndexError:
                if not usepos:
                    signature = ' '.join([signature, pos])
        elif pos == 'V' and feats[3] == 'inf':
            signature = ' '.join([signature, 'inf'])
        elif pos == 'A':
            comp, case, brev = feats[0], feats[1], feats[3]
            if case != '-':
                feat = case
            elif comp != '-':
                feat = comp
            elif brev != '-':
                feat = brev
            else:
                feat = '-'
            signature = ' '.join([signature, feat])
    if useanim and pos == 'S':
        signature = ' '.join([signature, feats[1]])
    return signature

def get_children(sent, dad_id, marker_set, pr=True,
                 usepos=False, usecase=False, useanim=False,
                 splice=False, strip=False,
                 negrels=(), prnegrels=()):
    """
    Collect all direct children and mark all tokens.
    """
    children = []
    #if pr:
    #    sent[dad_id - 1][8] = marker_set[1]
    for i, token in enumerate(sent):
        if int(token[6]) == dad_id and \
           token[3] not in ['PUNC', 'SENT'] and \
           token[7] not in relfilter:
            if token[3] != 'PR':
                if token[7] not in negrels and token[8] == '_':
                    # direct child with allowed relation
                    if pr:
                        token[8] = marker_set[2]
                        token[9] = token_signature(token, usepos, usecase, useanim, strip)
                    else:
                        token[8] = marker_set[4]
                    children.append(token)
            elif pr and token[7] not in prnegrels:
                # it's a preposition
                # deal with preposition's children
                token[8] = marker_set[3]
                pr_children = get_children(sent[i+1:], i+1, marker_set, pr=False)
                for child in pr_children:
                    # normalize preposition and put it after link
                    if splice and (token[9] == 'обст' or token[9].endswith('компл')):
                        token[9] = 'компл/обст'
                    elif strip and token[9].endswith('компл'):
                        token[9] = token[9][2:]
                    child[9] = ':'.join([token[9], prdict.get(token[2], token[2])])
                    child[9] = token_signature(child, usepos, usecase, useanim, strip=False)
                    children.append(child)
    return children

def get_children_posrels(sent, dad_id, marker_set, pr=False,
                 usepos=False, usecase=False, useanim=False,
                 splice=False, strip=False,
                 posrels=()):
    children = []
    for i, token in enumerate(sent):
        if int(token[6]) == dad_id and \
           token[3] not in ['PUNC', 'SENT'] and \
           token[7] not in relfilter and token[7] in posrels:
            if token[9] == '_':
                token[8] = marker_set[2]
                token[9] = token_signature(token, usepos, usecase, useanim, strip)
                children.append(token)
    return children

def prepare_tokens(raw_tokens):
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
        token[9] = token[7]
        tokens.append(token)
    return tokens

def extract_frame(tokens, tok_id,
            usepos, pro, usecase, useanim, 
            splice, strip, 
            posfeats, negfeats, 
            posrels, negrels, prnegrels):

    frame = get_children(tokens, tok_id, short_marker_set, 
                         usepos=usepos, usecase=usecase, useanim=useanim,
                         splice=splice, strip=strip,
                         negrels=negrels, prnegrels=prnegrels)
    tokens[tok_id - 1][8] = short_marker_set[1]

    if tokens[tok_id - 1][6] != '0':
        dad_id = int(tokens[tok_id - 1][6])
        if tokens[dad_id - 1][3] in ['V', 'A'] and \
           tokens[tok_id - 1][7] not in {'разъяснит', 'сент-соч', 'сочин', 'примыкат'}:
            if tokens[tok_id - 1][3] == 'V':
                feats = tokens[tok_id - 1][5].split(' ')

                if feats[3] == 'inf':
                    # infinitives are kings
                    distant_frame = get_children(tokens, dad_id, long_marker_set,
                                                 usepos=usepos, usecase=usecase, useanim=useanim,
                                                 splice=splice, strip=strip,
                                                 negrels=negrels, prnegrels=prnegrels)
                    if distant_frame != []:
                        tokens[dad_id - 1][8] = long_marker_set[1]
                        frame.extend(distant_frame)

                    # look for dad's coordinated dependencies
                    currtok = tokens[dad_id - 1]
                    mediators, steps = [], 0
                    while currtok[7] in coord_set:
                        currtok = tokens[int(currtok[6]) - 1]
                        mediators.append(currtok)
                        steps += 1
                    if steps > 0 and currtok[3] in ['V', 'A', 'PARTCP']:
                        distant_frame = get_children_posrels(tokens, int(currtok[0]), long_marker_set, 
                                         usepos=usepos, usecase=usecase, useanim=useanim,
                                         splice=splice, strip=strip,
                                         posrels=['предик'])
                        if distant_frame != []:
                            for mediator in mediators:
                                mediator[8] = 9
                            frame.extend(distant_frame)

                elif feats[3] == 'ger':
                    # transgressives only deserve subjects
                    distant_frame = get_children_posrels(tokens, dad_id, long_marker_set, 
                                             usepos=usepos, usecase=usecase, useanim=useanim,
                                             splice=splice, strip=strip,
                                             posrels=['предик'])
                    if distant_frame != []:
                        tokens[dad_id - 1][8] = long_marker_set[1]
                        frame.extend(distant_frame)

            # some stuff for nouns
            elif tokens[tok_id - 1][3] == 'S' and tokens[tok_id - 1][5].split(' ')[2] == 'acc':
                distant_frame = get_children(tokens, dad_id, long_marker_set, 
                                         usepos=usepos, usecase=usecase, useanim=useanim,
                                         splice=splice, strip=strip,
                                         negrels=negrels, prnegrels=prnegrels)
                if distant_frame != []:
                    tokens[dad_id - 1][8] = long_marker_set[1]
                    frame.extend(distant_frame)

        # look for coordinated dependencies
        currtok = tokens[tok_id - 1]
        mediators, steps = [], 0
        while currtok[7] in coord_set:
            currtok = tokens[int(currtok[6]) - 1]
            mediators.append(currtok)
            steps += 1
        if steps > 0 and (currtok[3] == tokens[tok_id - 1][3]) or \
           (tokens[tok_id - 1][3] == 'V' and currtok[3] in ['V', 'A', 'PARTCP']):
            distant_frame = get_children_posrels(tokens, int(currtok[0]), long_marker_set, 
                                         usepos=usepos, usecase=usecase, useanim=useanim,
                                         splice=splice, strip=strip,
                                         posrels=['предик'])
            if distant_frame != []:
                for mediator in mediators:
                    mediator[8] = 9
                frame.extend(distant_frame)

        if all(token[7] != 'предик' for token in frame if token[0] != str(tok_id)):
            # we're a little desperate for subject now
            currtok = tokens[tok_id - 1]
            mediators, steps = [], 0
            while currtok[7] in emergency_coord_set:
                currtok = tokens[int(currtok[6]) - 1]
                mediators.append(currtok)
                steps += 1
            if steps > 0 and currtok[6] != '0':
                currtok = tokens[int(currtok[6]) - 1]
                mediators.append(currtok)
                if  tokens[tok_id - 1][3] == 'V' and currtok[3] in ['V', 'A', 'PARTCP']:
                    distant_frame = get_children_posrels(tokens, int(currtok[0]), long_marker_set, 
                                         usepos=usepos, usecase=usecase, useanim=useanim,
                                         splice=splice, strip=strip,
                                         posrels=['предик'])
                    if distant_frame != []:
                        for mediator in mediators:
                            mediator[8] = 9
                        frame.extend(distant_frame)

    for token in tokens:
        if token[8] == '_':
            token[8] = 0
        if pro:
            token[9] = token[9].replace('PRO', '')
    return frame

def extract(idict, croot, 
            minfreq, maxfreq, maxcon, minpts,
            usepos, pro, usecase, useanim, 
            splice, strip, 
            posfeats, negfeats, 
            posrels, negrels, prnegrels):
    """
    Find all sentences within idict,
    get them, extract frames.
    """
    relset_dict, totl = {}, len(idict)
    for i, (ifname, entries) in enumerate(idict.items()):
        print('{}/{} Extracting from {}'.format(i, totl, ifname))
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

                tokens = prepare_tokens(raw_tokens)

                # extract frame
                frame = extract_frame(tokens, tok_id,
                                      usepos, pro, usecase, useanim, 
                                      splice, strip, 
                                      posfeats, negfeats, 
                                      posrels, negrels, prnegrels)

                if len(frame) >= minpts:
                    if posrels == [] or posrels == () or \
                       any(token[7] in posrels for token in frame if token[0] != tok_id):
                        relset = get_relset(frame)
                        relset_dict.setdefault(relset, [])
                        if maxcon == -1 or len(relset_dict[relset]) < maxcon:
                            relset_dict[relset].append((tok_id, tokens, frame))

    clean = {}
    for relset, frames in relset_dict.items():
        if len(frames) >= minfreq:
            if maxfreq == -1 or len(frames) <= maxfreq:
                clean[relset] = frames
    return clean

def extract_frames(lemma, iroot, croot, jsonpath, usepos=False,
                   usecase=False, pro=False, useanim=False, splice=False, strip=False,
                   posfeats=(), negfeats=(), posrels=(), negrels=(), prnegrels=(),
                   minfreq=2, maxfreq=-1, maxcon=100, minpts=1):
    """
    Extract frames from Alpha to Omega.
    """
    try:
        print('Extracting index for {}, {}'.format(*lemma))
        idict = get_index(lemma, iroot)
        print('Done extracting index')
    except FileNotFoundError:
        print('Failed')
        return {'error':'FileNotFoundError'}

    print('Extracting constructions')
    relset_dict = extract(idict, croot, minfreq, maxfreq, maxcon, minpts, 
                          usepos, pro, usecase, useanim, splice, strip,
                          posfeats=posfeats, negfeats=negfeats,
                          posrels=posrels, negrels=negrels, prnegrels=prnegrels)
    print('Done extracting constructions')

    if relset_dict == {}:
        print('No constructions found')
        return {'json':'', 'classes':[], 'frames':[], 'error':'NoExtract'}

    total = 0
    for relset_class, frames in relset_dict.items():
        total += len(frames)

    if total > hardcap:
        print('Too many constructions found')
        return {'json':'', 'classes':[], 'frames':[], 'error':'TooMany'}

    print('Classifying constructions')
    relset_classes, relset_ids = get_relset_classes(relset_dict)

    #with open('classes.log', 'w', encoding='utf-8') as clfile:
    #    for relset_class in relset_classes:
    #        clfile.write(str(relset_class) + '\n')

    relset_levels = get_relset_levels(relset_classes)
    print('Done classifying constructions')

    print('Making class graph')
    make_json_digraph(relset_levels, relset_ids, jsonpath)
    print('Done making class graph')

    relset_classes = [', '.join(relset_class) for relset_class in relset_classes]
    relset_dict = {', '.join(relset_class):frames for relset_class, frames in relset_dict.items()}

    print('Extraction successful')
    return {'json':os.path.join('.', 'static', 'json', os.path.basename(jsonpath)), 'classes':relset_classes, 'frames':relset_dict, 'error':'NoError'}
