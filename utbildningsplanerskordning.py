#!/usr/bin/env python3
# Skördar 2023 SLU utbildningsplaner med eventuella bilagor för arkivering i DSpace. Arkivbildare är SLU ua.
# Metadata tas från HTML filers body som dictionaries och konverteras till Dublin Core format.
# Skördningen sker iterativt om webservern har problem samt loggas i educationplanharvest.log.
#
# Arkiveringen sker efter konvertering av HTML-filer som deklareras vara på iso8859-1 format men lagrats som windows-1252.
# Detta avhjälper kanske inte alla konverteringsproblem. Alla filer som misslyckats konverteras listas i educationplan_not_converted.log. 

import argparse
import logging
import urllib.parse
import os
import pandas as pd
import bs4
import requests
import pystache
import json

logging.basicConfig(filename='educationplanharvest.log', filemode='w', level=logging.DEBUG)
with open('educationplan_not_converted.log', 'w') as f:
    f.write('')

# Länknamn med querys som har blanksteg behöver lite massage. 
def url_from_link(link):
    p = urllib.parse.urlparse(link)
    url1 = p.path.split('=')[1]
    url2 = urllib.parse.unquote(urllib.parse.quote_plus(p.query)).split('+target')[0]
    url = url1+'?'+url2

    # Returvärdet är inom citattecken.
    return url

# Hämta bilagor, returnera filnamn
def saveattach(spath):
    with open(spath) as f:
        slukhtml = f.read()
    sluksoup = bs4.BeautifulSoup(slukhtml, 'html.parser')
    pspl = os.path.split(spath)
    sbase = os.path.splitext(pspl[1])[0]
    attfiles = []
    for (i, link) in enumerate(sluksoup.find_all('a')):
       attpath = os.path.join(pspl[0], sbase + '_a{0}.pdf'.format(i))
       attfiles.append(os.path.split(attpath)[1])
       r = requests.get(link.get('href'))
       with open(attpath, 'wb') as f:
          f.write(r.content)
    return attfiles

# Skapa en arbetsfolder på simparch folderformat.
# Curla ner filerna från utbildningsplanlistan.

def dspace_simparch(dstmainpath, rowno):

    with open('dublin_core_utbildningsplaner_2023.mustache') as f:
        dctempl = f.read()

    # Utöka vyn med en kolumn arkivbildare.gällandeår för att kunna sortera, skapa foldrar och ta ner.
    coursecr = pd.read_table('utbildningsplaner_2023.tsv')
    coursecr = coursecr.assign(cryr = 'ua.' + coursecr['Giltig fr.o.m.'].str.split(' ').str.get(1))

    cryrs = list(set(coursecr['cryr']))
    scryrs = sorted(cryrs)

    # En arkivbildare.gällandeår cr default är att börja från första raden 0 i sorterade listan.
    rnr = int(rowno)
    if rnr != 0:
        scryrs = scryrs[rnr:]

    for cr in scryrs:
        logging.info('Sorterade utbildningars radnummer: '+str(rnr))
        logging.info('Utbildningsplaner: '+str(cr))
        df1 = coursecr[coursecr['cryr'] == cr]

        dstpath = os.path.join(dstmainpath, str(cr).split('.')[0], 'utbildningsplaner_' + str(cr).split('.')[0],'Utbildningsplaner ' + str(cr))
        logging.info('Folderpath: '+str(dstpath))
        os.makedirs(dstpath, exist_ok = True)
        
        with open(os.path.join(dstpath, 'contents'), 'w') as f:
            f.write('')

        dictjs = []
        courses = pd.DataFrame()

        for nr in df1['Nr']:
            logging.info('Utbildningsplannr: '+str(nr))
            
            # Förbered för simparch dublin core metadata fil.
            dc = dict()
            head_tail = os.path.split(dstpath)
            dc['itemtitle'] = head_tail[1]

            ccnr = coursecr[coursecr['Nr'] == nr]
            ccyr = str(ccnr[['cryr']].values[0][0]).split('.')[1]
            ccc = str(ccnr[['Programkod']].values[0][0])
            ccv = str(ccnr[['Version']].values[0][0])
            logging.info('Programkod: '+ccc)
            logging.info('Version: '+ccv)
            # Om länken innehåller åäö så lägg till omkodning för dem:
            linksv = str(ccnr[['Utbildningsplan sve']].values[0][0]).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
            ccsv = url_from_link(linksv)

            file = os.path.join(dstpath, ccc+'.'+ccyr+'.'+ccv)
            filesvhtml = file + '_sv.html'
            filesvpdf = file + '_sv.pdf'
            
            # Ta bort karaktärer som inte kan konverteras (iconv -c) eller som konverteras till unicode A0 - "non-breaking space" (sed).
            os.system('curl '+ccsv+' | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filesvhtml+'"')

            pands1 = 'pandoc --pdf-engine=context -f html -t pdf -M pdfa=2a -c ./Static/bootstrap.min.css '
            pands2 = ' -s --template=tagged-report-template.context -M logopath="/home/torbjorn/archive-harvest/utveckling/test_slukurs-ark" -o '
            r = os.system(pands1+'"'+filesvhtml+'"'+pands2+'"'+filesvpdf+'"')
            if r!= 0:
                with open('educationplan_not_converted.log', 'a') as f:
                    f.write(filesvhtml+'\n')

            # Addera filnamnet till contents-filen.
            head_tail = os.path.split(filesvpdf)
            with open(os.path.join(dstpath, 'contents'), 'a') as f:
                f.write(head_tail[1]+'\n')

            # Hämta bilagor och adfdera filnamnen till contents-filen.
            atts = saveattach(filesvhtml)
            if atts:
                for att in atts:
                    head_tail = os.path.split(att)
                    logging.info('Bilaga: '+head_tail[1])
                    with open(os.path.join(dstpath, 'contents'), 'a') as f:
                        f.write(head_tail[1]+'\n')
 
            linken = str(ccnr[['Utbildningsplan eng']].values[0][0]).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
            ccen = url_from_link(linken)
            fileenhtml = file + '_en.html'
            fileenpdf = file + '_en.pdf'
            os.system('curl '+ccen+' | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+fileenhtml+'"')
            r = os.system(pands1+'"'+fileenhtml+'"'+pands2+'"'+fileenpdf+'"')
            if r!= 0:
                with open('educationplan_not_converted.log', 'a') as f:
                    f.write(fileenhtml+'\n')

            head_tail = os.path.split(fileenpdf)
            with open(os.path.join(dstpath, 'contents'), 'a') as f:
                f.write(head_tail[1]+'\n')

            atts = saveattach(fileenhtml)
            if atts:
                for att in atts:
                    head_tail = os.path.split(att)
                    logging.info('Bilaga: '+head_tail[1])
                    with open(os.path.join(dstpath, 'contents'), 'a') as f:
                        f.write(head_tail[1]+'\n')

            linkjn = str(ccnr[['Json']].values[0][0]).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
            ccjn = url_from_link(linkjn)
            filejson = file + '_json.html'
            os.system('curl '+ccjn+' | iconv -c -f WINDOWS-1252 -t UTF-8 | sed "''s/­//g''" > "'+filejson+'"')

            # Extrahera kursens metadata som en lista av strängar.
            with open(filejson) as f:
                content = f.read()
            dictj = json.loads(bs4.BeautifulSoup(content, features="lxml").find('body').decode_contents().strip(), strict=False)
            dictjs.append(str(dictj))

            # Skapa en dataframe med textunderlag till dublin_core.
            cms = coursecr[coursecr['Programkod'] == ccc]
            c = pd.DataFrame(columns=['Programkod', 'Benamning', 'filkod', 'Version'])
            c.at[int(0), 'Programkod'] = ccc
            c.at[int(0), 'Benamning'] = str(pystache.render('{{Benamning_sve}}', dictj))
            c.at[int(1), 'Programkod'] = ccc
            c.at[int(1), 'Benamning'] = str(pystache.render('{{Benamning_eng}}', dictj))
            cmyr = str(cms.iloc[0]['Giltig fr.o.m.']).split(' ')[1]
            filkod = ccc+'.'+cmyr
            c.at[int(0), 'filkod'] = filkod
            c.at[int(1), 'filkod'] = filkod
            c.at[int(0), 'Version'] = str(pystache.render('{{Version}}', dictj))
            c.at[int(1), 'Version'] = str(pystache.render('{{Version}}', dictj))
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
        dc['programs'] = courses.to_dict('records')
        with open(os.path.join(dstpath, 'dublin_core.xml'), 'w') as f:
            f.write(pystache.render(dctempl, dc))

        # Uppdatera radnummer.
        rnr += 1 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='utbilkdningsplanerskordning.py',
                    description='Tar en srcmainpath folder, utökar den parsade utbildningsplanlistan med cryr arkivbildare.gällandeår, laddar ner utbildningsplaner och metadata json och byter namn.', 
                    epilog='Argumenten är python3 ./utbildningsplanerskordning.py ~/srcmainfolder')
    parser.add_argument('path', help='Foldern där arkivstrukturen bildas.')
    parser.add_argument('rowno', help='Option att fortsätta skördning i den sorterade listan från loggade radnummer.', nargs='?', const='0', default='0')
    args = parser.parse_args()
    dspace_simparch(args.path, args.rowno)
