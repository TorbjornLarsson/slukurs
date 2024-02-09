#!/usr/bin/env python3
# Skördar 2023 SLU kursplaner och kurstillfällen för arkivering i DSpace.
# Metadata tas från HTML filers body som dictionaries och konverteras till Dublin Core format.
# Skördningen sker iterativt om webservern har problem samt loggas i courseharvest.log.
#
# Arkiveringen sker efter konvertering av HTML-filer som deklareras vara på iso8859-1 format men lagrats som windows-1252.
# Detta avhjälper kanske inte alla konverteringsproblem. Alla filer som misslyckats konverteras listas i course_not_converted.log. 

import argparse
import logging
import os
import pandas as pd
import pystache
import bs4
import json

logging.basicConfig(filename='courseharvest.log', filemode='w', level=logging.DEBUG)
with open('course_not_converted.log', 'w') as f:
    f.write('')

# Skapa en arbetsfolder på simparch folderformat.
# Curla först ner filerna från den mer kompletta kurskodslistan.
# Komplettera sedan med eventuella kurstillfällen från kurstillfälleslistan,
# efter att den kontrollerats för att kurskodslistan inte saknar kurskod för kurstillfällen. 
# (Till exempel med korskontroll_kurstillfallen_kursplaner.py.)
# Det här förfarandet kan strömlinjeformas i framtiden beroende på hur kurser listas på servern. 

def dspace_simparch(dstmainpath, rowno):

    with open('dublin_core_kursplaner_2023.mustache') as f:
        dctempl = f.read()

    # Utöka vyn med en kolumn arkivbildare.fastställningsår för att kunna sortera, skapa foldrar och ta ner.
    coursecr = pd.read_table('vy_kursplaner_2023.tsv')
    coursecr = coursecr.assign(cryr = coursecr['creator'] + '.' + coursecr['Faststalld'].str.split('-').str.get(0))

    cryrs = list(set(coursecr['cryr']))
    scryrs = sorted(cryrs)

    # Skapa resten av kurstabellerna.
    cctable = pd.read_table('kurskod_vers.tsv')
    cmtable = pd.read_table('kurstillfallen_2023.tsv')

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
            logging.info('Kursplannr: '+str(nr))
            
            # Förbered för simparch dublin core metadata fil.
            dc = dict()
            dc['creator'] = df1['creator'].iloc[0]
            head_tail = os.path.split(dstpath)
            dc['itemtitle'] = head_tail[1]

            ccnr = cctable[cctable['Nr'] == nr]
            ccyr = str(coursecr[['cryr']].values[0][0]).split('.')[1]
            ccc = str(ccnr[['Kurskod']].values[0][0])
            cfile = ccc+'.'+ccyr
            logging.info('Kurskod: '+ccc)
            logging.info('Filkod: '+cfile)

            # Om länken innehåller åäö så lägg till omkodning för dem:
            ccsv = str(ccnr[['Kursplan sve_link0']].values[0][0]).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
                
            file = os.path.join(dstpath, cfile)
            filesvhtml = file + '_sv.html'
            filesvpdf = file + '_sv.pdf'
            
            # Ta bort karaktärer som inte kan konverteras (iconv -c) eller som konverteras till unicode A0 - "non-breaking space" (sed).
            os.system('curl "'+ccsv+'" | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filesvhtml+'"')

            pands1 = 'pandoc --pdf-engine=context -f html -t pdf -M pdfa=2a -c ./Static/bootstrap.min.css '
            pands2 = ' -s --template=tagged-report-template.context -M logopath="/home/torbjorn/archive-harvest/utveckling/test_slukurs-ark" -o '
            r = os.system(pands1+'"'+filesvhtml+'"'+pands2+'"'+filesvpdf+'"')
            if r!= 0:
                with open('course_not_converted.log', 'a') as f:
                    f.write(filesvhtml+'\n')

            # Addera filnamnet till contents-filen.
            head_tail = os.path.split(filesvpdf)
            with open(os.path.join(dstpath, 'contents'), 'a') as f:
                f.write(head_tail[1]+'\n')

            ccen = str(ccnr[['Kursplan eng_link0']].values[0][0]).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
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

            ccjn = str(ccnr[['Json_link0']].values[0][0]).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
            filejson = file + '_json.html'
            os.system('curl "'+ccjn+'" | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filejson+'"')

            # Extrahera kursens metadata som en lista av strängar.
            with open(filejson) as f:
                content = f.read()
            dictj = json.loads(bs4.BeautifulSoup(content, features="lxml").find('body').decode_contents().strip(), strict=False)
            dictjs.append(str(dictj))

            # Iterera över kurstillfällen.
            # Skapa en dataframe med textunderlag till dublin_core.
            cms = cmtable[cmtable['Kurskod'] == ccc]
            c = pd.DataFrame(columns=['Kurskod', 'benamning', 'filkod', 'Version'])
            for i in cms['Nr']:
                logging.info('Kurstillfällenr: '+str(nr))

                c.at[int(2*i), 'Kurskod'] = ccc
                c.at[int(2*i), 'benamning'] = str(pystache.render('{{Benamning_sve}}', dictj))
                c.at[int(2*i+1), 'Kurskod'] = ccc
                c.at[int(2*i+1), 'benamning'] = str(pystache.render('{{Benamning_eng}}', dictj))
                cmc = str(cms[cms['Nr'] == i].iloc[0]['Anmkod'])
                cmyr = str((cms[cms['Nr'] == i].iloc[0]['Läsår'])).zfill(4)
                cmf = str(cms[cms['Nr'] == i].iloc[0]['Kurstillfälle'])
                filkod = ccc+'.'+cmc+'.'+cmyr                    
                logging.info('Filkod: '+str(filkod))
                c.at[int(2*i), 'filkod'] = filkod
                c.at[int(2*i+1), 'filkod'] = filkod
                c.at[int(2*i), 'Version'] = str(pystache.render('{{Version}}', dictj))
                c.at[int(2*i+1), 'Version'] = str(pystache.render('{{Version}}', dictj))
                file = os.path.join(dstpath, filkod)
                filehtml = file + '.html'
                filepdf = file + '.pdf'
                os.system('curl "'+cmf+'" | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filehtml+'"')
                r = os.system(pands1+'"'+filehtml+'"'+pands2+'"'+filepdf+'"')
                if r!= 0:
                    with open('course_not_converted.log', 'a') as f:
                        f.write(filehtml+'\n')

                head_tail = os.path.split(filepdf)
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
                    prog='kursskordning.py',
                    description='Tar en srcmainpath folder, utökar den parsade kursvyn med cryr arkivbildare.faststallningsår, laddar ner kursplaner och metadata json och byter namn.', 
                    epilog='Argumenten är python3 ./kursskordning.py ~/srcmainfolder')
    parser.add_argument('path', help='Foldern där arkivstrukturen bildas.')
    parser.add_argument('rowno', help='Option att fortsätta skördning i den sorterade listan från loggade radnummer.', nargs='?', const='0', default='0')
    args = parser.parse_args()
    dspace_simparch(args.path, args.rowno)
