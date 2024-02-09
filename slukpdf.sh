#!/bin/bash
for akod in "$@" ; do
    for lang in "sv" "en"; do
        html="out/${akod}.${lang}.html"
        if ! [[ -e ${html} ]] ; then
                pdf="out/${akod}.${lang}.pdf"
                if [[ ${akod} =~ "P" ]] ; then
                        kupg="kurssidaPhD"
                else
                        kupg="kurssida"
                fi
                curl -L "https://epi-resurs.slu.se/slukurs-drift/${kupg}.cfm/?sprak=${lang}&anmkod=${akod}"\
                       | ./slukfilt.py > "${html}"
                inst="$(./inst.awk ${html})"
                kod="$(./kurskod.awk ${html} | uniq)"
                echo "${akod},${kod},${inst}"
                pandoc -L ./kursplan.lua --pdf-engine=context \
                        -M pdfa=2a -M title="${kod}" -M subtitle="${inst}" -o "${pdf}" "${html}"
        fi       
    done
done
