#!/usr/bin/awk -f

BEGIN {
    FS = "\t"
    lang[1] = "sv"
    lang[2] = "en"
}

$1 != "enhet" {
    for (l in lang) {
        html = sprintf("out/%s.%s.html", $2, lang[l])
        pdf = sprintf("out/short/%s.%s.short.pdf", $2, lang[l])
        # Definiera title/alttitle enligt språk.
        titlecmd = sprintf("pandoc -L printhead.lua %s | head -n1", html)
        alttitlecmd = sprintf("pandoc -L printstrong.lua %s | head -n1", html)
        titlecmd | getline title
        alttitlecmd | getline alttitle
        substcmd = sprintf("sed 's|<b>%s</b||' %s", alttitle, html)
        pdoccmd = sprintf("pandoc -L ./kursplan_short.lua --pdf-engine=context -f html\
                --template=tagged-report-template.context -M logopath='/home/karl/slulogo'\
                --top-level-division=section  -M pdfa=2a -M title='%s' -M subtitle='%s, %s'\
                -o '%s'", title, alttitle, $5, pdf)
        substpdoccmd = sprintf("%s | %s", substcmd, pdoccmd)
        system(substpdoccmd)
    }
}
