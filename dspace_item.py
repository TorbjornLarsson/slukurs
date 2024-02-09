#!/usr/bin/env python3
import glob
import os
import pandas as pd
import pystache
import shutil

with open('dublin_core.mustache') as f:
    dctempl = f.read()

with open('dublin_core_ramschema.mustache') as f:
    dcramtempl = f.read()

with open('dublin_core_utbplan.mustache') as f:
    dcutbtempl = f.read()

with open('contents.mustache') as f:
    conttempl = f.read()

coursecr = pd.read_table('vy_kurstillfalle-slu_creatordept.tsv')
coursecr = coursecr.assign(cryr =
                coursecr['creator'] + '.' + coursecr['anmkod'].str.split('.').str.get(1))
cryrs = list(set(coursecr['cryr']))

ram = pd.read_table('ramschema_rel.tsv')
ram = ram.assign(anmkod = ram['Läsår_link0'].str.split('=').str.get(-1))
ram = ram.assign(cryr = 'ua.' + ram['anmkod'].str.split('.').str.get(1))

utbpl = pd.read_table('utbplan_rel.tsv')

hdlcr = pd.read_table('dspace_creators_test.tsv',
                      index_col='creator').to_dict('index')

def planfiles(acode):
    return [acode + '.en.short.pdf', acode + '.sv.short.pdf']

def dspace_simparch(srcmainpath, dstmainpath, cryr, metaonly):
    dstpath = os.path.join(dstmainpath, 'item_' + cryr)
    df = coursecr[coursecr['cryr'] == cryr]
    dc = dict()
    creator = cryr.split('.')[0]
    dc['creator'] = creator
    dc['itemtitle'] = 'Kursplaner ' + cryr
    dc['courses'] = df.to_dict('records')
    dc['sluids'] = []
    coll = hdlcr[creator]['handle']
    acodes = list(df['anmkod'])
    pfs = list()
    for ac in acodes:
        pfs += planfiles(ac)
    pfs = list(filter(lambda f: os.path.join(srcmainpath, f) in
                      glob.glob(os.path.join(srcmainpath, '*')), pfs))
    if len(pfs) > 0:
        os.makedirs(dstpath, exist_ok = True)
        srcpaths = list(map(lambda f: os.path.join(srcmainpath, f), pfs))
        dstpaths = list(map(lambda f: os.path.join(dstpath, f), pfs))
        filenames = list(map(lambda f: {'filename': f}, pfs))
        with open(os.path.join(dstpath, 'collections'), 'w') as f:
            f.write(coll)
        with open(os.path.join(dstpath, 'contents'), 'w') as f:
            f.write(pystache.render(conttempl, {'itemfiles': filenames}))
        with open(os.path.join(dstpath, 'dublin_core.xml'), 'w') as f:
            f.write(pystache.render(dctempl, dc))
        if not(metaonly):
            for s, d in zip(srcpaths, dstpaths):
                shutil.copy(s, d)
