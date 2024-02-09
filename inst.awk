#!/usr/bin/awk -f

BEGIN {
    FS = "[<>]"
}

$3~"^ (Ansvarig institution|Responsible department)" {
    getline
    print $3
}
