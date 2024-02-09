#!/usr/bin/env python3
# Rutin som filtrerar en .tsv fil med kurstillfällen
import argparse
import pandas as pd
import requests

# Filtrera ut url
def cfilt(i, adr, df):
    # URLen kan innehålla Å,Ä,Ö på Windows-1252 format
    # adrc = str(adr).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
    adrc = str(adr).split(' ')[1].split('"')[1]
    print(adrc)
    return [df, adrc]

# Testa hämta kursens fil
def cver(i, e, adr, df):
    adrc = str(adr)
    print(adrc)
    r = requests.get(adrc)
    print(r.status_code)
    if r.status_code != 200:
        e += 1
        df.at[i,'Kurskod'] = 'no file'
        return [df, adrc, e]
    return [df, adrc, e]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog='kurstillfallen_vers.py',
                    description='Filtrerar ut url från en .tsv fil med kurstillfällen, skriver en ren .tsv fil, verifierar att filerna existerar. Möjllighet till omstart av en filtyp vid timeout.',
                    epilog='Argumenten är python3 ./kurstillfallen_vers.py kt/default (om)start_tusental')
    parser.add_argument('type', help='Filtyp för start.')
    parser.add_argument('j', help='Ordningstal för tusental för start.')
    args = parser.parse_args()

    if args.type != 'kt':
        courses = pd.read_table('kurstillfallen_vers.tsv')
        dfc = courses[['Nr', 'Kurskod', 'Version', 'Anmkod', 'Läsår', 'Kurstillfälle', 'Kursplan sve', 'Kursplan eng', 'Json']]
        print(dfc)

        # Filtrera ut url
        i = 0
        for fadr in courses.iloc[:,5]:
            [dfc, fadr] = cfilt(i, fadr, dfc)
            dfc.iloc[i,5] = fadr
            i += 1

        i = 0
        for fadr in courses.iloc[:,6]:
            [dfc, fadr] = cfilt(i, fadr, dfc)
            dfc.iloc[i,6] = fadr
            i += 1

        i = 0
        for fadr in courses.iloc[:,7]:
            [dfc, fadr] = cfilt(i, fadr, dfc)
            dfc.iloc[i,7] = fadr
            i += 1

        i = 0
        for fadr in courses.iloc[:,8]:
            [dfc, fadr] = cfilt(i, fadr, dfc)
            dfc.iloc[i,8] = fadr
            i += 1
        print(dfc)
        dfc.to_csv('kurstillfallen_2023.tsv', sep="\t", index=False)
        courses = pd.read_table('kurstillfallen_2023.tsv')
        dfc = courses[['Nr', 'Kurskod', 'Version', 'Anmkod', 'Läsår', 'Kurstillfälle', 'Kursplan sve', 'Kursplan eng', 'Json']]
        print(dfc)
    
    if args.type == 'kt':
        courses = pd.read_table('kurstillfallen_2023.tsv')
        dfc = courses[['Nr', 'Kurskod', 'Version', 'Anmkod', 'Läsår', 'Kurstillfälle', 'Kursplan sve', 'Kursplan eng', 'Json']]
        print(dfc)

    # Verifiera url
    i = 0
    j = 1
    if args.type == 'kt':
        j = int(args.j)
        i = 1000*j
    err = 0
    for fadr in courses.iloc[:,5]:
        [dfc, fadr, err] = cver(i, err, fadr, dfc)
        i += 1
        print(i)
        print(err)
    print('Antal rader som saknar kurstillfällen fil', err)
