#! /usr/bin/python3

import os, re, fnmatch, gc
from dirtools import parsefile

word_re = re.compile('^[а-яё]+[а-яё -]*$')

croot = "../SynTagRus2015Conll"
iroot = "../index-str"
threshold = 10000

def getflist(src):
    """
    Get paths to all conll files in src.
    """
    flist = []
    for root, dirnames, filenames in os.walk(src):
        for filename in fnmatch.filter(filenames, "*.conll"):
            flist.append(os.path.join(root, filename))
    flist.sort()
    return flist

def makeindex(flist, iroot, src):
    """
    Here we make our stand.
    """
    index = {}
    volume = len(flist)
    cfnum, toknum, fnum = 0, 0, 0

    for fname in flist:
        #print('Processing', fname)
        sents = parsefile(fname)
        fnum, cfnum = fnum + 1, cfnum + 1

        for j, sent in enumerate(sents):
            for token in sent:
                lemma = token[2].lower()
                if word_re.match(lemma): # need only words
                    key = ".".join([lemma, token[3]])
                    item = ";".join((os.path.relpath(fname, src), str(j), token[0], str(len(sent) - int(token[0])), token[-1]))
                    if not key in index:
                        index[key] = []
                        toknum += 1
                    index[key].append(item)

        # periodical dump
        if toknum >= threshold:
            print("{}/{} files total, {} tokens in {} files".format(fnum, volume, toknum, cfnum))
            dump(index, iroot)
            index = {}
            gc.collect()
            cfnum, toknum = 0, 0

    # dump what's left
    print("Last {}/{} files total, {} tokens in {} files".format(fnum, volume, toknum, cfnum))
    dump(index, iroot)
    print("Done")

def dump(index, iroot):
    """
    Dump a ready part of index into folders.
    """
    for key in index:
        fname = os.path.join(iroot, key[0], key + ".txt")
        try:
            with open(fname, "a", encoding="utf-8") as ofile:
                ofile.write('\n'.join(index[key]) + '\n')
        except OSError:
            print("Whoa, some shitfuck instead of a filename, har har har!")
            print(fname, key)

def mkdirs(root):
    """
    Make index folder for each letter.
    """
    for i in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя":
        folder = os.path.join(root, i)
        if not os.path.exists(folder):
            os.makedirs(folder)
                
if __name__ == "__main__":
    mkdirs(iroot)
    print("Building list of files")
    flist = getflist(croot)
    with open("flist.txt", "w", encoding="utf-8") as flistfile:
        for fname in flist:
            flistfile.write(fname + "\n")
    print("Processing {} files with {} tokens threshold".format(len(flist), threshold))
    makeindex(flist, iroot, croot)
