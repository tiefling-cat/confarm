#! /usr/bin/python3

import os
from simpl_ex import prepare_tokens, extract_frame
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
                tokens = prepare_tokens(raw_sent.split('\n'))
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
                frame = extract_frame(tokens, tok_id, 
                                 usepos=True, pro = True,
                                 usecase=True, useanim=False,
                                 splice=False, strip=False, 
                                 posfeats = (), negfeats = (),
                                 posrels = (),
                                 negrels=('аналит', 'огранич', 'вводн', 'разъяснит'), 
                                 prnegrels=())
                frame.append(tokens[tok_id - 1])
            except IndexError:
                print('Another shitfuck at', ifname)
                print(word, tok_id)
                for token in tokens:
                    print(token)
            #con_sents.append((tok_id, tokens, frame))
            ofile.write('-' * 75 + '\n')
            ofile.write('{}\t{}\n'.format(ifname.split('.')[0], word))
            ofile.write('-' * 75 + '\n\n')
            frame.sort(key=lambda token: int(token[0]))
            for token in frame:
                ofile.write('\t'.join(token[:2] + [str(token[8]), token[9]]) + '\n')
            ofile.write('\n')
            for token in tokens:
                ofile.write('\t'.join(token[:8] + [str(token[8]), token[9]]) + '\n')
            ofile.write('\n')
    ofile.close()

if __name__ == "__main__":
    extract(croot, False, False, (), (), ())
