#! /usr/bin/python3

import re, glob, os
import lxml.etree as ET
from dirtools import get_fnames

def get_pos_feat(line):
    """
    No time to explain.
    Just get pos and feat.
    """
    feats = line.split(' ')
    pos = feats[0]
    feat = ''.join(feats[1:]).lower()
    if feat == '': # empty feat
        feat = 'ZERO'
    return pos, feat

def flush_tokens(ifname, sent_id, ofile, token_list, id_map):
    """
    Here our sentence finally makes it to the file.
    """

    try:
        terminal = token_list[-1] # correct pos and feat for terminal symbol
        if not re.match('^[А-ЯЁа-яё-]$', terminal[1]): # if it's a word, don't touch it
            token_list[-1] = terminal[0:3] + ('SENT', 'SENT', 'SENT') + terminal[6:]
        for token in token_list:
            if token[7] in ['PUNC', 'SENT']: # PUNCs and SENTs already have correct domains
                ofile.write('\t'.join(token) + '\n')
            else: # for others, we correct it via id_map
                try:
                    ofile.write('\t'.join(list(token[:6]) + [id_map[token[6]]] + list(token[7:])) + '\n')
                except KeyError: # if id is not in the map, something went wrong
                    ids = list(id_map.keys())
                    ids.sort(key = lambda x: int(x))
                    print('Error in {}, {} at'.format(ifname, sent_id), token)
                    print(' '.join(['({}:{})'.format(map_id, id_map[map_id]) for map_id in ids]))
                    for token in token_list:
                        try:
                            print('\t'.join(list(token[:6]) + [id_map[token[6]]] + list(token[7:])))
                        except KeyError:
                            print('!!! ' + '\t'.join(token))
                    print()
        ofile.write('\n')
    except IndexError:
        pass

def get_fucking_punc(punc, punc_id, token_id, offset, before=True):
    """
    Here we deal with PUNCs by making tokens out of them.
    """
    true_id = punc_id + offset
    true_dom = token_id + offset
    if before: # PUNC is BEFORE the token
        punc_token = (str(true_id), punc, punc, 'PUNC', punc, '_', str(true_dom + 1), 'PUNC', '_', '_')
    else: # PUNC is AFTER the token
        punc_token = (str(true_id + 1), punc, punc, 'PUNC', punc, '_', str(true_dom), 'PUNC', '_', '_')
    return punc_token

def parse(token, prev_token):
    """
    Everything you wanted to know about your token.
    """
    if prev_token.tag == 'S':
        punc_before = prev_token.text.split('\n')[-1].strip()
    else:
        punc_before = prev_token.tail.split('\n')[-1]
    punc_after = token.tail.split('\n')[0].split()
    punc_after_divided = []
    for punc in punc_after:
        punc_after_divided.extend(list(punc))
    feats = token.attrib['FEAT'].split(' ', maxsplit=1)
    if len(feats) == 2:
        pos, feat = feats[0], feats[1]
    elif len(feats) == 1:
        pos, feat = feats[0], '_'
    else:
        pos, feat = '_', '_'
    if token.attrib['DOM'] == '_root':
        dom, link = '0', 'root'
    else:
        dom, link = token.attrib['DOM'], token.attrib['LINK']
    form = token.text
    lemma = token.attrib['LEMMA']
    token_id = int(token.attrib['ID'])
    return punc_before, pos, feat, token_id, form, lemma, dom, link, punc_after_divided

def munch_token(token, prev_token, id_offset, token_list, id_map):
    """
    As it says on the tin,
    this day we get the token,
    and not the token gets us.
    """
    punc_before, pos, feat, token_id, form, lemma, dom, link, punc_after = parse(token, prev_token)

    if punc_before: # found fucking punctuation before the token
        punc_token_before = get_fucking_punc(punc_before, token_id, token_id, id_offset, before=True)
        token_list.append(punc_token_before)
        id_offset += 1

    token = (str(token_id + id_offset), form, lemma, pos, '_', feat, dom, link, '_', '_')
    token_list.append(token)

    if punc_after: # found punctuation after the token
        for i, punc in enumerate(punc_after): # there can be many of them!
            punc_token_after = get_fucking_punc(punc, token_id + i, token_id, id_offset, before=False)
            token_list.append(punc_token_after)
    id_map[str(token_id)] = str(token_id + id_offset)

    if punc_after: # change offset if there is punctuation after the token
        id_offset += len(punc_after)
    return id_offset

def init_map_list_and_offset():
    return {'0':'0'}, [], 0

def xml_to_conll(ifname, ofname):
    """
    Converter function.
    """
    with open(ofname, 'w', encoding='utf-8') as ofile:
        tree = ET.parse(ifname)
        root = tree.getroot()
        for sentence in root[-1].findall('S'):

            # start of sentence
            id_map, token_list, id_offset = init_map_list_and_offset()
            prev_token = sentence
            for token in sentence.findall('W'):
                id_offset = munch_token(token, prev_token, id_offset, token_list, id_map)
                prev_token = token

            # end of sentence
            flush_tokens(os.path.basename(ifname), sentence.attrib.get('ID', None), ofile, token_list, id_map)

if __name__ == "__main__":
    ifnames, ofnames = get_fnames('/home/nm/syntagrus-annotated', '/home/nm/syntagrus-reannotated', '.xml', '.conll')
    for ifname, ofname in zip(ifnames, ofnames):
        print('Processing', ifname)
        print('Storing to', ofname)
        xml_to_conll(ifname, ofname)
