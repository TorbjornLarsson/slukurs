#!/bin/sh
while read -r l; do
    ramurlsuf=$(awk -F'\t' '{print $NF}' <<< "${l}")
    ramurl="https://slukurs.slu.se/ramschema/${ramurlsuf}"
    prognamn=$(awk -F'\t' '{print $2}' <<< "${l}")
    akod=$(awk -F'=' '{print $NF}' <<< "${l}")
    html="out/ramschema/${akod}.html"
    pdf="out/ramschema/${akod}.pdf"
    curl -L "${ramurl}" -o "${html}"
    pandoc  --pdf-engine=context \
            -M pdfa=2a  -M title="${prognamn}" -o "${pdf}" "${html}"
done
