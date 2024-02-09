#!/usr/bin/awk -f

BEGIN {
    FS = "\t"
}

$1 != "" {
    print $0
    prevkod = $1
    prevprog = $3
} 

$1 == "" {
    printf("%s\t%s\t%s\t%s\t%s\n", prevkod, $2, prevprog, $4, $5)
}
