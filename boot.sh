#!/bin/bash
source venv/bin/activate
# while true; do
#     flask db upgrade
#     if [[ "$?" == "0" ]]; then
#         break
#     fi
#     echo Upgrade command failed, retrying in 5 secs...
#     sleep 5
# done
# flask translate compile
# gunicorn -b localhost:8000 -w 4 microblog:app
exec waitress-serve --listen=*:5000 --expose-tracebacks homeroomconditions:app