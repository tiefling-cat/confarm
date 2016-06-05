#! /usr/bin/python3

from flask import Flask, request, session, jsonify
from flask import render_template, make_response
from flask import redirect, url_for
from werkzeug import secure_filename
import uuid, os, sys
from utilities.simpl_ex import extract_frames as xf

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

features = [('inf', 'Infinitive'), ('pf', 'Perfective'), ('ipf', 'Imperfective')]
relations = ['вводн', 'обст', 'сравн']

app = Flask(__name__)

app.config.from_pyfile(os.path.join(os.path.dirname(__file__), 'config_local.py'))

secret_path = app.config['FLASK_SECRET']

iroot_stgr = app.config['STR_INDEX']
croot_stgr = app.config['STR_CORPS']
iroot_post = app.config['POST50_INDEX']
croot_post = app.config['POST50_CORPS']

pfldr = app.config['PIC_FOLDR']
jsonfldr = app.config['JSON_FOLDR']

corpora = {'post':(iroot_post, croot_post), 'stgr':(iroot_stgr, croot_stgr)}

if not os.path.exists(os.path.join(os.path.dirname(__file__), 'flask-secret')):
    with open(os.path.join(os.path.dirname(__file__), 'flask-secret'), 'wb') as fd:
        fd.write(os.urandom(16))

with open(secret_path, 'rb') as fd:
    app.secret_key = fd.read()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract')
def extract():
    return render_template('extract.html', features=features, relations=relations, enumerate=enumerate)

def get_feats(featsname):
    feats = request.values[featsname]
    if feats == '':
        return []
    return feats.split(',')

@app.route('/json/extracted')
def extract_frames():
    lemma = request.values.get('lemma', '')
    pos = request.values.get('pos', '')
    usepos = (request.values.get('usepos', 'false') == 'true')
    usecase = (request.values.get('usecase', 'false') == 'true')
    useanim = (request.values.get('useanim', 'false') == 'true')
    splice = (request.values.get('splice', 'false') == 'true')
    strip = (request.values.get('strip', 'false') == 'true')
    threshold = int(request.values.get('threshold', 1))
    posfeats = get_feats('posfeats')
    negfeats = get_feats('negfeats')
    posrels = get_feats('posrels')
    negrels = get_feats('negrels')
    prnegrels = get_feats('prnegrels')

    corpus = request.values.get('corpus', '')
    iroot, croot = corpora[corpus]

    with open('params.log', 'a', encoding='utf-8') as pfile:
        pfile.write('\t'.join([lemma, pos, str(usepos), str(usecase), str(useanim), str(splice), str(strip), str(threshold)]) + '\n' + 
                    '\n'.join([str(posfeats), str(negfeats), str(posrels), str(negrels), str(prnegrels), iroot, croot]))

    if lemma != '':
        jsonpath = os.path.join(jsonfldr, str(uuid.uuid4()) + '.json')
        extracted = xf((lemma, pos), iroot=iroot, croot=croot, jsonpath=jsonpath, usepos=usepos,
                       usecase=usecase, useanim=useanim, splice=splice, strip=strip,
                       posfeats=posfeats, negfeats=negfeats, posrels=posrels, negrels=negrels, prnegrels=prnegrels,
                       threshold=threshold)
    else:
        extracted = {}

    return jsonify(extracted)

if __name__ == '__main__':
    app.run(debug=True)
