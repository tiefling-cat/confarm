import os

def get_fnames(ifolder, ofolder, ext, postfix, plain=False):
    ifname_list, ofname_list = [], []
    if not os.path.exists(ofolder):
        os.makedirs(ofolder)
    for root, subdirs, fnames in os.walk(ifolder):
        for fname in fnames:
            if fname.endswith(ext):
                ifname_list.append(os.path.join(root, fname))
                ofname = fname.replace(ext, postfix)
                if plain: # just output everything to ofolder
                    ofname_list.append(os.path.join(ofolder, ofname))
                else: # recreate subfolder structure
                    osubfolder = root.replace(ifolder, ofolder)
                    if not os.path.exists(osubfolder):
	                    os.makedirs(osubfolder)
                    ofname_list.append(os.path.join(osubfolder, ofname))
    return ifname_list, ofname_list

def parsefile(fname):
    """
    Break conll file into list of sentences,
    which are lists of tokens.
    """
    sents, cursent = [], []
    with open(fname, "r", encoding="utf-8") as ifile:
        for k, line in enumerate(ifile):
            if line == "\n":
                sents.append(cursent)
                cursent = []
            else:
                token = line.strip("\n").split("\t") + [str(k)]
                cursent.append(token)
    return sents
