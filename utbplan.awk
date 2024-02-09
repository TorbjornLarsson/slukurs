#!/usr/bin/awk -f

BEGIN {
    FS = "\t"
    baseurl = "https://slukurs.slu.se/utbildningsplan/"
}

NR > 1 {
    gsub(/['´]/, "’") 
    gsub(/-/, "–") 
    compath = sprintf("out/utbplan/%s.%s.", $1, $2)
    templpath = "tagged-report-template.context"
    logopath = "/home/karl/slulogo"
    enhtmlpath = sprintf("%sen.html", compath)
    enpdfpath = sprintf("%sen.pdf", compath)
    enurl = sprintf("%s%s", baseurl, $7)
    svhtmlpath = sprintf("%ssv.html", compath)
    svpdfpath = sprintf("%ssv.pdf", compath)
    svurl = sprintf("%s%s", baseurl, $5)
    #encurlcmd = sprintf("curl -L '%s' -o '%s'", enurl, enhtmlpath)
    ensedcmd = sprintf("sed -i 's/iso-8859-1/utf-8/'  %s", enhtmlpath)
    #enpycmd = sprintf("./utbplan.py %s", enhtmlpath)
    enpdoccmd = sprintf("pandoc --pdf-engine=context --template='%s'\
              --top-level-division=section -M logopath='%s' -M pdfa=2a -M title='%s' -o %s %s",
              templpath, logopath, $6, enpdfpath, enhtmlpath)
    #system(encurlcmd)
    system(ensedcmd)
    #system(enpycmd)
    system(enpdoccmd)
    #svcurlcmd = sprintf("curl -L '%s' -o '%s'", svurl, svhtmlpath)
    svsedcmd = sprintf("sed -i 's/iso-8859-1/utf-8/'  %s", svhtmlpath)
    #svpycmd = sprintf("./utbplan.py %s", svhtmlpath)
    svpdoccmd = sprintf("pandoc --pdf-engine=context --template='%s'\
              --top-level-division=section -M logopath='%s' -M pdfa=2a -M title='%s' -o %s %s",
              templpath, logopath, $4, svpdfpath, svhtmlpath)
    #system(svcurlcmd)
    system(svsedcmd)
    #system(svpycmd)
    system(svpdoccmd)
}
