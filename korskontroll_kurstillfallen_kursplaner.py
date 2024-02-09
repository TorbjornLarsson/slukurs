#!/usr/bin/env python3
# Korskör listan med kursplaner mot listan med kurstillfällen och tillse att det inte finns kurskoder som inte listats.
import pandas as pd

dfkp = pd.read_table('kurskod_vers.tsv')
dfkt = pd.read_table('kurstillfallen_2023.tsv')

i = 0
for nr in dfkt['Nr']:
    ccnr = dfkt[dfkt['Nr'] == nr]
    ccc = str(ccnr[['Kurskod']].values[0][0])
    print(nr)
    if any(dfkp[['Kurskod']].astype(str) == ccc):
        print(nr)
        i += 1

print('Antal kurstillfällen med listad kurskod: ', i)
print('Ska vara 21805 stycken')