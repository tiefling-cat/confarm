#! /usr/bin/python3

from time import process_time
from lxml import etree
import os

ifolder = '/home/nm/corpus/pre1950'
ofolder = '/home/nm/corpus-txt/pre1950'

def safe_str(text):
    if text is not None:
        return text
    return ''

def get_fname_lists(ifolder, ofolder):
    start = process_time()
    ifname_list, ofname_list = [], []
    for root, subdirs, fnames in os.walk(ifolder):
        for fname in fnames:
            if not fname.endswith('.conll'):
                ifname = os.path.join(root, fname)
                ifname_list.append(ifname)
                ofname = os.path.splitext(ifname)[0].replace(ifolder, ofolder) + '.txt'
                ofname_list.append(ofname)
                if not os.path.exists(os.path.dirname(ofname)):
                    os.makedirs(os.path.dirname(ofname))
    print('Listed/created folders in {:.3f} sec'.format(process_time() - start))
    return ifname_list, ofname_list

def xml_to_txt(ifname, ofname):
    try:
        if not os.path.exists(ofname):
            root = etree.parse(ifname).getroot()
            with open(ofname, 'w', encoding='utf-8') as ofile:
                for par in root.find('body').findall('p'):
                    tail = safe_str(par.tail)
                    tail = tail if tail != '' else '\n'
                    text = (safe_str(par.text) + tail).replace('--', '—')
                    ofile.write(text)
    except etree.XMLSyntaxError:
        print('Fucked up at', ifname)

def convert_all(ifname_list, ofname_list):
    start = process_time()
    for ifname, ofname in zip(ifname_list, ofname_list):
        if not os.path.exists(ofname):
            xml_to_txt(ifname, ofname)
    print('Converted files in {:.3f} sec'.format(process_time() - start))

if __name__ == "__main__":
    ifnames, ofnames = get_fname_lists(ifolder, ofolder)
    convert_all(ifnames, ofnames)

