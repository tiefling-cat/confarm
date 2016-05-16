#! /usr/bin/python3

import glob, os, shutil, re, sys, json
import lxml.etree as ET
from subprocess import call
from dirtools import get_fnames

# about mystem -----------------------------------------------------------
mystem_options = [
        './mystem_ruscorpora',
        '--format=json', # plaintext at input, json at output
        '-i', # print grammar tags
        '-d', # use lexical disambiguation
        '-c', # copy input onto output
        '--eng-gr', # grammar tags in English
        '--language=ru'
    ]
#-------------------------------------------------------------------------

gender = (re.compile(r'\b((МУЖ)|(ЖЕН)|(СРЕД))\b'), {'МУЖ':'m', 'ЖЕН':'f', 'СРЕД':'n'}, '-')
number = (re.compile(r'\b((ЕД)|(МН))\b'), {'ЕД':'sg', 'МН':'pl'}, '-')
anim = (re.compile(r'\b((ОД)|(НЕОД))\b'), {'ОД':'anim', 'НЕОД':'inan'}, '-')
case = (re.compile(r'\b((ИМ)|(РОД)|(ДАТ)|(ВИН)|(ТВОР)|(ПР)|(ПАРТ)|(МЕСТН)|(ЗВ)|(НЕСКЛ))\b'), 
		{'ИМ':'nom', 'РОД':'gen', 'ДАТ':'dat', 'ВИН':'acc', 'ТВОР':'ins', 
		 'ПР':'loc', 'ПАРТ':'part', 'МЕСТН':'loc2', 'ЗВ':'voc', 'НЕСКЛ':'nonflex'}, '-')
brev = (re.compile(r'\b((КР))\b'), {'КР':'brev'}, 'plen')
relat = (re.compile(r'\b((СРАВ)|(ПРЕВ))\b'), {'СРАВ':'comp', 'ПРЕВ':'supr'}, '-')
#tense = (re.compile(r'\b((НЕПРОШ)|(ПРОШ)|(НАСТ))\b'), {'НЕПРОШ':'inpraes', 'ПРОШ':'praet', 'НАСТ':'inpraes'}, '-')
tense = (re.compile(r'\b((ПРОШ)|(НАСТ)|(БУДУЩ))\b'), {'ПРОШ':'praet', 'НАСТ':'praes', 'БУДУЩ':'fut'}, '-')
aspect = (re.compile(r'\b((НЕСОВ)|(СОВ))\b'), {'НЕСОВ':'ipf', 'СОВ':'pf'}, '-')
repres = (re.compile(r'\b((ИЗЪЯВ)|(ПОВ)|(ИНФ)|(ДЕЕПР))\b'), {'ИЗЪЯВ':'indic', 'ПОВ':'imper', 'ИНФ':'inf', 'ДЕЕПР':'ger'}, '-')
person = (re.compile(r'\b([123]-Л)\b'), {'1-Л':'1p', '2-Л':'2p', '3-Л':'3p'}, '-')
voice = (re.compile(r'\b((СТРАД))\b'), {'СТРАД':'pass'}, 'act')
dim_re = re.compile(r'\bСМЯГ\b')

S_feats = (gender, anim, case, number)
A_feats = (relat, case, number, brev, gender, anim)
ADV_feats = (relat,)
NUM_feats = (case, gender, anim)
V_feats = (aspect, tense, number, repres, gender, person)
PARTCP_feats = (aspect, tense, case, number, brev, gender, voice, anim)

ms_gender = re.compile(r'\b[mfn]\b')
ms_number = re.compile(r'\b(sg|pl)\b')
ms_case = re.compile(r'\b(nom|gen|dat|acc|ins|loc|part|abl|voc)\b')
ms_casenum = re.compile(r'\b(nom|gen|dat|acc|ins|loc|part|abl|voc) (sg|pl)\b')

empty_adv = ('ADV', (['-'], []))

gtfo_tags = ['СЛ', 'НЕСТАНД', 'НЕПРАВ', 'МЕТА']
repl_part_dict = {'УЖЕ':empty_adv, 'ЕЩЕ':empty_adv, 'ПОЧТИ':empty_adv, 'ТАКЖЕ':empty_adv, 'ЧУТЬ':empty_adv}
repl_part_list = ['УЖЕ', 'ЕЩЕ', 'ПОЧТИ', 'ТАКЖЕ', 'ЧУТЬ']

spro_dict = {
    'Я':['sg', '1p', '-'],
    'МЫ':['pl', '1p', '-'],
    'ТЫ':['sg', '2p', '-'],
    'ВЫ':['pl', '2p', '-'],
    'ОН':['sg', '3p', 'm'],
    'ОНА':['sg', '3p', 'f'], 
    'ОНО':['sg', '3p', 'n'], 
    'ОНИ':['pl', '-', '-'],
    'СЕБЯ':['-', '-', '-']
    }

apro_list = ['его', 'ее', 'их']

def convert_feat(feat, feat_line):
    match = feat[0].search(feat_line)
    if match:
        return feat[1][match.group(0)], match.group(0)
    return feat[2], ''

def munch_feats(POS_feats, feat_line):
    for tag in gtfo_tags:
        feat_line = feat_line.replace(tag, '')
    converts, finds = [], []
    for feat in POS_feats:
        convert, find = convert_feat(feat, feat_line)
        converts.append(convert)
        finds.append(find)
    rejects = [feat for feat in feat_line.split() if feat not in finds]
    return converts, rejects

def detect_nonflex(analyses):
    all_feats = ' '.join([analysis.get('gr', '').replace(',', ' ').replace('=', ' ') 
                                for analysis in analyses])
    casenums = set(ms_casenum.findall(all_feats))
    if len(casenums) >= 12:
        return True, True
    elif len(casenums) >= 6:
        numcases = {}
        for (case, num) in casenums:
            numcases.setdefault(num, [])
            numcases[num].append(case)
        for num in numcases:
            numcases[num] = set(numcases[num])
        if any(len(cases) for cases in numcases.values()) >= 6:
            return True, False
    return False, False

def convert_feats(feat_line, lemma, text, reltype, mystemized):
    pos = feat_line.split(' ', 1)[0]
    feat_line = feat_line.replace(pos, '')
    if pos == 'S':
        if text in apro_list and reltype in ['квазиагент', 'атриб', 'опред']:
            return 'A', (['-', 'nonflex', 'nonflex', 'plen', '-', '-'], []), text.upper()

        if lemma in spro_dict:
            pos = 'SPRO'
            convert, find = convert_feat(case, feat_line)
            feats = spro_dict[lemma] + [convert]
            return pos, (feats, []), None

        if lemma == 'КОТОРЫЙ':
            return 'A', munch_feats(A_feats, feat_line), None

        analyses = mystemized[0].get('analysis', [])
        if len(analyses) >= 6:
            converts, rejects = munch_feats(S_feats, feat_line)
            nf_case, nf_number = detect_nonflex(analyses)
            if nf_case:
                converts[2] = 'nonflex'
            if nf_number:
                converts[3] = 'nonflex'
            return pos, (converts, rejects), None

        return pos, munch_feats(S_feats, feat_line), None
    if pos == 'A':
        if dim_re.search(feat_line) is not None:
            return pos, (['comp2', '-', '-', 'plen', '-', '-'], []), None
        return pos, munch_feats(A_feats, feat_line), None
    if pos == 'ADV':
        if dim_re.search(feat_line) is not None:
            return pos, (['comp2'], []), None
        return pos, munch_feats(ADV_feats, feat_line), None
    if pos == 'NUM':
        if lemma == 'ОДИН':
            return 'A', munch_feats(A_feats, feat_line), None
        return pos, munch_feats(NUM_feats, feat_line), None
    if pos == 'V':
        if 'ПРИЧ' not in feat_line:
            if 'НЕСОВ' in feat_line:
                feat_line = feat_line.replace('НЕПРОШ', 'НАСТ')
            elif 'СОВ' in feat_line:
                feat_line = feat_line.replace('НЕПРОШ', 'БУДУЩ')
            return pos, munch_feats(V_feats, feat_line), None
        else:
            feat_line = feat_line.replace('НЕПРОШ', 'НАСТ')
            return 'PARTCP', munch_feats(PARTCP_feats, feat_line.replace('ПРИЧ', '')), None
    if pos == 'NID':
        return 'NONLEX', ([], []), None
    if pos == 'PART' and lemma in repl_part_list:
        return 'ADV', (['-'], []), None
    return pos, ([], []), None

def mystemize_tokens(filename):
    tempfolder = 'tmp'
    if not os.path.exists(tempfolder):
        os.makedirs(tempfolder)
    tree = ET.parse(filename)
    root = tree.getroot()
    text = ''
    temp_i_fname = os.path.join(tempfolder, 'temp1.txt')
    temp_o_fname = os.path.join(tempfolder, 'temp2.txt')
    with open(temp_i_fname, 'w', encoding='utf-8') as dumpfile:
        for sentence in root[-1].findall('S'):
            for token in sentence.findall('W'):
                if token.text is not None:
                    dumpfile.write(token.text)
                dumpfile.write('\n')
    call(mystem_options + [temp_i_fname, temp_o_fname])
    return (json.loads(line) for line in open(temp_o_fname, 'r', encoding='utf-8'))

def munch(ifiles, ofiles):
    """
    Process all files in ifiles list.
    Output into ofiles list.
    """
    for ifname, ofname in zip(ifiles, ofiles):
        print('Processing', ifname)
        print('Storing to', ofname)
        mystemized_gen = mystemize_tokens(ifname)
        tree = ET.parse(ifname)
        root = tree.getroot()

        for sentence in root.find('body').findall('S'):

            # scan for phantoms and remove sentence altogether if found
            if any('NODETYPE' in word.attrib for word in sentence.findall('W')):
                sentence.getparent().remove(sentence)
                continue

            # remove LFs
            if 'CLASS' in sentence.attrib:
                sentence.attrib.pop('CLASS')
                for lfshit in sentence.findall('LF'):
                    lfshit.getparent().remove(lfshit)

            # reassign feats
            for token in sentence.findall('W'):
                mystemized = next(mystemized_gen)
                text = token.text
                if text is not None:
                    text = text.strip().lower()

                if 'FEAT' in token.attrib:
                    pos, (feats, rejects), rep_lemma = convert_feats(token.attrib['FEAT'], 
                                                                     token.attrib.get('LEMMA', ''),
                                                                     text, token.attrib.get('LINK', ''),
                                                                     mystemized)

                    if rejects != [] and rejects != ['СТРАД']:
                        print(token.text, token.attrib.get('FEAT', 'NOFEAT'), pos, ' '.join(feats), rejects)

                    token.attrib['FEAT'] = ' '.join([pos] + feats).strip()
                    if rep_lemma is not None:
                        token.attrib['LEMMA'] = rep_lemma

        tree.write(ofname, encoding = 'utf-8')

if __name__ == "__main__":
    munch(*get_fnames('../SynTagRus2015', '../FeatConv', '.tgt', '.xml'))
    #munch(*get_fnames('Testing', 'Testing', '.tgt', '.xml'))
