#!/bin/sh
curl "https://epi-resurs.slu.se/slukurs-drift/search.cfm?\
search=1&sprak=sv&fritext=&program=$2&termin=la$1&nivaGA_pc=&nivaF_pc=\
&omfattning_pc=&ort_pc=&amne_pc=&enhet_pc=&undervisningssprak_pc=A&takt_pc=\
&undervisningstid_pc=&nivaGA_mobil=&nivaF_mobil=&omfattning_mobil=\
&ort_mobil=&amne_mobil=&enhet_mobil=&undervisningssprak_mobil=A&takt_mobil=\
&undervisningstid_mobil=&CourseSearchButton=&Sortering=Starttid" \
| iconv -f iso8859-1 -t utf-8 | tee "anmyrs_$1$2.html" | awk -F'"' '$2~"anmkod"{print $2}' \
| awk -F'[&=]' '{printf("%s,%s\n",$2,$4)}'
