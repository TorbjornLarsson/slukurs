#!/bin/sh
for akod in "$@" ; do
    for lang in "sv" "en"; do
        html="out/${akod}.${lang}.html"
        pdf="out/short/${akod}.${lang}.short.pdf"
        inst="$(./inst.awk ${html})"
        kurstitel="$(pandoc -L printhead.lua ${html} | head -n1)"
        altkurstitel="$(pandoc -L printstrong.lua ${html} | head -n1)"
        echo "${akod},${kurstitel},${inst}"
        sed "s|<b>${altkurstitel}</b>||" "${html}" | \
        pandoc -L ./kursplan_short.lua --pdf-engine=context -f html \
               --template=tagged-report-template.context -M logopath="/home/karl/slulogo" \
                --top-level-division=section -M pdfa=2a -M title="${kurstitel}" \
                -M subtitle="${altkurstitel}, ${inst}" -o "${pdf}"
    done
done
