#! /usr/bin/python3

from flask import Flask, request, session, jsonify
from flask import render_template, make_response
from flask import redirect, url_for
from werkzeug import secure_filename
import uuid, os, sys
from utilities.simpl_ex import extract_frames as xf # nashe vsio

# BEGIN: UGLY MONKEYPATCH
import pkgutil
orig_get_loader = pkgutil.get_loader
def get_loader(name):
    try:
        return orig_get_loader(name)
    except AttributeError:
        pass
pkgutil.get_loader = get_loader
# END: UGLY MONKEYPATCH

app = Flask(__name__)

app.config.from_pyfile(os.path.join(os.path.dirname(__file__), 'config.py'))

iroot_stgr = app.config['STR_INDEX']
croot_stgr = app.config['STR_CORPS']
iroot_post = app.config['POST50_INDEX']
croot_post = app.config['POST50_CORPS']
pfldr = app.config['PIC_FOLDR']
jsonfldr = app.config['JSON_FOLDR']

corpora = {'post':(iroot_post, croot_post), 'stgr':(iroot_stgr, croot_stgr)}

secret_path = app.config['FLASK_SECRET']
with open(secret_path, 'rb') as fd:
    app.secret_key = fd.read()

@app.route('/')
def index():
    """
    Render About ConFarm page.
    """
    return render_template('index.html')

@app.route('/extract')
def extract():
    """
    Render Farm Constructions page.
    """
    return render_template('extract.html', enumerate=enumerate)

def parse_tagsinput(inputname):
    """
    Parse tagsinput value.
    """
    value = request.values[inputname]
    if value == '':
        return []
    return value.split(',')

@app.route('/json/extracted')
def extract_frames():
    """
    Get options, extract constructions, return them.
    """
    lemma = request.values.get('lemma', '')
    pos = request.values.get('pos', '')
    usepos = (request.values.get('usepos', 'false') == 'true')
    pro = (request.values.get('pro', 'false') == 'true')
    usecase = (request.values.get('usecase', 'false') == 'true')
    useanim = (request.values.get('useanim', 'false') == 'true')
    splice = (request.values.get('splice', 'false') == 'true')
    strip = (request.values.get('strip', 'false') == 'true')
    threshold = int(request.values.get('threshold', 1))
    posfeats = parse_tagsinput('posfeats')
    negfeats = parse_tagsinput('negfeats')
    posrels = parse_tagsinput('posrels')
    negrels = parse_tagsinput('negrels')
    prnegrels = parse_tagsinput('prnegrels')

    corpus = request.values.get('corpus', '')
    iroot, croot = corpora[corpus]

    with open('params.log', 'a', encoding='utf-8') as pfile:
        pfile.write('\t'.join([lemma, pos, str(usepos), str(pro), str(usecase), str(useanim), str(splice), str(strip), str(threshold)]) + '\n' + 
                    '\n'.join([str(posfeats), str(negfeats), str(posrels), str(negrels), str(prnegrels), iroot, croot]))

    if lemma != '':
        jsonpath = os.path.join(jsonfldr, str(uuid.uuid4()) + '.json')
        extracted = xf((lemma, pos), iroot=iroot, croot=croot, jsonpath=jsonpath, usepos=usepos,
                       usecase=usecase, pro=pro, useanim=useanim, splice=splice, strip=strip,
                       posfeats=posfeats, negfeats=negfeats, posrels=posrels, negrels=negrels, prnegrels=prnegrels,
                       threshold=threshold)
    else:
        extracted = {}

    return jsonify(extracted)

if __name__ == '__main__':
    app.run(debug=True)
