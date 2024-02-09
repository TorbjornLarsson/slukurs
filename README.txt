---
title: Slukurs PDF-generator
---

Spara anmälningskoder för läsår 2019/20 i CSV.

```
./anmyrs.sh 19 > amyrs_19.csv
```

Generera PDF/A-2a för kurs med kod 10061.1920 med Pandoc och Context.

```
./slukpdf.sh 10061.1920
```

För anmyrs_19.csv

```
awk -F',' '{print $2}'  anmyrs_19.csv | xargs ./slukpdf.sh
```

Spara slukurs tabellsidor från https://slukurs.slu.se/arkivering/indexindex.cfm som .tsv, till exempel via https://wtools.io/convert-html-to-tsv .
Python-rutinerna har hjälptext för argumenten, och i tillämpliga fall loggfiler.
Om arkivbildaren inte kunde säkerställas fördes dokumenten till en ny DSpace 'unk' arkivbildare.

För studenters kursplaner och kurstillfällen fram till 2023 genererades en kursvy.

```
python3 ./kurstillfallen_vers.py kt/default (om)start_tusental'
```

En korskontroll mellan kursplaner och kurstillfällen kördes.

```
python3 ./korskontroll_kurstillfallen_kursplaner.py
```

Skördning, konvertering till PDF/A-2a och simparch bildning kördes. Option finns för återstart från ett loggat radnummer.

```
python3 ./kursskordning.py ~/srcmainfolder' [radnummer]
```

För forskares kursplaner och kurstillfällen integrerades vy-prepareringen i programmet. 

Först kördes en korskontroll.

```
python3 ./korskontroll_phdkurstillfallen_phdkursplaner.py
```

Skördning, konvertering till PDF/A-2a och simparch bildning kördes. Option finns för återstart från ett loggat radnummer.

```
python3 phdkursskordning.py ~/srcmainfolder' [radnummer]
```

För studenters utbnildningsplaner kördes skördning, konvertering till PDF/A-2a och simparch bildning under arkivbildaren 'ua'.

```
python3 utbildningsplanerskordning.py ~/srcmainfolder' [radnummer]
```

Importen till DSpace av respektive simparch folderstruktur kördes.
Systemen är 'test' respektive 'mål'. Optioner för dokumenttypen 'utbildningsplaner' och för att testa på enstaka arkivbildare finns.
Det kan vara en god idé att kommentera bort "subprocess"-raden och titta på loggen innan själva importen, 
och man kan också modifiera till att köra en långsammare DSpace testkörning genom att lägga till ' -v ' eller ' --validate ' där.

```
sudo python3 dspace_import.py <e-post DSpace-admin> <arkivkatalog> <sökväg till DSpace> <system> [dokumenttyp] [arkivbildare]
```


