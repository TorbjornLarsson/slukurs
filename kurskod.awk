#!/usr/bin/awk -f

BEGIN {
    FS = "/"
}

$4=="kursfiler" {
    print $5
}
