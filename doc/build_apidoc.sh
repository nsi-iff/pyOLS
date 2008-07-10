#!/bin/bash

cd "`dirname \"$0\"`"

if [[ ! -x "`which epydoc`" ]]; then
    echo "epydoc is not installed.  Install it with \`easy_install epydoc\`?"
    exit 1
fi

epydoc pyols -o api
exit $?
