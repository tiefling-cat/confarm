#! /usr/bin/python3

import os
from simpl_ex import get_children
croot = '/home/nm/repos/confarm/sqlframebank/examples-annotated'

def extract(croot, splice, strip, posrels, negrels, prnegrels):
    """
    Find all sentences within idict,
    get them, extract frames.
    """
    con_sents = []
    ifnames = os.listdir(croot)
    ifnames.sort(key = lambda ifname: int(ifname.split('.')[0]))
    ofile = open('/home/nm/repos/confarm/sqlframebank/examples-extracted.txt', 'w', encoding='utf-8')
    for ifname in ifnames:
        word = ifname.split('.')[1].lower().strip('.,!?;:)(«»"')
        path = os.path.join(croot, ifname)
        with open(path, 'r', encoding='utf-8') as ifile:
            raw_sents = ifile.read().split('\n\n')[:-1]
        tok_id = None
        for raw_sent in raw_sents:
            if tok_id is None:
                raw_tokens = raw_sent.split('\n')
                tokens = []
                for token in raw_tokens:
                    token = token.strip().split('\t')
                    token[4] = token[3]
                    if token[5][0].isupper():
                        try:
                            token[5] = token[5].split(' ', maxsplit=1)[1]
                        except IndexError:
                            token[5] = '_'
                    tokens.append(token)
                for token in tokens:
                    try:
                        if token[1].lower().strip('.,!?;:)(«»"') == word:
                            tok_id = int(token[0])
                    except IndexError:
                        print(raw_sent)
        if tok_id is None:
            print('Shitfuck at', ifname)
        else:
            # extract frame
            try:
                frame = get_children(tokens, tok_id, usepos=True,
                                 usecase=True, useanim=False,
                                 splice=splice, strip=strip, 
                                 negrels=negrels, prnegrels=prnegrels)
            except IndexError:
                print('Another shitfuck at', ifname)
                print(word, tok_id)
                for token in tokens:
                    print(token)
            #con_sents.append((tok_id, tokens, frame))
            ofile.write('-' * 75 + '\n')
            ofile.write('{}\t{}\n'.format(ifname.split('.')[0], word))
            ofile.write('-' * 75 + '\n\n')
            for token in frame:
                ofile.write('\t'.join(token[:2] + [str(token[8]), token[9]]) + '\n')
            ofile.write('\n')
            for token in tokens:
                ofile.write('\t'.join(token[:8] + [str(token[8]), token[9]]) + '\n')
            ofile.write('\n')
    ofile.close()

if __name__ == "__main__":
    extract(croot, False, False, (), (), ())
