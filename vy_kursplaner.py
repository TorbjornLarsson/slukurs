#!/usr/bin/env python3
# Rutin som itererar över en .tsv fil med kursplaner och sammanställer en .tsv fil med en vy över dessa
import pandas as pd
import requests
import bs4
import pystache
import json

# Hämta kursens json html, extrahera body och konvertera till ett dictionary
def cadd(i, e1, e2, adr, df):
    # URLen kan innehålla Å,Ä,Ö på Windows-1252 format
    # adrc = str(adr).replace('Å','%C5').replace('Ä','%C4').replace('Ö','%D6')
    adrc = str(adr)
    print(adrc)
    r = requests.get(adrc)
    print(r.status_code)
    if r.status_code != 200:
        e1 += 1
        df.at[i,'Kurskod'] = 'no json'
        return [df, e1, e2]
    dictj = json.loads(bs4.BeautifulSoup(r.content, features="lxml").find('body').decode_contents().strip(), strict=False)
    print(pystache.render('{{Kurskod}}', dictj))
    df.at[i,'Enhet'] = str(pystache.render('{{Enhet}}', dictj))
    df.at[i,'Kurskod'] = str(pystache.render('{{Kurskod}}', dictj))
    df.at[i,'Version'] = int(pystache.render('{{Version}}', dictj))
    df.at[i,'Faststalld'] = str(pystache.render('{{Faststalld}}', dictj))
    df.at[i,'benamning'] = str(pystache.render('{{Benamning_sve}}', dictj))
    df.at[i,'Enhetsnamn'] = str(pystache.render('{{Enhetsnamn}}', dictj))

    # Hämta Enhetsnamn
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
    return [df, e1, e2]

if __name__ == '__main__':
    # Gör en dataframe kursvy från kurser tsv
    courses = pd.read_table('kurskod_vers.tsv')
    dfvy = courses[['Nr','Kurskod', 'Version']].copy()
    dfvy[['Enhet','Faststalld','benämning','Enhetsnamn','creator']] = None
    dfvy = dfvy[['Nr','Enhet','Kurskod','Version','Faststalld','benämning','Enhetsnamn','creator']]

    # Hämta kursens json adress, och fyll i kursvyn
    n = 0
    err1 = 0
    err2 = 0
    for jsonadr in courses.iloc[:,8]:
        [dfvy, err1, err2] = cadd(n, err1, err2, jsonadr, dfvy)
        n += 1
        print(n)
        print(err1)
        print(err2)
    print(dfvy)
    dfvy.to_csv('vy_kursplaner_2023.tsv', sep="\t", index=False)
    print('Antal rader som saknar json', err1)
    print('Antal rader som saknar oid', err2)
