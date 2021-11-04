#!/bin/bash
if [ -z "$1" ]
    then
    echo USAGE: psconvert.sh [file_to_convert]
    exit
fi
echo -n "powershell -e "
cat $1 | iconv -f UTF8 -t UTF16LE | base64 | tr -d '\n' 
echo -e '\n'
