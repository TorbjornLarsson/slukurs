#!/usr/bin/env python3
# Skördar 2023 SLU forskarkursplaner och forskarkurstillfällen för arkivering i DSpace.
# Metadata tas från HTML filers body som dictionaries och konverteras till Dublin Core format.
# Skördningen sker iterativt om webservern har problem samt loggas i phdcourseharvest.log.
#
# Arkiveringen sker efter konvertering av HTML-filer som deklareras vara på iso8859-1 format men lagrats som windows-1252.
# Detta avhjälper kanske inte alla konverteringsproblem. Alla filer som misslyckats konverteras listas i phdcourse_not_converted.log. 

import argparse
import logging
import pandas as pd
import os
import requests
import pystache
import bs4
import json

logging.basicConfig(filename='phdcourseharvest.log', filemode='w', level=logging.DEBUG)
with open('phdcourse_not_converted.log', 'w') as f:
    f.write('')

# Kurstillfälleslistan ska först kompletteras med arkivbildare från json-filens enhetsbeskrivning.
# Hämta kursens json html, extrahera body och konvertera till ett dictionary.
def cadd(i, e1, e2, adr, df):
    adrc = str(adr)
    print(adrc)
    r = requests.get(adrc)
    if r.status_code != 200:
        e1 += 1
        df.at[i,'Kurskod'] = 'no json'
        return [df, e1, e2]
    dictj = json.loads(bs4.BeautifulSoup(r.content, features="lxml").find('body').decode_contents().strip(), strict=False)
    df.at[i,'Kurskod'] = str(pystache.render('{{Kurskod}}', dictj))
    df.at[i,'benamning'] = str(pystache.render('{{Benamning_sve}}', dictj))
    df.at[i,'Enhet'] = str(pystache.render('{{Enhet}}', dictj))

    # Hämta Enhetsnamn, och konvertera Läsår till sträng
    enhnamn = pd.read_table('slu_creatordept_231002.tsv', dtype=str)
    enh = str(pystache.render('{{Enhet}}', dictj))
    print(enh)
    enhr = enhnamn.loc[enhnamn['enhet'] == enh]
    if not enhr.empty:
        creator = enhr['creator'].iloc[0]
    else:
        e2 += 1
        creator = ''
        df.at[i,'Nr'] = '*'
    print(creator)
    df.at[i,'creator'] = creator
    df.at[i,'Läsår'] = df.at[i, 'Läsår'].zfill(4)
    return [df, e1, e2]

# Gör en dataframe kursvy från kurstillfällen tsv
courses = pd.read_table('phdkurstillfallen_2023.tsv', dtype=str)
dfvy = courses[['Nr','Kurskod','Anmkod','Läsår', 'Kurstillfälle','Kursplan sve','Kursplan eng','Json']].copy()
dfvy[['benämning','Enhet','creator']] = None
dfvy = dfvy[['Nr','Kurskod','Anmkod','Läsår','benämning','Enhet','creator','Kurstillfälle','Kursplan sve','Kursplan eng','Json']]

# Hämta kursens json adress från kursplaner tsv, och fyll i kursvyn
n = 0
err1 = 0
err2 = 0
for jsonadr in dfvy.iloc[:,10]:
    logging.info('Radindex: '+str(n))
    cmpath = "https://slukurs.slu.se/arkivering/"
    ccpath = os.path.join(cmpath, jsonadr.split('"')[1])
    [dfvy, err1, err2] = cadd(n, err1, err2, ccpath, dfvy)
    n += 1
    print('Preparerar rad:', n)
print('\nKursvyn klar:\n', dfvy)
dfvy.to_csv('vy_phdkurstillfallen_2023.tsv', sep="\t", index=False)
logging.debug('Antal rader som saknar json: '+str(err1))
logging.debug('Antal rader som saknar oid: '+str(err2))

# Skapa en arbetsfolder på simparch folderformat.
# Eftersom jsonfilerna saknar datuminfo tas det från kurstillfälleslistans läsår.

def dspace_simparch(dstmainpath, rowno):

    with open('dublin_core_phdkursplaner_2023.mustache') as f:
        dctempl = f.read()

    # Utöka vyn med en kolumn arkivbildare.fastställningsår för att kunna sortera, skapa foldrar och ta ner.
    coursecr = pd.read_table('vy_phdkurstillfallen_2023.tsv', dtype=str)
    coursecr = coursecr.assign(cryr = coursecr['creator'] + '.' + coursecr['Läsår'])
    
    cryrs = list(set(coursecr['cryr']))
    scryrs = sorted(cryrs)

    # En arkivbildare.kursår cr default är att börja från första raden 0 i sorterade listan.
    rnr = int(rowno)
    if rnr != 0:
        scryrs = scryrs[rnr:]

    for cr in scryrs:
        logging.info('Sorterade kursers radnummer: '+str(rnr))
        logging.info('Kurser: '+str(cr))
        df1 = coursecr[coursecr['cryr'] == cr]

        dstpath = os.path.join(dstmainpath, str(cr).split('.')[0], 'kursplaner_' + str(cr).split('.')[0],'Kursplaner ' + str(cr))
        logging.info('Folderpath: '+str(dstpath))
        os.makedirs(dstpath, exist_ok = True)
        
        with open(os.path.join(dstpath, 'contents'), 'w') as f:
            f.write('')

        dictjs = []
        courses = pd.DataFrame()

        for nr in df1['Nr']:
            logging.info('Kurstillfällenr: '+str(nr))

            ccnr = coursecr[coursecr['Nr'] == nr]

            # Skapa dataframe och dictionary för textunderlag till dublin core metadata fil.
            c = pd.DataFrame(columns=['Kurskod', 'benamning', 'filkod'])
            ccyr = str(ccnr[['Läsår']].values[0][0])
            ccc = str(ccnr[['Kurskod']].values[0][0])
            cfile = ccc+'.'+ccyr
            logging.info('Kurskod: '+ccc)
            logging.info('Filkod: '+cfile)

            dc = dict()
            dc['creator'] = df1['creator'].iloc[0]
            head_tail = os.path.split(dstpath)
            dc['itemtitle'] = head_tail[1]

            cmpath = "https://slukurs.slu.se/arkivering/"
            ccjn = os.path.join(cmpath, str(ccnr[['Json']].values[0][0]).split('"')[1])
            file = os.path.join(dstpath, cfile)
            filejson = file + '_json.html'
            os.system('curl "'+ccjn+'" | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filejson+'"')

            # Extrahera kursens metadata som en lista av strängar.
            with open(filejson) as f:
                content = f.read()
            dictj = json.loads(bs4.BeautifulSoup(content, features="lxml").find('body').decode_contents().strip(), strict=False)
            dictjs.append(str(dictj))

            cmc = str(ccnr[['Anmkod']].values[0][0])
            cmf =  str(ccnr[['Kurstillfälle']].values[0][0]).split('"')[1]
            filkod = ccc+'.'+cmc+'.'+ccyr
            file = os.path.join(dstpath, filkod)
            logging.info('Kurstillfälle: '+cmf)
            logging.info('Filkod: '+filkod)
            filehtml = file + '.html'
            filepdf = file + '.pdf'

            c.at[0, 'Kurskod'] = ccc
            c.at[0, 'benamning'] = str(pystache.render('{{Benamning_sve}}', dictj))
            c.at[1, 'Kurskod'] = ccc
            c.at[1, 'benamning'] = str(pystache.render('{{Benamning_eng}}', dictj))
            c.at[0, 'filkod'] = filkod
            c.at[1, 'filkod'] = filkod

            # Ta ner kurstillfällets filer, konvertera till pdf och lägg tilll pdf-filen i contents-filen
            pands1 = 'pandoc --pdf-engine=context -f html -t pdf -M pdfa=2a -c ./Static/bootstrap.min.css '
            pands2 = ' -s --template=tagged-report-template.context -M logopath="/home/torbjorn/archive-harvest/utveckling/test_slukurs-ark" -o '
            # Ta bort karaktärer som inte kan konverteras (iconv -c) eller som konverteras till unicode A0 - "non-breaking space" (sed).
            os.system('curl "'+cmf+'" | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filehtml+'"')
            r = os.system(pands1+'"'+filehtml+'"'+pands2+'"'+filepdf+'"')
            if r!= 0:
                with open('phdcourse_not_converted.log', 'a') as f:
                    f.write(filehtml+'\n')
            head_tail = os.path.split(filepdf)
            with open(os.path.join(dstpath, 'contents'), 'a') as f:
                f.write(head_tail[1]+'\n')

            ccsv = str(ccnr[['Kursplan sve']].values[0][0]).split('"')[1]                
            file = os.path.join(dstpath, cfile)
            filesvhtml = file + '_sv.html'
            filesvpdf = file + '_sv.pdf'
            os.system('curl "'+ccsv+'" | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filesvhtml+'"')
            r = os.system(pands1+'"'+filesvhtml+'"'+pands2+'"'+filesvpdf+'"')
            if r!= 0:
                with open('phdcourse_not_converted.log', 'a') as f:
                    f.write(filesvhtml+'\n')
            head_tail = os.path.split(filesvpdf)
            with open(os.path.join(dstpath, 'contents'), 'a') as f:
                f.write(head_tail[1]+'\n')

            ccen = str(ccnr[['Kursplan eng']].values[0][0]).split('"')[1]
            fileenhtml = file + '_en.html'
            fileenpdf = file + '_en.pdf'
            os.system('curl "'+ccen+'" | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+fileenhtml+'"')
            r = os.system(pands1+'"'+fileenhtml+'"'+pands2+'"'+fileenpdf+'"')
            if r!= 0:
                with open('course_not_converted.log', 'a') as f:
                    f.write(fileenhtml+'\n')
            head_tail = os.path.split(fileenpdf)
            with open(os.path.join(dstpath, 'contents'), 'a') as f:
                f.write(head_tail[1]+'\n')
            courses = pd.concat([courses,c])

            # Radera tempfiler
            os.system('find "'+dstpath+'" -type f -not \( -name '+'"'+'*.pdf'+'"'+ ' -or -name '+'"'+'contents'+'"'' \) -delete')

        # Skapa simparch collection fil med mönstret handle/collection.
        # Testsystemet har handle 123456789.

        head_tail1 = os.path.split(dstpath)
        head_tail2 = os.path.split(head_tail1[0])
        coll = '123456789/'+head_tail2[1]
        with open(os.path.join(dstpath, 'collections'), 'w') as f:
            f.write(coll)
            
        # Skapa simparch dublin core metadata fil.
        dc['dictjs'] = pd.DataFrame(dictjs, columns=['metadata']).to_dict('records')
        dc['courses'] = courses.to_dict('records')
        with open(os.path.join(dstpath, 'dublin_core.xml'), 'w') as f:
            f.write(pystache.render(dctempl, dc))

        # Uppdatera radnummer.
        rnr += 1 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='phdkursskordning.py',
                    description='Tar en srcmainpath folder, utökar den parsade kursvyn med cryr arkivbildare.faststallningsår, laddar ner kursplaner och metadata json och byter namn.', 
                    epilog='Argumenten är python3 phdkursskordning.py ~/srcmainfolder')
    parser.add_argument('path', help='Foldern där arkivstrukturen bildas.')
    parser.add_argument('rowno', help='Option att fortsätta skördning i den sorterade listan från loggade radnummer.', nargs='?', const='0', default='0')
    args = parser.parse_args()
    dspace_simparch(args.path, args.rowno)
