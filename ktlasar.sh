#!/bin/sh
for ni in GA F ; do
        fname="kurser_${ni}_$1.tsv"
        vd "https://slukurs.slu.se/listor/KTKurser.cfm?niva=${ni}&lasar=$1" +:table_0:: \
                -b -o $fname
        awk -v yr=$1 '{printf("%s.%s\n", $1, yr)}' $fname | xargs ./slukpdf.sh >> \
                out/slukurs_$1.csv
done
