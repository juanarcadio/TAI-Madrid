#!/bin/bash

cd "$(dirname "$0")"

if [ "$1" == "--borrar" ]; then
    find . -type f -not -name '*.py' -not -name '*.md' -not -name '*.sh' -delete
    find */ -type f -name "*.html" -delete
fi

curl -s "http://www.sepe.es/direccionesytelefonosWeb/jsp/JSP_index.jsp" | grep --text "(new GLatLng" | sed -e 's/)).*//' -e 's/.*(/"/' -e 's/)/"/' | iconv -f ISO-8859-1 -t UTF-8 > sepe.txt

python3 get-links.py > wget.txt

grep -v '^#' wget.txt | wget -i- --continue --no-clobber

find . -iname "*.pdf" -exec pdftotext "{}" "{}-nolayout.txt" \;
find . -iname "*.pdf" -exec pdftotext -layout "{}" "{}-layout.txt" \;

./get-novacantes.py
./administracion.gob.es/descargar.sh
./csic.es/descargar.sh
